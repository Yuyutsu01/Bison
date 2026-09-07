"""
Backtesting REST API Routes.

Handles backtest submission, status polling, results retrieval, trade inspection,
order/execution querying, portfolio state inspection, risk events, and CSV export.
"""

import asyncio
import io
import csv
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.db.models import (
    BacktestRunModel, StrategyVersionModel, StrategyModel, TradeModel,
    OrderModel, ExecutionModel, PortfolioModel, PositionModel,
    PortfolioSnapshotModel, RiskEventModel, TransactionCostModel
)
from app.core.security import get_current_user_id
from app.domains.jobs.worker import execute_backtest_job

router = APIRouter(prefix="/backtests", tags=["Backtesting"])


class CreateBacktestRequest(BaseModel):
    strategy_id: str
    version: Optional[int] = None
    initial_capital: float = 100000.0


class TransactionCostBreakdownDTO(BaseModel):
    id: str
    execution_id: str
    turnover: float
    brokerage: float
    stt: float
    exchange_charges: float
    sebi_fees: float
    stamp_duty: float
    gst: float
    other_charges: float
    total_cost: float


class BacktestSummaryDTO(BaseModel):
    id: str
    strategy_id: str
    strategy_name: str
    status: str
    error_message: Optional[str] = None
    initial_capital: float
    final_capital: Optional[float] = None
    total_net_pnl: Optional[float] = None
    total_trades: int = 0
    win_rate: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown_percent: Optional[float] = None
    created_at: str


class TradeDTO(BaseModel):
    id: str
    trade_identifier: str
    symbol: str
    side: str
    entry_time: str
    entry_price: float
    exit_time: Optional[str] = None
    exit_price: Optional[float] = None
    quantity: float
    gross_pnl: float
    net_pnl: float
    total_costs: float
    exit_reason: Optional[str] = None
    entry_indicators: Optional[dict] = None
    exit_indicators: Optional[dict] = None


class OrderDTO(BaseModel):
    id: str
    signal_id: str
    instrument_id: str
    symbol: str
    side: str
    order_type: str
    quantity: float
    status: str
    execution_policy: str
    created_at: str
    eligible_at: str
    idempotency_key: str
    rejection_reason: Optional[str] = None


class ExecutionDTO(BaseModel):
    id: str
    order_id: str
    instrument_id: str
    symbol: str
    timestamp: str
    side: str
    quantity: float
    reference_price: float
    execution_price: float
    slippage: float
    status: str


class PortfolioDTO(BaseModel):
    id: str
    initial_capital: float
    cash: float
    equity: float
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
    gross_exposure: float
    net_exposure: float


class PositionDTO(BaseModel):
    id: str
    symbol: str
    side: str
    quantity: float
    average_entry_price: float
    current_price: float
    realized_pnl: float
    unrealized_pnl: float
    status: str
    opened_at: str
    last_updated_at: str
    holding_bars: int


class RiskEventDTO(BaseModel):
    id: str
    position_id: Optional[str] = None
    symbol: str
    event_type: str
    timestamp: str
    trigger_price: float
    reason: str


class BacktestDetailDTO(BacktestSummaryDTO):
    equity_curve: Optional[list] = None
    trades: List[TradeDTO] = []
    portfolio: Optional[PortfolioDTO] = None


