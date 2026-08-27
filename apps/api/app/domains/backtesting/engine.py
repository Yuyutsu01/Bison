"""
Deterministic Event-Driven Backtesting Simulator Engine.

Executes rule-based quantitative trading strategies on historical OHLCV data.
Enforces zero look-ahead bias (orders generated on bar t execute strictly on bar t+1 Open).
Models Indian market transaction costs, slippage, position sizing, and risk rules.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from app.domains.strategies.schemas import StrategyDSL, PositionSizingType
from app.domains.indicators.calculator import IndicatorEngine
from app.domains.backtesting.costs import IndianTransactionCostCalculator, CostModelConfig
from app.domains.backtesting.evaluator import RuleEvaluator


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


class BacktestEngine:
    """Core event-driven simulation engine for quantitative backtests."""

    def __init__(
        self,
        strategy: StrategyDSL,
        initial_capital: float = 100000.0,
        cost_config: CostModelConfig = CostModelConfig()
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.cost_config = cost_config

    def run(self, df: pd.DataFrame) -> BacktestResult:
        if df.empty or len(df) < 2:
            raise ValueError("Input DataFrame is too short for backtesting.")

        df = df.copy()
        # Clean column names
        df.columns = [c.lower() for c in df.columns]
        if "timestamp" not in df.columns and "date" in df.columns:
            df["timestamp"] = df["date"]

        # 1. Pre-calculate all required indicators
        indicators = self._precalculate_indicators(df)

        # 2. Simulation state variables
        capital = self.initial_capital
        peak_capital = self.initial_capital
        active_position: Optional[TradeRecord] = None
        pending_order: Optional[Dict[str, Any]] = None  # Signal generated on bar t for execution on bar t+1
        trades: List[TradeRecord] = []
        equity_curve: List[EquityPoint] = []
        trade_counter = 0

        # Position sizing parameters
        pos_sizing = self.strategy.position_sizing
        risk = self.strategy.risk

        # 3. Bar-by-bar Event Loop (Chronological simulation)
        for i in range(len(df)):
            row = df.iloc[i]
            timestamp_str = str(row.get("timestamp", f"bar_{i}"))
            bar_open = float(row["open"])
            bar_high = float(row["high"])
            bar_low = float(row["low"])
            bar_close = float(row["close"])

            # A. Process Pending Order generated on previous bar (t-1) -> Fills on current bar t Open
            if pending_order is not None and active_position is None:
                side = pending_order["side"]
                # Calculate quantity based on position sizing
                if pos_sizing.type == PositionSizingType.FIXED_QUANTITY:
                    qty = pos_sizing.value
                else:
                    qty = (capital * (pos_sizing.value / 100.0)) / bar_open

                # Apply Indian friction & slippage to entry fill
                entry_cost = IndianTransactionCostCalculator.calculate_cost("BUY", qty, bar_open, self.cost_config)

                trade_counter += 1
                active_position = TradeRecord(
                    trade_id=f"TRD_{trade_counter:04d}",
                    symbol=self.strategy.instrument.symbol,
                    side=side,
                    entry_time=timestamp_str,
                    entry_price=entry_cost.executed_price_with_slippage,
                    quantity=qty,
                    total_costs=entry_cost.total_cost,
                    entry_indicators=self._get_indicator_snapshot(indicators, i)
                )
                pending_order = None

            # B. Check Risk Management / Exits for Active Position during bar t
            if active_position is not None:
                active_position.holding_bars += 1
                exit_triggered = False
                exit_price = bar_close
                exit_reason = None

                # 1. Stop-loss check
                if risk.stop_loss_percent is not None:
                    sl_price = active_position.entry_price * (1.0 - (risk.stop_loss_percent / 100.0))
                    if bar_low <= sl_price:
                        exit_triggered = True
                        exit_price = sl_price
                        exit_reason = "STOP_LOSS"

                # 2. Target check
                if not exit_triggered and risk.target_percent is not None:
                    target_price = active_position.entry_price * (1.0 + (risk.target_percent / 100.0))
                    if bar_high >= target_price:
                        exit_triggered = True
                        exit_price = target_price
                        exit_reason = "TARGET"

                # 3. Max holding period check
                if not exit_triggered and risk.max_holding_bars is not None:
                    if active_position.holding_bars >= risk.max_holding_bars:
                        exit_triggered = True
                        exit_price = bar_close
                        exit_reason = "MAX_HOLDING_EXCEEDED"

                # 4. Strategy Exit Conditions check
                if not exit_triggered and self.strategy.exit.conditions:
                    if RuleEvaluator.evaluate_rule_group(self.strategy.exit, df, indicators, i):
                        exit_triggered = True
                        exit_price = bar_close
                        exit_reason = "STRATEGY_EXIT_RULE"

                # 5. End of Day Exit check (if intraday session ending)
                if not exit_triggered and risk.end_of_day_exit and i == len(df) - 1:
                    exit_triggered = True
                    exit_price = bar_close
                    exit_reason = "END_OF_DAY"

                # Process Exit if triggered
                if exit_triggered:
                    exit_cost = IndianTransactionCostCalculator.calculate_cost(
                        "SELL", active_position.quantity, exit_price, self.cost_config
                    )
                    active_position.exit_time = timestamp_str
                    active_position.exit_price = exit_cost.executed_price_with_slippage
                    active_position.exit_reason = exit_reason
                    active_position.total_costs += exit_cost.total_cost
                    active_position.exit_indicators = self._get_indicator_snapshot(indicators, i)

                    # P&L Calculation
                    gross_pnl = (active_position.exit_price - active_position.entry_price) * active_position.quantity
                    net_pnl = gross_pnl - active_position.total_costs

                    active_position.gross_pnl = round(gross_pnl, 2)
                    active_position.net_pnl = round(net_pnl, 2)

                    capital += net_pnl
                    trades.append(active_position)
                    active_position = None

            # C. Evaluate Strategy Entry Rules at bar t close (Zero look-ahead: order fills on bar t+1 Open)
            if active_position is None and pending_order is None:
                if RuleEvaluator.evaluate_rule_group(self.strategy.entry, df, indicators, i):
                    pending_order = {"side": "BUY", "generated_bar": i}

            # D. Record Mark-to-Market Equity Point
            current_equity = capital
            if active_position is not None:
                unrealized_pnl = (bar_close - active_position.entry_price) * active_position.quantity
                current_equity += unrealized_pnl

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

        # 4. Calculate Final Performance Metrics
        return self._compute_metrics(trades, equity_curve, self.initial_capital, capital)

    def _precalculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        indicators: Dict[str, pd.Series] = {}

        # Scan entry and exit rules for indicator requirements
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

        # Calculate Sharpe Ratio
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
