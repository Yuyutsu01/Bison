"""
Cost Profile and Transaction Cost Domain Models.

Defines AssetClass, BrokerageModel, CostProfileVersion, and TransactionCostBreakdown
using precise Decimal types for financial charge calculations.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional
from decimal import Decimal


class AssetClass(str, Enum):
    """Supported Indian market asset segments."""
    EQUITY_DELIVERY = "EQUITY_DELIVERY"
    EQUITY_INTRADAY = "EQUITY_INTRADAY"
    INDEX_FUTURES = "INDEX_FUTURES"
    STOCK_FUTURES = "STOCK_FUTURES"
    INDEX_OPTIONS = "INDEX_OPTIONS"
    STOCK_OPTIONS = "STOCK_OPTIONS"


class BrokerageModel(str, Enum):
    """Supported brokerage fee structures."""
    FLAT_PER_ORDER = "FLAT_PER_ORDER"
    PERCENTAGE = "PERCENTAGE"
    PERCENTAGE_WITH_CAP = "PERCENTAGE_WITH_CAP"


class CostProfileNotFoundError(ValueError):
    """Raised when no matching cost profile is found for an execution timestamp."""
    pass


class InvalidCostProfileError(ValueError):
    """Raised when a cost profile contains invalid rates or configurations."""
    pass


class UnsupportedAssetClassError(ValueError):
    """Raised when an execution attempts cost calculation on an unsupported asset class."""
    pass


@dataclass
class CostProfileVersion:
    """Versioned configuration object for transaction fee & tax calculations."""
    id: str
    profile_id: str
    name: str
    version: int
    effective_from: str
    effective_to: str
    asset_class: AssetClass
    brokerage_model: BrokerageModel = BrokerageModel.PERCENTAGE_WITH_CAP
    brokerage_rate: Decimal = Decimal("0.0003")      # 0.03%
    brokerage_cap: Decimal = Decimal("20.0")          # Flat ₹20 cap
    brokerage_flat: Decimal = Decimal("20.0")         # Flat ₹20
    stt_buy_rate: Decimal = Decimal("0.0000")         # 0% STT on intraday buy
    stt_sell_rate: Decimal = Decimal("0.00025")       # 0.025% STT on intraday sell
    exchange_charge_rate: Decimal = Decimal("0.0000345")  # NSE 0.00345%
    sebi_fee_rate: Decimal = Decimal("0.000001")      # ₹10 per crore (0.0001%)
    stamp_duty_rate: Decimal = Decimal("0.00003")     # 0.003% on buy side
    gst_rate: Decimal = Decimal("0.18")               # 18% GST on taxable base
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Convert numerical fields to Decimal instances
        if not isinstance(self.brokerage_rate, Decimal):
            self.brokerage_rate = Decimal(str(self.brokerage_rate))
        if not isinstance(self.brokerage_cap, Decimal):
            self.brokerage_cap = Decimal(str(self.brokerage_cap))
        if not isinstance(self.brokerage_flat, Decimal):
            self.brokerage_flat = Decimal(str(self.brokerage_flat))
        if not isinstance(self.stt_buy_rate, Decimal):
            self.stt_buy_rate = Decimal(str(self.stt_buy_rate))
        if not isinstance(self.stt_sell_rate, Decimal):
            self.stt_sell_rate = Decimal(str(self.stt_sell_rate))
        if not isinstance(self.exchange_charge_rate, Decimal):
            self.exchange_charge_rate = Decimal(str(self.exchange_charge_rate))
        if not isinstance(self.sebi_fee_rate, Decimal):
            self.sebi_fee_rate = Decimal(str(self.sebi_fee_rate))
        if not isinstance(self.stamp_duty_rate, Decimal):
            self.stamp_duty_rate = Decimal(str(self.stamp_duty_rate))
        if not isinstance(self.gst_rate, Decimal):
            self.gst_rate = Decimal(str(self.gst_rate))


@dataclass
class TransactionCostBreakdown:
    """Itemized cost breakdown produced for an execution."""
    id: str
    execution_id: str
    cost_profile_version_id: str
    turnover: Decimal
    brokerage: Decimal
    stt: Decimal
    exchange_charges: Decimal
    sebi_fees: Decimal
    stamp_duty: Decimal
    gst: Decimal
    other_charges: Decimal = Decimal("0.0")
    total_cost: Decimal = Decimal("0.0")
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.turnover, Decimal):
            self.turnover = Decimal(str(self.turnover))
        if not isinstance(self.brokerage, Decimal):
            self.brokerage = Decimal(str(self.brokerage))
        if not isinstance(self.stt, Decimal):
            self.stt = Decimal(str(self.stt))
        if not isinstance(self.exchange_charges, Decimal):
            self.exchange_charges = Decimal(str(self.exchange_charges))
        if not isinstance(self.sebi_fees, Decimal):
            self.sebi_fees = Decimal(str(self.sebi_fees))
        if not isinstance(self.stamp_duty, Decimal):
            self.stamp_duty = Decimal(str(self.stamp_duty))
        if not isinstance(self.gst, Decimal):
            self.gst = Decimal(str(self.gst))
        if not isinstance(self.other_charges, Decimal):
            self.other_charges = Decimal(str(self.other_charges))
        if not isinstance(self.total_cost, Decimal):
            self.total_cost = Decimal(str(self.total_cost))
