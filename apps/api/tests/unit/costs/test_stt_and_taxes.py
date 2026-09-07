"""
Unit tests for STT, Exchange Charges, SEBI Fees, Stamp Duty, and GST Calculators.
"""

from decimal import Decimal
import pytest
from app.domains.costs.calculators import (
    StatutoryTaxCalculator, ExchangeChargeCalculator, SEBIFeeCalculator,
    StampDutyCalculator, GSTCalculator
)


def test_stt_equity_intraday_buy_side():
    """Equity intraday buy side has 0% STT rate."""
    turnover = Decimal("100000.00")
    stt = StatutoryTaxCalculator.calculate_stt(
        turnover=turnover,
        side="BUY",
        buy_rate=Decimal("0.00"),
        sell_rate=Decimal("0.00025")
    )
    assert stt == Decimal("0.00")


def test_stt_equity_intraday_sell_side():
    """Equity intraday sell side has 0.025% STT rate. ₹100,000 * 0.00025 = ₹25.00."""
    turnover = Decimal("100000.00")
    stt = StatutoryTaxCalculator.calculate_stt(
        turnover=turnover,
        side="SELL",
        buy_rate=Decimal("0.00"),
        sell_rate=Decimal("0.00025")
    )
    assert stt == Decimal("25.00")


def test_exchange_charges():
    """NSE Exchange charge rate of 0.00345% on ₹100,000 turnover = ₹3.45."""
    turnover = Decimal("100000.00")
    ex_charge = ExchangeChargeCalculator.calculate_exchange_charges(
        turnover=turnover,
        rate=Decimal("0.0000345")
    )
    assert ex_charge == Decimal("3.45")


def test_sebi_fees():
    """SEBI fee rate of ₹10 per crore (0.0001%) on ₹1,000,000 turnover = ₹1.00."""
    turnover = Decimal("1000000.00")
    sebi_fee = SEBIFeeCalculator.calculate_sebi_fee(
        turnover=turnover,
        rate=Decimal("0.000001")
    )
    assert sebi_fee == Decimal("1.00")


def test_stamp_duty_buy_side():
    """Stamp duty of 0.003% on BUY side ₹100,000 turnover = ₹3.00."""
    turnover = Decimal("100000.00")
    stamp_duty = StampDutyCalculator.calculate_stamp_duty(
        turnover=turnover,
        side="BUY",
        rate=Decimal("0.00003")
    )
    assert stamp_duty == Decimal("3.00")


def test_stamp_duty_sell_side():
    """Stamp duty on SELL side is 0 (buyers pay stamp duty in Indian markets)."""
    turnover = Decimal("100000.00")
    stamp_duty = StampDutyCalculator.calculate_stamp_duty(
        turnover=turnover,
        side="SELL",
        rate=Decimal("0.00003")
    )
    assert stamp_duty == Decimal("0.00")


def test_gst_calculation_base():
    """GST 18% must apply strictly to (Brokerage + Exchange Fees + SEBI Fees).

    Example:
      Brokerage = ₹20.00
      Exchange Fees = ₹3.45
      SEBI Fees = ₹0.10
      Taxable Base = ₹23.55
      GST 18% = ₹23.55 * 0.18 = ₹4.239
    """
    brokerage = Decimal("20.00")
    exchange_charges = Decimal("3.45")
    sebi_fees = Decimal("0.10")
    taxable_base = brokerage + exchange_charges + sebi_fees
    gst_rate = Decimal("0.18")

    gst = GSTCalculator.calculate_gst(
        taxable_base=taxable_base,
        gst_rate=gst_rate
    )
    assert gst == Decimal("4.239")