@router.post("", response_model=BacktestSummaryDTO, status_code=status.HTTP_202_ACCEPTED)
async def run_backtest(
    req: CreateBacktestRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    # Retrieve Strategy
    result = await db.execute(
        select(StrategyModel)
        .options(selectinload(StrategyModel.versions))
        .where(StrategyModel.id == req.strategy_id, StrategyModel.user_id == user_id)
    )
    strategy = result.scalars().first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found.")

    target_ver_num = req.version or strategy.current_version
    target_version = next((v for v in strategy.versions if v.version == target_ver_num), None)
    if not target_version:
        raise HTTPException(status_code=404, detail=f"Strategy version v{target_ver_num} not found.")

    # Create Backtest Run Record
    backtest_run = BacktestRunModel(
        user_id=user_id,
        strategy_version_id=target_version.id,
        initial_capital=req.initial_capital,
        status="QUEUED"
    )
    db.add(backtest_run)
    await db.commit()
    await db.refresh(backtest_run)

    # Dispatch Background Worker Execution
    background_tasks.add_task(execute_backtest_job, backtest_run.id)

    return BacktestSummaryDTO(
        id=backtest_run.id,
        strategy_id=strategy.id,
        strategy_name=strategy.name,
        status=backtest_run.status,
        initial_capital=backtest_run.initial_capital,
        created_at=backtest_run.created_at.isoformat()
    )


@router.get("", response_model=List[BacktestSummaryDTO])
async def list_backtests(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(BacktestRunModel)
        .options(selectinload(BacktestRunModel.strategy_version).selectinload(StrategyVersionModel.strategy))
        .where(BacktestRunModel.user_id == user_id)
        .order_by(desc(BacktestRunModel.created_at))
    )
    runs = result.scalars().all()
    return [
        BacktestSummaryDTO(
            id=r.id,
            strategy_id=r.strategy_version.strategy.id if r.strategy_version else "",
            strategy_name=r.strategy_version.strategy.name if r.strategy_version else "Strategy",
            status=r.status,
            error_message=r.error_message,
            initial_capital=r.initial_capital,
            final_capital=r.final_capital,
            total_net_pnl=r.total_net_pnl,
            total_trades=r.total_trades,
            win_rate=r.win_rate,
            sharpe_ratio=r.sharpe_ratio,
            max_drawdown_percent=r.max_drawdown_percent,
            created_at=r.created_at.isoformat()
        )
        for r in runs
    ]


@router.get("/{backtest_id}", response_model=BacktestDetailDTO)
async def get_backtest(
    backtest_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(BacktestRunModel)
        .options(
            selectinload(BacktestRunModel.strategy_version).selectinload(StrategyVersionModel.strategy),
            selectinload(BacktestRunModel.trades),
            selectinload(BacktestRunModel.portfolio)
        )
        .where(BacktestRunModel.id == backtest_id, BacktestRunModel.user_id == user_id)
    )
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Backtest run not found.")

    trades_dto = [
        TradeDTO(
            id=t.id,
            trade_identifier=t.trade_identifier,
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
            entry_indicators=t.entry_indicators_json,
            exit_indicators=t.exit_indicators_json
        )
        for t in run.trades
    ]

    portfolio_dto = None
    if run.portfolio:
        portfolio_dto = PortfolioDTO(
            id=run.portfolio.id,
            initial_capital=run.portfolio.initial_capital,
            cash=run.portfolio.cash,
            equity=run.portfolio.equity,
            realized_pnl=run.portfolio.realized_pnl,
            unrealized_pnl=run.portfolio.unrealized_pnl,
            total_pnl=run.portfolio.total_pnl,
            gross_exposure=run.portfolio.gross_exposure,
            net_exposure=run.portfolio.net_exposure
        )

    return BacktestDetailDTO(
        id=run.id,
        strategy_id=run.strategy_version.strategy.id if run.strategy_version else "",
        strategy_name=run.strategy_version.strategy.name if run.strategy_version else "Strategy",
        status=run.status,
        error_message=run.error_message,
        initial_capital=run.initial_capital,
        final_capital=run.final_capital,
        total_net_pnl=run.total_net_pnl,
        total_trades=run.total_trades,
        win_rate=run.win_rate,
        sharpe_ratio=run.sharpe_ratio,
        max_drawdown_percent=run.max_drawdown_percent,
        equity_curve=run.equity_curve_json,
        trades=trades_dto,
        portfolio=portfolio_dto,
        created_at=run.created_at.isoformat()
    )


@router.get("/{backtest_id}/orders", response_model=List[OrderDTO])
async def get_backtest_orders(
    backtest_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(OrderModel)
        .join(BacktestRunModel)
        .where(OrderModel.backtest_run_id == backtest_id, BacktestRunModel.user_id == user_id)
    )
    orders = result.scalars().all()
    return [
        OrderDTO(
            id=o.id,
            signal_id=o.signal_id,
            instrument_id=o.instrument_id,
            symbol=o.symbol,
            side=o.side,
            order_type=o.order_type,
            quantity=o.quantity,
            status=o.status,
            execution_policy=o.execution_policy,
            created_at=o.created_at,
            eligible_at=o.eligible_at,
            idempotency_key=o.idempotency_key,
            rejection_reason=o.rejection_reason
        )
        for o in orders
    ]


@router.get("/{backtest_id}/executions", response_model=List[ExecutionDTO])
async def get_backtest_executions(
    backtest_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ExecutionModel)
        .join(BacktestRunModel)
        .where(ExecutionModel.backtest_run_id == backtest_id, BacktestRunModel.user_id == user_id)
    )
    executions = result.scalars().all()
    return [
        ExecutionDTO(
            id=e.id,
            order_id=e.order_id,
            instrument_id=e.instrument_id,
            symbol=e.symbol,
            timestamp=e.timestamp,
            side=e.side,
            quantity=e.quantity,
            reference_price=e.reference_price,
            execution_price=e.execution_price,
            slippage=e.slippage,
            status=e.status
        )
        for e in executions
    ]


