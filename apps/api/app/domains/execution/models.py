"""
Execution Domain Models and Enums.

Defines Execution entity, execution policy enum, and status tracking.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
from decimal import Decimal


class ExecutionPolicy(str, Enum):
    """Supported execution timing policies."""
    NEXT_BAR_OPEN = "NEXT_BAR_OPEN"
    NEXT_BAR_MARKET = "NEXT_BAR_MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    INTRABAR = "INTRABAR"


class ExecutionStatus(str, Enum):
    """Status of simulated execution."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


@dataclass
class Execution:
    """Core domain model representing an executed trade fill."""
    id: str
    order_id: str
    instrument_id: str
    symbol: str
    timestamp: str
    side: str  # "BUY" or "SELL"
    quantity: Decimal
    reference_price: Decimal
    execution_price: Decimal
    slippage: Decimal
    status: ExecutionStatus = ExecutionStatus.SUCCESS
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Enforce Decimal types for numerical financial values
        if not isinstance(self.quantity, Decimal):
            self.quantity = Decimal(str(self.quantity))
        if not isinstance(self.reference_price, Decimal):
            self.reference_price = Decimal(str(self.reference_price))
        if not isinstance(self.execution_price, Decimal):
            self.execution_price = Decimal(str(self.execution_price))
        if not isinstance(self.slippage, Decimal):
            self.slippage = Decimal(str(self.slippage))
