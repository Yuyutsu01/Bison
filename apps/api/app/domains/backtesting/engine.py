"""
Deterministic Event-Driven Backtesting Simulator Engine.

Executes rule-based quantitative trading strategies on historical OHLCV data.
Enforces zero look-ahead bias (orders generated on bar t execute strictly on bar t+1 Open).
Integrates Order Domain, Execution Simulator, Portfolio Engine, and Risk Engine.
"""

import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from decimal import Decimal
import pandas as pd
import numpy as np

from app.domains.strategies.schemas import StrategyDSL, PositionSizingType
from app.domains.indicators.calculator import IndicatorEngine
from app.domains.signals.models import Signal, SignalType
from app.domains.orders.models import Order, OrderStatus, OrderType
from app.domains.orders.factory import OrderFactory
from app.domains.execution.models import Execution
from app.domains.execution.simulator import ExecutionSimulator
from app.domains.execution.slippage import SlippageModel, FixedPointsSlippage, PercentageSlippage, ZeroSlippage
from app.domains.backtesting.costs import IndianTransactionCostCalculator, CostModelConfig, SlippageType
from app.domains.backtesting.evaluator import RuleEvaluator

from app.domains.portfolio.models import (
    Portfolio, Position, PositionSide, PositionStatus, PortfolioSnapshot
)
from app.domains.portfolio.service import PortfolioService
from app.domains.portfolio.sizing import PositionSizingEngine
from app.domains.risk.models import RiskEvent, RiskEventType
from app.domains.risk.engine import RiskEngine


@dataclass
class TradeRecord:
    trade_id: str
    symbol: str
    side: str  # "BUY" or "SELL"
    entry_time: str
    entry_price: float
    exit_time: Optional[str] = None
    exit_price: Optional[float] = None
    quantity: float = 1.0
    gross_pnl: float = 0.0
    net_pnl: float = 0.0
    total_costs: float = 0.0
    exit_reason: Optional[str] = None
    holding_bars: int = 0
    entry_indicators: Dict[str, float] = field(default_factory=dict)
    exit_indicators: Dict[str, float] = field(default_factory=dict)


@dataclass
class EquityPoint:
    timestamp: str
    equity: float
    cash: float
    drawdown: float
    drawdown_percent: float


@dataclass
class BacktestResult:
    trades: List[TradeRecord]
    equity_curve: List[EquityPoint]
    initial_capital: float
    final_capital: float
    total_net_pnl: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    profit_factor: float
    max_drawdown_percent: float
    sharpe_ratio: float
    orders: List[Order] = field(default_factory=list)
    executions: List[Execution] = field(default_factory=list)
    portfolio: Optional[Portfolio] = None
    snapshots: List[PortfolioSnapshot] = field(default_factory=list)
    risk_events: List[RiskEvent] = field(default_factory=list)
    positions: List[Position] = field(default_factory=list)


