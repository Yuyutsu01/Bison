"""
Core Backtesting Execution Engine.

Orchestrates the synchronous event loop:
1. Yields MarketDataEvents chronologically from DataReplayIterator.
2. Executes pending OrderEvents using the next bar's Open price (avoiding look-ahead bias).
3. Applies commission fees and slippage models to produce FillEvents.
4. Passes MarketDataEvents to Strategy components to generate SignalEvents.
5. Processes Portfolio updates and calculates end-of-run analytics.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import pandas as pd

from app.core.events import (
    EventType, MarketDataEvent, OrderEvent, FillEvent, SignalDirection
)
from app.core.event_bus import EventBus
from app.data.replay import DataReplayIterator
from app.strategies.base import StrategyRegistry, BaseStrategy
from app.backtest.portfolio import PortfolioTracker
from app.backtest.metrics import PerformanceMetrics

logger = logging.getLogger(__name__)


class ExecutionModel:
    """
    Simulates real-world market execution mechanics.
    Fills orders at the next bar's Open price, factoring in commission fees and slippage.
    """

    def __init__(self, commission_per_trade: float = 1.0, slippage_bps: float = 5.0):
        self.commission_per_trade = commission_per_trade
        self.slippage_pct = slippage_bps / 10000.0  # Basis points to percentage multiplier

    def fill_order(self, order: OrderEvent, fill_price: float, timestamp: datetime) -> FillEvent:
        # Apply slippage: increase price for BUYs, decrease price for SELLs
        if order.direction == SignalDirection.BUY:
            actual_price = fill_price * (1.0 + self.slippage_pct)
            slippage_amt = actual_price - fill_price
        else:
            actual_price = fill_price * (1.0 - self.slippage_pct)
            slippage_amt = fill_price - actual_price

        return FillEvent(
            event_type=None,
            timestamp=timestamp,
            symbol=order.symbol,
            quantity=order.quantity,
            direction=order.direction,
            price=round(actual_price, 4),
            commission=self.commission_per_trade,
            slippage=round(slippage_amt * order.quantity, 4)
        )


class BacktestEngine:
    """
    High-performance event-driven backtesting runner.
    """

    def __init__(
        self,
        symbol: str,
        df_data: pd.DataFrame,
        strategy_name: str,
        strategy_config: dict,
        initial_capital: float = 100000.0,
        commission: float = 1.0,
        slippage_bps: float = 5.0
    ):
        self.symbol = symbol
        self.df_data = df_data
        self.strategy_name = strategy_name
        self.strategy_config = strategy_config
        self.initial_capital = initial_capital
        
        # Instantiate Core Components
        self.event_bus = EventBus()
        self.portfolio = PortfolioTracker(self.event_bus, initial_capital=initial_capital)
        self.execution = ExecutionModel(commission_per_trade=commission, slippage_bps=slippage_bps)
        self.replay = DataReplayIterator(df_data, symbol)

        # Dynamically load Strategy from registry
        strategy_cls = StrategyRegistry.get_strategy_class(strategy_name)
        self.strategy: BaseStrategy = strategy_cls(
            strategy_id=f"{strategy_name}_1",
            symbol=symbol,
            event_bus=self.event_bus,
            config=strategy_config
        )

        # Pending order queue to execute at next bar's Open price
        self._pending_orders: List[OrderEvent] = []
        self.event_bus.subscribe(EventType.ORDER, self._on_order)

    def _on_order(self, event: OrderEvent) -> None:
        """Queue order for fill on the next market bar."""
        self._pending_orders.append(event)

    def run(self) -> Dict[str, Any]:
        """
        Execute synchronous backtest loop over all historical market data bars.
        """
        self.strategy.on_start()

        for market_event in self.replay:
            # 1. Fill pending orders using current bar's OPEN price (eliminating look-ahead bias)
            if self._pending_orders:
                for order in self._pending_orders:
                    fill = self.execution.fill_order(
                        order=order,
                        fill_price=market_event.open,
                        timestamp=market_event.timestamp
                    )
                    self.event_bus.put(fill)
                self._pending_orders.clear()

            # 2. Dispatch MarketDataEvent to Portfolio & Strategy
            self.event_bus.put(market_event)

            # 3. Strategy processes bar and may publish SignalEvents
            signals = self.strategy.on_market_data(market_event)
            for sig in signals:
                self.event_bus.put(sig)

            # 4. Drain event queue for this bar
            self.event_bus.process_all()

        # Compute final quantitative metrics
        metrics = PerformanceMetrics.calculate(
            equity_curve=self.portfolio.equity_curve,
            trades=self.portfolio.trades,
            initial_capital=self.initial_capital
        )

        # Format trade log for API payload
        trades_list = [
            {
                "id": t.trade_id,
                "symbol": t.symbol,
                "entry_time": t.entry_time.strftime("%Y-%m-%d %H:%M:%S") if isinstance(t.entry_time, datetime) else str(t.entry_time),
                "exit_time": t.exit_time.strftime("%Y-%m-%d %H:%M:%S") if t.exit_time else "OPEN",
                "direction": t.direction,
                "quantity": t.quantity,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price if t.exit_price else 0.0,
                "pnl": round(t.pnl, 2),
                "pnl_pct": round(t.pnl_pct, 2)
            }
            for t in self.portfolio.trades
        ]

        return {
            "status": "COMPLETED",
            "metrics": metrics,
            "equity_curve": self.portfolio.equity_curve,
            "trades": trades_list
        }
