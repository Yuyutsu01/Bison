"""
Unit tests for Brokerage Calculator.

Tests percentage with cap model (e.g. 0.03% capped at ₹20), flat model, and percentage model.
"""

from decimal import Decimal
import pytest
from app.domains.costs.models import BrokerageModel
from app.domains.costs.calculators import BrokerageCalculator


def test_brokerage_percentage_with_cap_under_cap():
    """Turnover of ₹10,000 at 0.03% = ₹3.00, which is < cap of ₹20."""
    turnover = Decimal("10000.00")
    brokerage = BrokerageCalculator.calculate_brokerage(
        turnover=turnover,
        model_name=BrokerageModel.PERCENTAGE_WITH_CAP,
        rate=Decimal("0.0003"),
        cap=Decimal("20.00"),
        flat=Decimal("20.00")
    )
    assert brokerage == Decimal("3.00")


def test_brokerage_percentage_with_cap_exceeding_cap():
    """Turnover of ₹1,000,000 at 0.03% = ₹300.00, which exceeds cap of ₹20. Should cap at ₹20.00."""
    turnover = Decimal("1000000.00")
    brokerage = BrokerageCalculator.calculate_brokerage(
        turnover=turnover,
        model_name=BrokerageModel.PERCENTAGE_WITH_CAP,
        rate=Decimal("0.0003"),
        cap=Decimal("20.00"),
        flat=Decimal("20.00")
    )
    assert brokerage == Decimal("20.00")


def test_brokerage_flat_rate():
    """Flat rate model should always return the flat amount regardless of turnover."""
    turnover = Decimal("500000.00")
    brokerage = BrokerageCalculator.calculate_brokerage(
        turnover=turnover,
        model_name=BrokerageModel.FLAT_PER_ORDER,
        rate=Decimal("0.0003"),
        cap=Decimal("20.00"),
        flat=Decimal("15.00")
    )
    assert brokerage == Decimal("15.00")


def test_brokerage_percentage_only():
    """Percentage model without cap."""
    turnover = Decimal("100000.00")
    brokerage = BrokerageCalculator.calculate_brokerage(
        turnover=turnover,
        model_name=BrokerageModel.PERCENTAGE,
        rate=Decimal("0.0005"),
        cap=Decimal("20.00"),
        flat=Decimal("20.00")
    )
    assert brokerage == Decimal("50.00")
