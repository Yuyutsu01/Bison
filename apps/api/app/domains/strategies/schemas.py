"""
Strategy DSL Definitions and Pydantic Schemas.

Provides the formal, serializable JSON schema for rule-based quantitative trading strategies.
Used by both the visual strategy builder and the core backtesting engine.
"""

from enum import Enum
from typing import List, Dict, Any, Union, Optional
from pydantic import BaseModel, Field, field_validator


class TimeFrame(str, Enum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    D1 = "1d"


class Exchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"


class Operator(str, Enum):
    GREATER_THAN = "GREATER_THAN"
    LESS_THAN = "LESS_THAN"
    GREATER_THAN_EQUAL = "GREATER_THAN_EQUAL"
    LESS_THAN_EQUAL = "LESS_THAN_EQUAL"
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    CROSS_ABOVE = "CROSS_ABOVE"
    CROSS_BELOW = "CROSS_BELOW"


class LogicalOperator(str, Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class OperandType(str, Enum):
    PRICE = "price"
    INDICATOR = "indicator"
    CONSTANT = "constant"


class PriceField(str, Enum):
    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    VOLUME = "volume"


class PriceOperand(BaseModel):
    type: OperandType = OperandType.PRICE
    field: PriceField


class IndicatorOperand(BaseModel):
    type: OperandType = OperandType.INDICATOR
    name: str  # e.g., SMA, EMA, RSI, MACD, BB, ATR
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ConstantOperand(BaseModel):
    type: OperandType = OperandType.CONSTANT
    value: float


Operand = Union[PriceOperand, IndicatorOperand, ConstantOperand]


class Condition(BaseModel):
    left: Operand
    operator: Operator
    right: Operand


class RuleGroup(BaseModel):
    operator: LogicalOperator = LogicalOperator.AND
    conditions: List[Condition] = Field(default_factory=list)


class RiskManagement(BaseModel):
    stop_loss_percent: Optional[float] = Field(default=None)
    target_percent: Optional[float] = Field(default=None)
    trailing_stop_percent: Optional[float] = Field(default=None)
    max_holding_bars: Optional[int] = Field(default=None)
    end_of_day_exit: bool = Field(default=True)


class PositionSizingType(str, Enum):
    FIXED_QUANTITY = "FIXED_QUANTITY"
    PERCENT_OF_CAPITAL = "PERCENT_OF_CAPITAL"


class PositionSizing(BaseModel):
    type: PositionSizingType = PositionSizingType.FIXED_QUANTITY
    value: float = Field(default=1.0)


class InstrumentSpec(BaseModel):
    symbol: str
    exchange: Exchange = Exchange.NSE
    timeframe: TimeFrame = TimeFrame.M5


class StrategyDSL(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = None
    version: int = Field(default=1, ge=1)
    instrument: InstrumentSpec
    entry: RuleGroup
    exit: RuleGroup = Field(default_factory=RuleGroup)
    risk: RiskManagement = Field(default_factory=RiskManagement)
    position_sizing: PositionSizing = Field(default_factory=PositionSizing)

    @field_validator('name')
    def name_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Strategy name cannot be empty or whitespace.")
        return v.strip()