class BacktestEngine:
    """Core event-driven simulation engine integrating Portfolio & Risk Engine."""

    def __init__(
        self,
        strategy: StrategyDSL,
        initial_capital: float = 100000.0,
        cost_config: CostModelConfig = CostModelConfig(),
        slippage_model: Optional[SlippageModel] = None,
        max_simultaneous_positions: Optional[int] = None
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.cost_config = cost_config
        self.max_simultaneous_positions = max_simultaneous_positions

        if slippage_model is not None:
            self.slippage_model = slippage_model
        elif cost_config.slippage_type == SlippageType.ZERO:
            self.slippage_model = ZeroSlippage()
        elif cost_config.slippage_type == SlippageType.PERCENTAGE:
            self.slippage_model = PercentageSlippage(Decimal(str(cost_config.slippage_value)))
        else:
            self.slippage_model = FixedPointsSlippage(Decimal(str(cost_config.slippage_value)))

        self.execution_simulator = ExecutionSimulator(slippage_model=self.slippage_model)

    def run(self, df: pd.DataFrame) -> BacktestResult:
        if df.empty or len(df) < 2:
            raise ValueError("Input DataFrame is too short for backtesting.")

        df = df.copy()
        df.columns = [c.lower() for c in df.columns]
        if "timestamp" not in df.columns and "date" in df.columns:
            df["timestamp"] = df["date"]

        # 1. Pre-calculate indicators
        indicators = self._precalculate_indicators(df)

        # 2. Initialize Portfolio Domain & Service
        initial_cap_dec = Decimal(str(self.initial_capital))
        portfolio = Portfolio(
            id=f"PORT_{uuid.uuid4().hex[:12]}",
            backtest_run_id="BACKTEST_RUN",
            initial_capital=initial_cap_dec,
            cash=initial_cap_dec,
            equity=initial_cap_dec
        )
        portfolio_service = PortfolioService(portfolio)

        # State tracking variables
        capital = self.initial_capital
        peak_capital = self.initial_capital
        active_trade: Optional[TradeRecord] = None
        pending_order: Optional[Order] = None

        trades: List[TradeRecord] = []
        all_orders: List[Order] = []
        all_executions: List[Execution] = []
        all_snapshots: List[PortfolioSnapshot] = []
        all_risk_events: List[RiskEvent] = []
        equity_curve: List[EquityPoint] = []
        trade_counter = 0

        pos_sizing = self.strategy.position_sizing
        risk = self.strategy.risk
        symbol = self.strategy.instrument.symbol
        lot_size = Decimal(str(getattr(self.strategy.instrument, "lot_size", 1)))

        # 3. Bar-by-Bar Chronological Event Loop
        for i in range(len(df)):
            row = df.iloc[i]
            timestamp_str = str(row.get("timestamp", f"bar_{i}"))
            bar_open = float(row["open"])
            bar_high = float(row["high"])
            bar_low = float(row["low"])
            bar_close = float(row["close"])
            bar_dict = {
                "open": bar_open,
                "high": bar_high,
                "low": bar_low,
                "close": bar_close,
                "symbol": symbol,
                "timestamp": timestamp_str
            }
            is_final_bar = (i == len(df) - 1)

            # A. Process Pending Order (generated on previous bar t-1) -> Fills on bar t Open
            if pending_order is not None:
                execution = self.execution_simulator.simulate_execution(
                    order=pending_order,
                    bar=bar_dict,
                    tick_size=Decimal("0.05")
                )

                if execution is not None:
                    all_executions.append(execution)
                    exec_qty = float(execution.quantity)
                    exec_price = float(execution.execution_price)

                    # Source of Truth: Apply Execution to Portfolio
                    portfolio_service.apply_execution(execution)

                    if execution.side in ("BUY", "LONG_ENTRY"):
                        entry_cost = IndianTransactionCostCalculator.calculate_cost("BUY", exec_qty, exec_price, self.cost_config)
                        trade_counter += 1
                        active_trade = TradeRecord(
                            trade_id=f"TRD_{trade_counter:04d}",
                            symbol=symbol,
                            side=execution.side,
                            entry_time=timestamp_str,
                            entry_price=exec_price,
                            quantity=exec_qty,
                            total_costs=entry_cost.total_cost,
                            entry_indicators=self._get_indicator_snapshot(indicators, i)
                        )
                    elif execution.side in ("SELL", "LONG_EXIT") and active_trade is not None:
                        exit_cost = IndianTransactionCostCalculator.calculate_cost("SELL", exec_qty, exec_price, self.cost_config)
                        active_trade.exit_time = timestamp_str
                        active_trade.exit_price = exec_price
                        active_trade.exit_reason = pending_order.metadata.get("signal_reason", "EXIT_ORDER")
                        active_trade.total_costs += exit_cost.total_cost
                        active_trade.exit_indicators = self._get_indicator_snapshot(indicators, i)

                        gross_pnl = (active_trade.exit_price - active_trade.entry_price) * active_trade.quantity
                        net_pnl = gross_pnl - active_trade.total_costs
                        active_trade.gross_pnl = round(gross_pnl, 2)
                        active_trade.net_pnl = round(net_pnl, 2)

                        trades.append(active_trade)
                        active_trade = None

                pending_order = None

            # B. Mark-to-Market Portfolio Revaluation
            snapshot = portfolio_service.mark_to_market(bar_dict, timestamp_str)
            all_snapshots.append(snapshot)
            capital = float(portfolio.cash)
            current_equity = float(portfolio.equity)

            # C. Evaluate Risk Engine on Open Positions during bar t
            open_pos = portfolio.positions.get(symbol)
            if open_pos is not None and open_pos.status == PositionStatus.OPEN and pending_order is None:
                risk_event = RiskEngine.evaluate_position_risk(
                    portfolio=portfolio,
                    position=open_pos,
                    bar=bar_dict,
                    risk_config=risk,
                    is_final_bar=is_final_bar
                )

                if risk_event is not None:
                    all_risk_events.append(risk_event)

                    # Risk rule creates an Exit Signal -> Exit Order (never directly mutates position)
                    next_ts = str(df.iloc[i + 1]["timestamp"]) if (i + 1 < len(df) and "timestamp" in df.columns) else f"bar_{i+1}"
                    exit_signal = Signal(
                        signal_id=f"SIG_RISK_{i:04d}",
                        timestamp=timestamp_str,
                        symbol=symbol,
                        signal_type=SignalType.SELL,
                        bar_index=i,
                        trigger_price=float(risk_event.trigger_price),
                        reason=risk_event.reason,
                        indicator_snapshot=self._get_indicator_snapshot(indicators, i)
                    )

                    exit_order = OrderFactory.create_order_from_signal(
                        signal=exit_signal,
                        strategy_id="STRAT_BACKTEST",
                        strategy_version_id="VER_1",
                        quantity=open_pos.quantity,
                        eligible_at_timestamp=next_ts,
                        instrument_id=symbol,
                        lot_size=lot_size
                    )
                    pending_order = exit_order
                    all_orders.append(exit_order)

            # D. Evaluate Strategy Entry Rules if no open position and no pending exit order
            if open_pos is None and pending_order is None:
                if RuleEvaluator.evaluate_rule_group(self.strategy.entry, df, indicators, i):
                    # Check Risk Engine for max positions
                    entry_risk_decision = RiskEngine.evaluate_entry_risk(
                        portfolio=portfolio,
                        max_simultaneous_positions=self.max_simultaneous_positions
                    )

                    if not entry_risk_decision.allowed:
                        event_id = f"RSK_REJ_{uuid.uuid4().hex[:12]}"
                        all_risk_events.append(RiskEvent(
                            id=event_id,
                            portfolio_id=portfolio.id,
                            position_id=None,
                            symbol=symbol,
                            event_type=RiskEventType.MAX_POSITION_REJECTED,
                            timestamp=timestamp_str,
                            trigger_price=Decimal(str(bar_close)),
                            reason=entry_risk_decision.reason or "MAX_POSITIONS_REACHED"
                        ))
                    else:
                        # Entry signal generated
                        signal = Signal(
                            signal_id=f"SIG_ENT_{i:04d}",
                            timestamp=timestamp_str,
                            symbol=symbol,
                            signal_type=SignalType.BUY,
                            bar_index=i,
                            trigger_price=bar_close,
                            reason="ENTRY_RULE_TRIGGERED",
                            indicator_snapshot=self._get_indicator_snapshot(indicators, i)
                        )

                        next_ts = str(df.iloc[i + 1]["timestamp"]) if (i + 1 < len(df) and "timestamp" in df.columns) else f"bar_{i+1}"

                        # Calculate quantity via PositionSizingEngine
                        order_qty = PositionSizingEngine.calculate_quantity(
                            position_sizing=pos_sizing,
                            available_cash=portfolio.cash,
                            reference_price=Decimal(str(bar_close)),
                            lot_size=lot_size
                        )

                        order = OrderFactory.create_order_from_signal(
                            signal=signal,
                            strategy_id="STRAT_BACKTEST",
                            strategy_version_id="VER_1",
                            quantity=order_qty,
                            eligible_at_timestamp=next_ts,
                            instrument_id=symbol,
                            lot_size=lot_size
                        )
                        pending_order = order
                        all_orders.append(order)

            # E. Record Equity Curve Point
            if current_equity > peak_capital:
                peak_capital = current_equity

            drawdown = peak_capital - current_equity
            drawdown_percent = (drawdown / peak_capital * 100.0) if peak_capital > 0 else 0.0

            equity_curve.append(EquityPoint(
                timestamp=timestamp_str,
                equity=round(current_equity, 2),
                cash=round(capital, 2),
                drawdown=round(drawdown, 2),
                drawdown_percent=round(drawdown_percent, 2)
            ))

        # Handle active trade remaining open at end of simulation
        if active_trade is not None:
            last_timestamp = str(df.iloc[-1].get("timestamp", "end"))
            last_close = float(df.iloc[-1]["close"])
            active_trade.exit_time = last_timestamp
            active_trade.exit_price = last_close
            active_trade.exit_reason = "END_OF_SIMULATION"
            gross_pnl = (active_trade.exit_price - active_trade.entry_price) * active_trade.quantity
            active_trade.gross_pnl = round(gross_pnl, 2)
            active_trade.net_pnl = round(gross_pnl - active_trade.total_costs, 2)
            trades.append(active_trade)

        # Handle pending order on final candle
        if pending_order is not None and pending_order.status == OrderStatus.CREATED:
            self.execution_simulator.simulate_execution(order=pending_order, bar=None)

        # Compute performance metrics
        res = self._compute_metrics(trades, equity_curve, self.initial_capital, float(portfolio.equity))
        res.orders = all_orders
        res.executions = all_executions
        res.portfolio = portfolio
        res.snapshots = all_snapshots
        res.risk_events = all_risk_events
        res.positions = list(portfolio.positions.values())
        return res

    def _precalculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        indicators: Dict[str, pd.Series] = {}
        all_conditions = self.strategy.entry.conditions + self.strategy.exit.conditions

        for cond in all_conditions:
            for operand in (cond.left, cond.right):
                if operand.type == "indicator":
                    name = operand.name.upper()
                    params = getattr(operand, "parameters", {})
                    key = RuleEvaluator._get_indicator_key(operand)

                    if key not in indicators:
                        if name == "SMA":
                            indicators[key] = IndicatorEngine.calculate_sma(df, period=params.get("period", 20))
                        elif name == "EMA":
                            indicators[key] = IndicatorEngine.calculate_ema(df, period=params.get("period", 20))
                        elif name == "RSI":
                            indicators[key] = IndicatorEngine.calculate_rsi(df, period=params.get("period", 14))
                        elif name == "ATR":
                            indicators[key] = IndicatorEngine.calculate_atr(df, period=params.get("period", 14))
                        elif name == "MACD":
                            macd_dict = IndicatorEngine.calculate_macd(
                                df,
                                fast_period=params.get("fast_period", 12),
                                slow_period=params.get("slow_period", 26),
                                signal_period=params.get("signal_period", 9)
                            )
                            indicators[key] = macd_dict["macd"]

        return indicators

    def _get_indicator_snapshot(self, indicators: Dict[str, pd.Series], idx: int) -> Dict[str, float]:
        snapshot = {}
        for k, series in indicators.items():
            val = series.iloc[idx]
            snapshot[k] = round(float(val), 2) if not np.isnan(val) else 0.0
        return snapshot

    def _compute_metrics(
        self,
        trades: List[TradeRecord],
        equity_curve: List[EquityPoint],
        initial_capital: float,
        final_capital: float
    ) -> BacktestResult:
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.net_pnl > 0])
        losing_trades = len([t for t in trades if t.net_pnl <= 0])
        win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0

        gross_profits = sum(t.net_pnl for t in trades if t.net_pnl > 0)
        gross_losses = abs(sum(t.net_pnl for t in trades if t.net_pnl < 0))
        profit_factor = (gross_profits / gross_losses) if gross_losses > 0 else (gross_profits if gross_profits > 0 else 0.0)

        max_dd_percent = max([eq.drawdown_percent for eq in equity_curve]) if equity_curve else 0.0

        equities = pd.Series([eq.equity for eq in equity_curve])
        returns = equities.pct_change().dropna()
        if len(returns) > 1 and returns.std() > 0:
            sharpe_ratio = float((returns.mean() / returns.std()) * np.sqrt(252))
        else:
            sharpe_ratio = 0.0

        total_net_pnl = final_capital - initial_capital

        return BacktestResult(
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=initial_capital,
            final_capital=round(final_capital, 2),
            total_net_pnl=round(total_net_pnl, 2),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=round(win_rate, 2),
            profit_factor=round(profit_factor, 2),
            max_drawdown_percent=round(max_dd_percent, 2),
            sharpe_ratio=round(sharpe_ratio, 2)
        )
