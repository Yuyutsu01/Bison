"""
Indian Market Transaction Cost & Friction Model.

Calculates realistic trading fees for Indian exchanges (NSE/BSE) including:
- Brokerage (Flat ₹20 per trade or capped percentage)
- STT (Securities Transaction Tax)
- Exchange Turnover Fees
- SEBI Charges
- GST (18% on Brokerage + Exchange fees)
- Stamp Duty
- Basis-point / Rupee Slippage
"""

from dataclasses import dataclass
from enum import Enum


class SlippageType(str, Enum):
    ZERO = "ZERO"
    FIXED_RUPEE = "FIXED_RUPEE"
    PERCENTAGE = "PERCENTAGE"


@dataclass
class CostModelConfig:
    brokerage_per_order: float = 20.0  # Flat ₹20 per order
    brokerage_percent_cap: float = 0.0003  # 0.03% cap
    stt_sell_percent: float = 0.00025  # 0.025% STT on intraday sell side
    exchange_charge_percent: float = 0.0000345  # NSE exchange fee 0.00345%
    sebi_charge_percent: float = 0.000001  # SEBI ₹10 per crore (0.0001%)
    gst_percent: float = 0.18  # 18% GST on brokerage & exchange fees
    stamp_duty_buy_percent: float = 0.00003  # 0.003% Stamp duty on buy side
    slippage_type: SlippageType = SlippageType.PERCENTAGE
    slippage_value: float = 0.0005  # 5 bps slippage (0.05%)


@dataclass
class TransactionCostBreakdown:
    brokerage: float
    stt: float
    exchange_charges: float
    sebi_charges: float
    gst: float
    stamp_duty: float
    slippage_cost: float
    total_cost: float
    executed_price_with_slippage: float


class IndianTransactionCostCalculator:
    """Calculates comprehensive transaction costs for an Indian market trade execution."""

    @classmethod
    def calculate_cost(
        cls,
        side: str,  # "BUY" or "SELL"
        quantity: float,
        price: float,
        config: CostModelConfig = CostModelConfig()
    ) -> TransactionCostBreakdown:
        turnover = quantity * price
        side_upper = side.upper()

        # 1. Brokerage calculation (Flat ₹20 or capped percent)
        capped_brokerage = turnover * config.brokerage_percent_cap
        brokerage = min(config.brokerage_per_order, capped_brokerage)

        # 2. STT (Applied on sell side for intraday trading)
        stt = (turnover * config.stt_sell_percent) if side_upper == "SELL" else 0.0

        # 3. Exchange Turnover Charge
        exchange_charges = turnover * config.exchange_charge_percent

        # 4. SEBI Charges
        sebi_charges = turnover * config.sebi_charge_percent

        # 5. GST (18% on Brokerage + Exchange fees)
        gst = (brokerage + exchange_charges) * config.gst_percent

        # 6. Stamp Duty (Applied on buy side)
        stamp_duty = (turnover * config.stamp_duty_buy_percent) if side_upper == "BUY" else 0.0

        # 7. Slippage Calculation
        if config.slippage_type == SlippageType.FIXED_RUPEE:
            price_offset = config.slippage_value
        elif config.slippage_type == SlippageType.PERCENTAGE:
            price_offset = price * config.slippage_value
        else:
            price_offset = 0.0

        # Buyer pays higher price due to slippage, seller receives lower price
        if side_upper == "BUY":
            executed_price = price + price_offset
        else:
            executed_price = max(0.0, price - price_offset)

        slippage_cost = abs(executed_price - price) * quantity
        statutory_taxes = brokerage + stt + exchange_charges + sebi_charges + gst + stamp_duty
        total_cost = statutory_taxes + slippage_cost

        return TransactionCostBreakdown(
            brokerage=round(brokerage, 2),
            stt=round(stt, 2),
            exchange_charges=round(exchange_charges, 2),
            sebi_charges=round(sebi_charges, 2),
            gst=round(gst, 2),
            stamp_duty=round(stamp_duty, 2),
            slippage_cost=round(slippage_cost, 2),
            total_cost=round(total_cost, 2),
            executed_price_with_slippage=round(executed_price, 2)
        )
