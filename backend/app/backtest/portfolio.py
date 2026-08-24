"""
Portfolio Tracker & Order Management System (OMS).

Tracks positions, cash balance, unrealized/realized P&L, and equity curve history.
Converts SignalEvents into OrderEvents based on position sizing rules.
Updates portfolio state on FillEvents.
"""

from datetime import datetime
from typing import Dict, List, Optional
import logging

from app.core.events import (
    EventType, SignalEvent, SignalDirection,
    OrderEvent, OrderType, FillEvent, PortfolioEvent, MarketDataEvent
)
from app.core.event_bus import EventBus

logger = logging.getLogger(__name__)


class TradeRecord:
    """Represents a completed or active trade position log."""
    def __init__(self, trade_id: int, symbol: str, entry_time: datetime, entry_price: float, quantity: float, direction: str):
        self.trade_id = trade_id
        self.symbol = symbol
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.quantity = quantity
        self.direction = direction
        self.exit_time: Optional[datetime] = None
        self.exit_price: Optional[float] = None
        self.pnl: float = 0.0
        self.pnl_pct: float = 0.0
        self.is_open: bool = True

    def close_trade(self, exit_time: datetime, exit_price: float, commission: float):
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.is_open = False
        
        if self.direction == "BUY":
            raw_pnl = (self.exit_price - self.entry_price) * self.quantity
        else:
            raw_pnl = (self.entry_price - self.exit_price) * self.quantity
            
        self.pnl = raw_pnl - commission
        cost_basis = self.entry_price * self.quantity
        self.pnl_pct = (self.pnl / cost_basis) * 100.0 if cost_basis > 0 else 0.0


class PortfolioTracker:
    """
    Maintains real-time portfolio balance, position sizing, and trade logs during backtesting.
    """

    def __init__(self, event_bus: EventBus, initial_capital: float = 100000.0, position_size_pct: float = 0.95):
        self.event_bus = event_bus
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.position_size_pct = position_size_pct  # Allocates % of available cash per trade

        # Holdings map: symbol -> quantity
        self.holdings: Dict[str, float] = {}
        # Cost basis map: symbol -> avg purchase price
        self.cost_basis: Dict[str, float] = {}
        
        # Latest market price map: symbol -> price
        self.current_prices: Dict[str, float] = {}
        
        # Equity curve time-series logs: list of dicts {"timestamp": ..., "equity": ..., "cash": ...}
        self.equity_curve: List[dict] = []
        
        # Trade logs
        self.trades: List[TradeRecord] = []
        self._active_trade: Optional[TradeRecord] = None
        self._trade_counter = 0

        # Subscribe to relevant events
        self.event_bus.subscribe(EventType.MARKET_DATA, self.on_market_data)
        self.event_bus.subscribe(EventType.SIGNAL, self.on_signal)
        self.event_bus.subscribe(EventType.FILL, self.on_fill)

    def get_total_equity(self) -> float:
        """Mark-to-market total portfolio valuation (cash + market value of open holdings)."""
        holdings_value = sum(
            qty * self.current_prices.get(sym, self.cost_basis.get(sym, 0.0))
            for sym, qty in self.holdings.items()
        )
        return self.cash + holdings_value

    def on_market_data(self, event: MarketDataEvent) -> None:
        """Update latest market price and snapshot portfolio equity curve."""
        self.current_prices[event.symbol] = event.close
        total_equity = self.get_total_equity()
        
        self.equity_curve.append({
            "timestamp": event.timestamp.strftime("%Y-%m-%d %H:%M:%S") if isinstance(event.timestamp, datetime) else str(event.timestamp),
            "equity": round(total_equity, 2),
            "cash": round(self.cash, 2)
        })

    def on_signal(self, event: SignalEvent) -> None:
        """
        Convert a SignalEvent into an OrderEvent with risk-managed position sizing.
        """
        current_price = self.current_prices.get(event.symbol)
        if not current_price or current_price <= 0:
            return

        current_qty = self.holdings.get(event.symbol, 0.0)

        if event.direction == SignalDirection.BUY and current_qty == 0:
            # Calculate quantity to purchase based on available cash and position size allocation
            allocated_cash = self.cash * self.position_size_pct
            quantity = int(allocated_cash // current_price)
            if quantity > 0:
                order = OrderEvent(
                    event_type=None,
                    timestamp=event.timestamp,
                    symbol=event.symbol,
                    quantity=float(quantity),
                    direction=SignalDirection.BUY,
                    order_type=OrderType.MARKET
                )
                self.event_bus.put(order)

        elif event.direction in (SignalDirection.SELL, SignalDirection.EXIT) and current_qty > 0:
            # Close existing position
            order = OrderEvent(
                event_type=None,
                timestamp=event.timestamp,
                symbol=event.symbol,
                quantity=current_qty,
                direction=SignalDirection.SELL,
                order_type=OrderType.MARKET
            )
            self.event_bus.put(order)

    def on_fill(self, event: FillEvent) -> None:
        """
        Update cash, holdings, cost basis, and trade records when an order is executed.
        """
        total_cost = (event.price * event.quantity) + event.commission

        if event.direction == SignalDirection.BUY:
            self.cash -= total_cost
            self.holdings[event.symbol] = self.holdings.get(event.symbol, 0.0) + event.quantity
            self.cost_basis[event.symbol] = event.price
            
            # Start trade log
            self._trade_counter += 1
            self._active_trade = TradeRecord(
                trade_id=self._trade_counter,
                symbol=event.symbol,
                entry_time=event.timestamp,
                entry_price=event.price,
                quantity=event.quantity,
                direction="BUY"
            )
            self.trades.append(self._active_trade)

        elif event.direction in (SignalDirection.SELL, SignalDirection.EXIT):
            gross_proceeds = event.price * event.quantity
            net_proceeds = gross_proceeds - event.commission
            self.cash += net_proceeds
            
            self.holdings[event.symbol] = max(0.0, self.holdings.get(event.symbol, 0.0) - event.quantity)
            
            if self._active_trade and self._active_trade.is_open:
                self._active_trade.close_trade(event.timestamp, event.price, event.commission)
                self._active_trade = None
