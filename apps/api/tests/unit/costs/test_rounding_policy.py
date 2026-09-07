"""
Unit tests for FinancialRoundingPolicy.
"""

from decimal import Decimal
from app.domains.costs.calculators import FinancialRoundingPolicy


def test_rounding_policy_half_up():
    """ROUND_HALF_UP rounds half to even up to the nearest cent (2 decimal places)."""
    val_round_up = Decimal("12.345")
    val_round_down = Decimal("12.344")
    val_exact = Decimal("12.340")

    assert FinancialRoundingPolicy.round_currency(val_round_up) == Decimal("12.35")
    assert FinancialRoundingPolicy.round_currency(val_round_down) == Decimal("12.34")
    assert FinancialRoundingPolicy.round_currency(val_exact) == Decimal("12.34")


def test_rounding_policy_prevents_float_drift():
    """Decimal rounding prevents typical float precision issues like 0.0000000000000001."""
    val = Decimal("0.1") + Decimal("0.2")
    rounded = FinancialRoundingPolicy.round_currency(val)
    assert rounded == Decimal("0.30")
