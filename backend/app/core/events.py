"""
Event Definitions for Algorithmic Trading Core Engine.

Events are immutable data structures representing state changes or data arrivals
in the trading pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class EventType(str, Enum):
    MARKET_DATA = "MARKET_DATA"
    SIGNAL = "SIGNAL"
    ORDER = "ORDER"
    FILL = "FILL"
    PORTFOLIO = "PORTFOLIO"


class SignalDirection(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    EXIT = "EXIT"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


@dataclass(frozen=True)
class Event:
    """Base class for all immutable trading events."""
    event_type: EventType
    timestamp: datetime


@dataclass(frozen=True)
class MarketDataEvent(Event):
    """
    Emitted when a new market data bar (OHLCV) arrives.
    Contains timestamp, symbol, and open, high, low, close, volume price bar data.
    """
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self):
        object.__setattr__(self, 'event_type', EventType.MARKET_DATA)


@dataclass(frozen=True)
class SignalEvent(Event):
    """
    Emitted by a Strategy component when entry or exit criteria are triggered.
    Contains target symbol, direction (BUY/SELL/EXIT), and signal strength (0.0 - 1.0).
    """
    strategy_id: str
    symbol: str
    direction: SignalDirection
    strength: float = 1.0

    def __post_init__(self):
        object.__setattr__(self, 'event_type', EventType.SIGNAL)


@dataclass(frozen=True)
class OrderEvent(Event):
    """
    Emitted by Portfolio / Order Management System converting a Signal into an Order.
    Contains symbol, quantity (positive integer/float), and order_type (MARKET/LIMIT).
    """
    symbol: str
    quantity: float
    direction: SignalDirection
    order_type: OrderType = OrderType.MARKET
    price: Optional[float] = None

    def __post_init__(self):
        object.__setattr__(self, 'event_type', EventType.ORDER)


@dataclass(frozen=True)
class FillEvent(Event):
    """
    Emitted by Execution Handler when an Order is filled in the market.
    Incorporate real-world market friction: commission fee and price slippage.
    """
    symbol: str
    quantity: float
    direction: SignalDirection
    price: float
    commission: float
    slippage: float

    def __post_init__(self):
        object.__setattr__(self, 'event_type', EventType.FILL)


@dataclass(frozen=True)
class PortfolioEvent(Event):
    """
    Emitted after portfolio evaluation to snapshot mark-to-market holdings & performance.
    """
    cash: float
    holdings: dict[str, float]
    total_value: float

    def __post_init__(self):
        object.__setattr__(self, 'event_type', EventType.PORTFOLIO)
