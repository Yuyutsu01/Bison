"""
Modular Transaction Fee & Tax Calculators.

Provides discrete calculation components for:
- Turnover
- Brokerage (Flat, Percentage, Percentage with Cap)
- STT / CTT
- Exchange Charges
- SEBI Fees
- Stamp Duty
- GST (18% on Taxable Base)
- Financial Rounding Policy
"""

from decimal import Decimal, ROUND_HALF_UP


class FinancialRoundingPolicy:
    """Centralized rounding policy for INR currency values."""

    @staticmethod
    def round_currency(value: Decimal) -> Decimal:
        """Rounds Decimal currency to 2 decimal places using ROUND_HALF_UP."""
        if not isinstance(value, Decimal):
            value = Decimal(str(value))
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class TurnoverCalculator:
    """Calculates gross transaction turnover."""

    @staticmethod
    def calculate_turnover(price: Decimal, quantity: Decimal) -> Decimal:
        if not isinstance(price, Decimal):
            price = Decimal(str(price))
        if not isinstance(quantity, Decimal):
            quantity = Decimal(str(quantity))
        return price * quantity


class BrokerageCalculator:
    """Calculates brokerage fee according to configured BrokerageModel."""

    @staticmethod
    def calculate_brokerage(
        turnover: Decimal,
        model_name: str,
        rate: Decimal,
        cap: Decimal,
        flat: Decimal
    ) -> Decimal:
        """
        Calculates brokerage fee.

        Models:
        - FLAT_PER_ORDER: flat fee per order.
        - PERCENTAGE: turnover * rate.
        - PERCENTAGE_WITH_CAP: min(turnover * rate, cap).
        """
        if model_name == "FLAT_PER_ORDER":
            return flat
        elif model_name == "PERCENTAGE":
            return turnover * rate
        else:  # PERCENTAGE_WITH_CAP
            raw_bkr = turnover * rate
            return min(raw_bkr, cap)


class StatutoryTaxCalculator:
    """Calculates STT/CTT statutory tax."""

    @staticmethod
    def calculate_stt(
        turnover: Decimal,
        side: str,
        buy_rate: Decimal,
        sell_rate: Decimal
    ) -> Decimal:
        """
        Calculates STT/CTT tax based on transaction side.

        Important Logic:
        - BUY side applies buy_rate.
        - SELL side applies sell_rate (e.g. 0.025% on intraday equity sell side).
        """
        is_buy = side in ("BUY", "LONG_ENTRY")
        rate = buy_rate if is_buy else sell_rate
        return turnover * rate


class ExchangeChargeCalculator:
    """Calculates Exchange Turnover Charges."""

    @staticmethod
    def calculate_exchange_charges(turnover: Decimal, rate: Decimal) -> Decimal:
        return turnover * rate


class SEBIFeeCalculator:
    """Calculates SEBI Regulatory Fee."""

    @staticmethod
    def calculate_sebi_fee(turnover: Decimal, rate: Decimal) -> Decimal:
        return turnover * rate


class StampDutyCalculator:
    """Calculates Stamp Duty."""

    @staticmethod
    def calculate_stamp_duty(turnover: Decimal, side: str, rate: Decimal) -> Decimal:
        """
        Calculates Stamp Duty.

        Important Logic:
        - Applied strictly to BUY side transactions in Indian markets.
        - SELL side returns zero stamp duty.
        """
        is_buy = side in ("BUY", "LONG_ENTRY")
        if not is_buy:
            return Decimal("0.0")
        return turnover * rate


class GSTCalculator:
    """Calculates Goods & Services Tax (GST)."""

    @staticmethod
    def calculate_gst(taxable_base: Decimal, gst_rate: Decimal) -> Decimal:
        """
        Calculates 18% GST.

        Important Logic:
        - Taxable Base = Brokerage + Exchange Charges + SEBI Fees.
        - Explicitly excludes STT and Stamp Duty from the taxable base.
        """
        if taxable_base <= Decimal("0.0"):
            return Decimal("0.0")
        return taxable_base * gst_rate
