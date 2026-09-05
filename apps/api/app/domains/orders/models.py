"""
Order Domain Entities and State Machine.

Defines Order types, sides, statuses, state transitions, and validation rules.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, Set
from decimal import Decimal
import hashlib


class OrderSide(str, Enum):
    """Supported order sides and position intents."""
    BUY = "BUY"
    SELL = "SELL"
    LONG_ENTRY = "LONG_ENTRY"
    LONG_EXIT = "LONG_EXIT"
    SHORT_ENTRY = "SHORT_ENTRY"
    SHORT_EXIT = "SHORT_EXIT"

    @property
    def is_buy_side(self) -> bool:
        """Returns True if the order side acts as a buy/long entry/short exit."""
        return self in (OrderSide.BUY, OrderSide.LONG_ENTRY, OrderSide.SHORT_EXIT)


class OrderType(str, Enum):
    """Order type classification."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderStatus(str, Enum):
    """Lifecycle state machine states for orders."""
    CREATED = "CREATED"
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


# Define legal state machine transitions for orders
LEGAL_TRANSITIONS: Dict[OrderStatus, Set[OrderStatus]] = {
    OrderStatus.CREATED: {OrderStatus.PENDING, OrderStatus.REJECTED, OrderStatus.CANCELLED, OrderStatus.EXPIRED},
    OrderStatus.PENDING: {OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.EXPIRED},
    OrderStatus.FILLED: set(),      # Terminal state
    OrderStatus.CANCELLED: set(),   # Terminal state
    OrderStatus.REJECTED: set(),    # Terminal state
    OrderStatus.EXPIRED: set(),     # Terminal state
}


class InvalidStateTransitionError(ValueError):
    """Raised when an illegal order status transition is attempted."""
    pass


class UnsupportedOrderTypeError(ValueError):
    """Raised when an order type not yet implemented in execution simulator is processed."""
    pass


class OrderValidationError(ValueError):
    """Raised when an order fails quantity, lot size, or parameter validation."""
    pass


@dataclass
class Order:
    """Core domain model representing a trading order."""
    id: str
    strategy_id: str
    strategy_version_id: str
    signal_id: str
    instrument_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    created_at: str
    eligible_at: str
    status: OrderStatus = OrderStatus.CREATED
    requested_price: Optional[Decimal] = None
    execution_policy: str = "NEXT_BAR_OPEN"
    rejection_reason: Optional[str] = None
    idempotency_key: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Ensure financial values are Decimal instances
        if not isinstance(self.quantity, Decimal):
            self.quantity = Decimal(str(self.quantity))
        if self.requested_price is not None and not isinstance(self.requested_price, Decimal):
            self.requested_price = Decimal(str(self.requested_price))
        if not self.idempotency_key:
            self.idempotency_key = self.generate_idempotency_key(
                strategy_version_id=self.strategy_version_id,
                signal_timestamp=self.created_at,
                symbol=self.symbol,
                side=self.side.value
            )

    @staticmethod
    def generate_idempotency_key(
        strategy_version_id: str,
        signal_timestamp: str,
        symbol: str,
        side: str
    ) -> str:
        """Generates a deterministic idempotency key for duplicate signal protection."""
        raw_key = f"{strategy_version_id}:{signal_timestamp}:{symbol}:{side}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]

    def transition_to(self, new_status: OrderStatus, reason: Optional[str] = None) -> None:
        """
        Transitions order to a new state if legally allowed by the state machine.
        
        Important Logic:
        - Prevents illegal transitions (e.g. FILLED -> PENDING or CANCELLED -> FILLED).
        - Records rejection or cancellation reason when moving to failed states.
        """
        allowed = LEGAL_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                f"Cannot transition order {self.id} from state '{self.status.value}' to '{new_status.value}'."
            )
        self.status = new_status
        if reason:
            self.rejection_reason = reason
