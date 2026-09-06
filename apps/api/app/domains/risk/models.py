"""
Risk Engine Domain Models and Event Enums.

Defines RiskDecision, RiskEventType, and RiskEvent entities.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
from decimal import Decimal


class RiskEventType(str, Enum):
    """Structured risk event classification."""
    STOP_LOSS_TRIGGERED = "STOP_LOSS_TRIGGERED"
    TARGET_TRIGGERED = "TARGET_TRIGGERED"
    TRAILING_STOP_TRIGGERED = "TRAILING_STOP_TRIGGERED"
    MAX_HOLDING_TRIGGERED = "MAX_HOLDING_TRIGGERED"
    EOD_EXIT_TRIGGERED = "EOD_EXIT_TRIGGERED"
    MAX_POSITION_REJECTED = "MAX_POSITION_REJECTED"
    INSUFFICIENT_CAPITAL = "INSUFFICIENT_CAPITAL"


@dataclass
class RiskDecision:
    """Evaluation output from RiskEngine."""
    allowed: bool
    action: str  # "ALLOW_ENTRY", "REJECT_ENTRY", "EXIT_POSITION", "HOLD"
    reason: Optional[str] = None
    trigger_price: Optional[Decimal] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskEvent:
    """Structured risk log event for Trade Inspector and auditing."""
    id: str
    portfolio_id: str
    position_id: Optional[str]
    symbol: str
    event_type: RiskEventType
    timestamp: str
    trigger_price: Decimal
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.trigger_price, Decimal):
            self.trigger_price = Decimal(str(self.trigger_price))
