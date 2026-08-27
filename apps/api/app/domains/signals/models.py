"""
Signal Engine Domain Entities.

Defines Signal types (BUY, SELL, EXIT) and deterministic Signal event data objects.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    EXIT = "EXIT"


@dataclass
class Signal:
    signal_id: str
    timestamp: str
    symbol: str
    signal_type: SignalType
    bar_index: int
    trigger_price: float
    reason: str
    indicator_snapshot: Dict[str, float] = field(default_factory=dict)
