"""
Background Job Worker Module.

Executes backtest simulations asynchronously, decoupling calculation loads from the FastAPI server.
"""

import os
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.db.models import BacktestRunModel, StrategyVersionModel, TradeModel
from app.domains.strategies.schemas import StrategyDSL
from app.domains.market_data.loader import MarketDataLoader
from app.domains.backtesting.engine import BacktestEngine, CostModelConfig

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bison.db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async_engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionMaker = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


async def execute_backtest_job(backtest_run_id: str) -> None:
    """Executes backtest job asynchronously and persists results to database."""
    async with AsyncSessionMaker() as db:
        result = await db.execute(
            select(BacktestRunModel).where(BacktestRunModel.id == backtest_run_id)
        )
        backtest_run = result.scalars().first()
        if not backtest_run:
            return

        try:
            backtest_run.status = "RUNNING"
            await db.commit()

            # Load Strategy Version DSL
            ver_result = await db.execute(
                select(StrategyVersionModel).where(StrategyVersionModel.id == backtest_run.strategy_version_id)
            )
            version_model = ver_result.scalars().first()
            if not version_model:
                raise ValueError("Associated Strategy Version not found.")

            dsl = StrategyDSL(**version_model.dsl_json)

            # Load Market Data Fixture (NIFTY 5m default)
            fixture_path = os.path.join("..", "..", "data", "fixtures", "nifty_5m.csv")
            if not os.path.exists(fixture_path):
                # Fallback to local relative path if executing inside apps/api
                fixture_path = os.path.join("data", "fixtures", "nifty_5m.csv")
                if not os.path.exists(fixture_path):
                    fixture_path = "../../data/fixtures/nifty_5m.csv"

            df, quality_report = MarketDataLoader.load_from_csv(fixture_path, dsl.instrument.symbol)

            # Execute Engine
            engine = BacktestEngine(
                strategy=dsl,
                initial_capital=backtest_run.initial_capital,
                cost_config=CostModelConfig()
            )
            res = engine.run(df)

            # Persist Results
            backtest_run.status = "COMPLETED"
            backtest_run.completed_at = datetime.utcnow()
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

            # Save Executed Trade Records
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

            await db.commit()

        except Exception as e:
            backtest_run.status = "FAILED"
            backtest_run.error_message = str(e)
            await db.commit()
