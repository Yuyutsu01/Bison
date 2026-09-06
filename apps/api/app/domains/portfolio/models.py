"""
Portfolio & Position Domain Models.

Defines core financial entities (Portfolio, Position, PortfolioSnapshot, EquityPoint)
using precise Decimal arithmetic for cash, valuation, exposure, and P&L tracking.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List
from decimal import Decimal


class PositionSide(str, Enum):
    """Position direction."""
    LONG = "LONG"
    SHORT = "SHORT"


class PositionStatus(str, Enum):
    """Position status lifecycle."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class Position:
    """Core domain entity representing an active or closed position."""
    id: str
    portfolio_id: str
    instrument_id: str
    symbol: str
    side: PositionSide
    quantity: Decimal
    average_entry_price: Decimal
    current_price: Decimal
    realized_pnl: Decimal = Decimal("0.0")
    unrealized_pnl: Decimal = Decimal("0.0")
    opened_at: str = ""
    last_updated_at: str = ""
    holding_bars: int = 0
    status: PositionStatus = PositionStatus.OPEN
    highest_price_since_entry: Optional[Decimal] = None
    lowest_price_since_entry: Optional[Decimal] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Enforce Decimal types for numerical financial quantities
        if not isinstance(self.quantity, Decimal):
            self.quantity = Decimal(str(self.quantity))
        if not isinstance(self.average_entry_price, Decimal):
            self.average_entry_price = Decimal(str(self.average_entry_price))
        if not isinstance(self.current_price, Decimal):
            self.current_price = Decimal(str(self.current_price))
        if not isinstance(self.realized_pnl, Decimal):
            self.realized_pnl = Decimal(str(self.realized_pnl))
        if not isinstance(self.unrealized_pnl, Decimal):
            self.unrealized_pnl = Decimal(str(self.unrealized_pnl))
        if self.highest_price_since_entry is None:
            self.highest_price_since_entry = self.average_entry_price
        if self.lowest_price_since_entry is None:
            self.lowest_price_since_entry = self.average_entry_price

    @property
    def market_value(self) -> Decimal:
        """Market value of the position."""
        return self.quantity * self.current_price

    def update_market_price(self, price: Decimal) -> None:
        """
        Updates current market price and recalculates unrealized P&L.
        
        Important Logic:
        - LONG unrealized PnL = (current_price - average_entry_price) * quantity
        - SHORT unrealized PnL = (average_entry_price - current_price) * quantity
        - Trailing stop price trackers strictly update in favorable direction.
        """
        if not isinstance(price, Decimal):
            price = Decimal(str(price))
        self.current_price = price

        if self.side == PositionSide.LONG:
            self.unrealized_pnl = (self.current_price - self.average_entry_price) * self.quantity
            if self.highest_price_since_entry is None or price > self.highest_price_since_entry:
                self.highest_price_since_entry = price
        else:
            self.unrealized_pnl = (self.average_entry_price - self.current_price) * self.quantity
            if self.lowest_price_since_entry is None or price < self.lowest_price_since_entry:
                self.lowest_price_since_entry = price


@dataclass
class PortfolioSnapshot:
    """Point-in-time snapshot of portfolio valuation captured at every bar."""
    timestamp: str
    cash: Decimal
    equity: Decimal
    gross_exposure: Decimal
    net_exposure: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal
    open_position_count: int


@dataclass
class Portfolio:
    """Core domain entity representing the complete financial state of a account/backtest."""
    id: str
    backtest_run_id: str
    initial_capital: Decimal
    cash: Decimal
    equity: Decimal
    realized_pnl: Decimal = Decimal("0.0")
    unrealized_pnl: Decimal = Decimal("0.0")
    total_pnl: Decimal = Decimal("0.0")
    gross_exposure: Decimal = Decimal("0.0")
    net_exposure: Decimal = Decimal("0.0")
    positions: Dict[str, Position] = field(default_factory=dict)
    processed_execution_ids: set = field(default_factory=set)

    def __post_init__(self):
        if not isinstance(self.initial_capital, Decimal):
            self.initial_capital = Decimal(str(self.initial_capital))
        if not isinstance(self.cash, Decimal):
            self.cash = Decimal(str(self.cash))
        if not isinstance(self.equity, Decimal):
            self.equity = Decimal(str(self.equity))
        if not isinstance(self.realized_pnl, Decimal):
            self.realized_pnl = Decimal(str(self.realized_pnl))
        if not isinstance(self.unrealized_pnl, Decimal):
            self.unrealized_pnl = Decimal(str(self.unrealized_pnl))
        if not isinstance(self.total_pnl, Decimal):
            self.total_pnl = Decimal(str(self.total_pnl))