@router.get("/{backtest_id}/portfolio", response_model=Optional[PortfolioDTO])
async def get_backtest_portfolio(
    backtest_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PortfolioModel)
        .join(BacktestRunModel)
        .where(PortfolioModel.backtest_run_id == backtest_id, BacktestRunModel.user_id == user_id)
    )
    port = result.scalars().first()
    if not port:
        return None
    return PortfolioDTO(
        id=port.id,
        initial_capital=port.initial_capital,
        cash=port.cash,
        equity=port.equity,
        realized_pnl=port.realized_pnl,
        unrealized_pnl=port.unrealized_pnl,
        total_pnl=port.total_pnl,
        gross_exposure=port.gross_exposure,
        net_exposure=port.net_exposure
    )


@router.get("/{backtest_id}/positions", response_model=List[PositionDTO])
async def get_backtest_positions(
    backtest_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(PositionModel)
        .join(PortfolioModel)
        .join(BacktestRunModel)
        .where(PositionModel.portfolio_id == PortfolioModel.id, PortfolioModel.backtest_run_id == backtest_id, BacktestRunModel.user_id == user_id)
    )
    positions = result.scalars().all()
    return [
        PositionDTO(
            id=p.id,
            symbol=p.symbol,
            side=p.side,
            quantity=p.quantity,
            average_entry_price=p.average_entry_price,
            current_price=p.current_price,
            realized_pnl=p.realized_pnl,
            unrealized_pnl=p.unrealized_pnl,
            status=p.status,
            opened_at=p.opened_at,
            last_updated_at=p.last_updated_at,
            holding_bars=p.holding_bars
        )
        for p in positions
    ]


@router.get("/{backtest_id}/risk-events", response_model=List[RiskEventDTO])
async def get_backtest_risk_events(
    backtest_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(RiskEventModel)
        .join(BacktestRunModel)
        .where(RiskEventModel.backtest_run_id == backtest_id, BacktestRunModel.user_id == user_id)
    )
    events = result.scalars().all()
    return [
        RiskEventDTO(
            id=ev.id,
            position_id=ev.position_id,
            symbol=ev.symbol,
            event_type=ev.event_type,
            timestamp=ev.timestamp,
            trigger_price=ev.trigger_price,
            reason=ev.reason
        )
        for ev in events
    ]


@router.get("/{backtest_id}/export/csv")
async def export_trades_csv(
    backtest_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(BacktestRunModel)
        .options(selectinload(BacktestRunModel.trades))
        .where(BacktestRunModel.id == backtest_id, BacktestRunModel.user_id == user_id)
    )
    run = result.scalars().first()
    if not run:
        raise HTTPException(status_code=404, detail="Backtest run not found.")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Trade ID", "Symbol", "Side", "Entry Time", "Entry Price",
        "Exit Time", "Exit Price", "Quantity", "Gross PnL", "Net PnL",
        "Total Costs", "Exit Reason"
    ])

    for t in run.trades:
        writer.writerow([
            t.trade_identifier, t.symbol, t.side, t.entry_time, t.entry_price,
            t.exit_time, t.exit_price, t.quantity, t.gross_pnl, t.net_pnl,
            t.total_costs, t.exit_reason
        ])

    output.seek(0)
    filename = f"backtest_trades_{backtest_id}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{backtest_id}/costs", response_model=List[TransactionCostBreakdownDTO])
async def get_backtest_costs(
    backtest_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all transaction cost breakdowns for executions in a backtest run."""
    result = await db.execute(
        select(TransactionCostModel)
        .join(BacktestRunModel)
        .where(TransactionCostModel.backtest_run_id == backtest_id, BacktestRunModel.user_id == user_id)
    )
    costs = result.scalars().all()
    return [
        TransactionCostBreakdownDTO(
            id=c.id,
            execution_id=c.execution_id,
            turnover=c.turnover,
            brokerage=c.brokerage,
            stt=c.stt,
            exchange_charges=c.exchange_charges,
            sebi_fees=c.sebi_fees,
            stamp_duty=c.stamp_duty,
            gst=c.gst,
            other_charges=c.other_charges,
            total_cost=c.total_cost
        )
        for c in costs
    ]

