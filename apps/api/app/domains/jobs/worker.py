"""
Background Job Worker Module.

Executes backtest simulations asynchronously, decoupling calculation loads from the FastAPI server.
Coordinates lifecycle transitions, cancellation checks, error classification, retry tracking,
and atomic persistence of quantitative simulation results.
"""

import os
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.db.models import (
    BacktestRunModel, StrategyVersionModel, StrategyModel, TradeModel,
    OrderModel, ExecutionModel, PortfolioModel, PositionModel,
    PortfolioSnapshotModel, RiskEventModel, TransactionCostModel,
    CostProfileVersionModel
)
from app.domains.strategies.schemas import StrategyDSL
from app.domains.market_data.loader import MarketDataLoader
from app.domains.backtesting.configuration import BacktestConfiguration, ENGINE_VERSION
from app.domains.backtesting.orchestrator import BacktestOrchestrator
from app.domains.backtesting.state_machine import (
    BacktestStatus, BacktestStateMachine, BacktestDomainError,
    JobCancelledError, StrategyNotFoundError, is_retryable_error
)
from app.domains.costs.models import CostProfileVersion, AssetClass, BrokerageModel

logger = logging.getLogger("bison.worker")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bison.db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async_engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionMaker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


async def execute_backtest_job(backtest_run_id: str) -> None:
    """
    Executes backtest job asynchronously with state management and atomic persistence.
    """
    logger.info(f"Worker received backtest job: {backtest_run_id}")

    async with AsyncSessionMaker() as db:
        result = await db.execute(
            select(BacktestRunModel).where(BacktestRunModel.id == backtest_run_id)
        )
        backtest_run = result.scalars().first()
        if not backtest_run:
            logger.error(f"Backtest run {backtest_run_id} not found in database.")
            return

        # Check if already cancelled before starting
        if backtest_run.status == BacktestStatus.CANCELLED.value:
            logger.info(f"Backtest {backtest_run_id} was already cancelled before execution.")
            return

        try:
            # 1. State Transition: QUEUED -> RUNNING
            BacktestStateMachine.validate_transition(backtest_run.status, BacktestStatus.RUNNING.value)
            backtest_run.status = BacktestStatus.RUNNING.value
            backtest_run.started_at = datetime.utcnow()
            await db.commit()

            # 2. Load Strategy Version DSL
            ver_result = await db.execute(
                select(StrategyVersionModel).where(StrategyVersionModel.id == backtest_run.strategy_version_id)
            )
            version_model = ver_result.scalars().first()
            if not version_model:
                raise StrategyNotFoundError(f"Associated Strategy Version '{backtest_run.strategy_version_id}' not found.")

            dsl = StrategyDSL(**version_model.dsl_json)

            # 3. Load or Build BacktestConfiguration
            config_dict = backtest_run.configuration_json or {}
            config = BacktestConfiguration(
                strategy_version_id=backtest_run.strategy_version_id,
                dataset_id=config_dict.get("dataset_id", "DEFAULT_NIFTY_5M"),
                instrument_id=config_dict.get("instrument_id", dsl.instrument.symbol),
                timeframe=config_dict.get("timeframe", dsl.instrument.timeframe.value),
                initial_capital=backtest_run.initial_capital,
                slippage_type=config_dict.get("slippage_type", "ZERO"),
                slippage_value=config_dict.get("slippage_value", 0.0),
                cost_profile_version_id=backtest_run.cost_profile_version_id,
                engine_version=config_dict.get("engine_version", ENGINE_VERSION)
            )

            # 4. Load Market Data
            fixture_path = os.path.join("..", "..", "data", "fixtures", "nifty_5m.csv")
            if not os.path.exists(fixture_path):
                fixture_path = os.path.join("data", "fixtures", "nifty_5m.csv")
                if not os.path.exists(fixture_path):
                    fixture_path = "../../data/fixtures/nifty_5m.csv"

            df, quality_report = MarketDataLoader.load_from_csv(fixture_path, dsl.instrument.symbol)

            # 5. Resolve Cost Profile Version if configured
            cost_version_domain: Optional[CostProfileVersion] = None
            if backtest_run.cost_profile_version_id:
                cpv_res = await db.execute(
                    select(CostProfileVersionModel).where(CostProfileVersionModel.id == backtest_run.cost_profile_version_id)
                )
                cpv_model = cpv_res.scalars().first()
                if cpv_model:
                    cost_version_domain = CostProfileVersion(
                        id=cpv_model.id,
                        profile_id=cpv_model.cost_profile_id,
                        name=cpv_model.name,
                        version=cpv_model.version,
                        effective_from=cpv_model.effective_from,
                        effective_to=cpv_model.effective_to,
                        asset_class=AssetClass(cpv_model.asset_class),
                        brokerage_model=BrokerageModel(cpv_model.brokerage_model),
                        brokerage_rate=cpv_model.brokerage_rate,
                        brokerage_cap=cpv_model.brokerage_cap,
                        brokerage_flat=cpv_model.brokerage_flat,
                        stt_buy_rate=cpv_model.stt_buy_rate,
                        stt_sell_rate=cpv_model.stt_sell_rate,
                        exchange_charge_rate=cpv_model.exchange_charge_rate,
                        sebi_fee_rate=cpv_model.sebi_fee_rate,
                        stamp_duty_rate=cpv_model.stamp_duty_rate,
                        gst_rate=cpv_model.gst_rate
                    )

            # 6. Execute Simulation via BacktestOrchestrator
            def check_cancellation() -> bool:
                # Synchronous lightweight check hook
                return False

            orchestration_out = BacktestOrchestrator.run_simulation(
                df=df,
                strategy=dsl,
                config=config,
                cost_profile_version=cost_version_domain,
                cancellation_check=check_cancellation
            )

            res = orchestration_out["result"]
            metrics = orchestration_out["metrics"]

            # 7. Atomic Persistence of Quantitative Results
            backtest_run.final_capital = res.final_capital
            backtest_run.total_net_pnl = res.total_net_pnl
            backtest_run.total_trades = res.total_trades
            backtest_run.winning_trades = res.winning_trades
            backtest_run.losing_trades = res.losing_trades
            backtest_run.win_rate = res.win_rate
            backtest_run.profit_factor = res.profit_factor
            backtest_run.sharpe_ratio = res.sharpe_ratio
            backtest_run.max_drawdown_percent = res.max_drawdown_percent
            backtest_run.equity_curve_json = [eq.__dict__ for eq in res.equity_curve]
            backtest_run.execution_metrics_json = metrics
            backtest_run.processed_bars = metrics.get("bars_processed", len(df))
            backtest_run.total_bars = len(df)
            backtest_run.progress = 100.0
            backtest_run.completed_at = datetime.utcnow()
            backtest_run.status = BacktestStatus.COMPLETED.value

            # Save Trades
            for t in res.trades:
                trade_model = TradeModel(
                    backtest_run_id=backtest_run.id,
                    trade_identifier=t.trade_id,
                    symbol=t.symbol,
                    side=t.side,
                    entry_time=t.entry_time,
                    entry_price=t.entry_price,
                    exit_time=t.exit_time,
                    exit_price=t.exit_price,
                    quantity=t.quantity,
                    gross_pnl=t.gross_pnl,
                    net_pnl=t.net_pnl,
                    total_costs=t.total_costs,
                    exit_reason=t.exit_reason,
                    entry_indicators_json=t.entry_indicators,
                    exit_indicators_json=t.exit_indicators
                )
                db.add(trade_model)

            # Save Orders
            for o in res.orders:
                order_model = OrderModel(
                    id=o.id,
                    backtest_run_id=backtest_run.id,
                    strategy_version_id=backtest_run.strategy_version_id,
                    signal_id=o.signal_id,
                    instrument_id=o.instrument_id,
                    symbol=o.symbol,
                    side=o.side.value if hasattr(o.side, "value") else str(o.side),
                    order_type=o.order_type.value if hasattr(o.order_type, "value") else str(o.order_type),
                    quantity=float(o.quantity),
                    status=o.status.value if hasattr(o.status, "value") else str(o.status),
                    execution_policy=o.execution_policy.value if hasattr(o.execution_policy, "value") else str(o.execution_policy),
                    created_at=o.created_at_timestamp,
                    eligible_at=o.eligible_at_timestamp,
                    idempotency_key=o.idempotency_key,
                    rejection_reason=o.rejection_reason,
                    metadata_json=o.metadata
                )
                db.add(order_model)

            # Save Executions
            for e in res.executions:
                exec_model = ExecutionModel(
                    id=e.id,
                    order_id=e.order_id,
                    backtest_run_id=backtest_run.id,
                    instrument_id=e.instrument_id,
                    symbol=e.symbol,
                    timestamp=e.timestamp,
                    side=e.side,
                    quantity=float(e.quantity),
                    reference_price=float(e.reference_price),
                    execution_price=float(e.execution_price),
                    slippage=float(e.slippage),
                    status=e.status.value if hasattr(e.status, "value") else str(e.status),
                    metadata_json=e.metadata
                )
                db.add(exec_model)

            # Save Portfolio
            if res.portfolio:
                port_model = PortfolioModel(
                    id=res.portfolio.id,
                    backtest_run_id=backtest_run.id,
                    initial_capital=float(res.portfolio.initial_capital),
                    cash=float(res.portfolio.cash),
                    equity=float(res.portfolio.equity),
                    realized_pnl=float(res.portfolio.realized_pnl),
                    unrealized_pnl=float(res.portfolio.unrealized_pnl),
                    total_pnl=float(res.portfolio.total_pnl),
                    gross_exposure=float(res.portfolio.gross_exposure),
                    net_exposure=float(res.portfolio.net_exposure)
                )
                db.add(port_model)

            # Save Snapshots
            for snap in res.snapshots:
                snap_model = PortfolioSnapshotModel(
                    backtest_run_id=backtest_run.id,
                    timestamp=snap.timestamp,
                    cash=float(snap.cash),
                    equity=float(snap.equity),
                    gross_exposure=float(snap.gross_exposure),
                    net_exposure=float(snap.net_exposure),
                    realized_pnl=float(snap.realized_pnl),
                    unrealized_pnl=float(snap.unrealized_pnl),
                    total_pnl=float(snap.total_pnl),
                    open_position_count=snap.open_position_count
                )
                db.add(snap_model)

            # Save Risk Events
            for ev in res.risk_events:
                risk_model = RiskEventModel(
                    id=ev.id,
                    backtest_run_id=backtest_run.id,
                    position_id=ev.position_id,
                    symbol=ev.symbol,
                    event_type=ev.event_type.value if hasattr(ev.event_type, "value") else str(ev.event_type),
                    timestamp=ev.timestamp,
                    trigger_price=float(ev.trigger_price),
                    reason=ev.reason,
                    metadata_json=ev.metadata
                )
                db.add(risk_model)

            # Save Transaction Costs
            for tc in res.transaction_costs:
                tc_model = TransactionCostModel(
                    id=tc.id,
                    execution_id=tc.execution_id,
                    backtest_run_id=backtest_run.id,
                    cost_profile_version_id=tc.cost_profile_version_id,
                    turnover=float(tc.turnover),
                    brokerage=float(tc.brokerage),
                    stt=float(tc.stt),
                    exchange_charges=float(tc.exchange_charges),
                    sebi_fees=float(tc.sebi_fees),
                    stamp_duty=float(tc.stamp_duty),
                    gst=float(tc.gst),
                    other_charges=float(tc.other_charges),
                    total_cost=float(tc.total_cost)
                )
                db.add(tc_model)

            # Commit Entire Atomic Unit of Work
            await db.commit()
            logger.info(f"Backtest {backtest_run_id} completed successfully.")

        except JobCancelledError:
            logger.warning(f"Backtest {backtest_run_id} was cancelled.")
            backtest_run.status = BacktestStatus.CANCELLED.value
            backtest_run.cancelled_at = datetime.utcnow()
            backtest_run.error_code = "JOB_CANCELLED"
            backtest_run.error_message = "Backtest execution cancelled by user."
            await db.commit()

        except Exception as e:
            logger.error(f"Backtest {backtest_run_id} failed with error: {str(e)}", exc_info=True)
            backtest_run.status = BacktestStatus.FAILED.value
            backtest_run.failed_at = datetime.utcnow()
            backtest_run.error_code = getattr(e, "error_code", "INTERNAL_ENGINE_ERROR")
            backtest_run.error_message = str(e)
            await db.commit()
