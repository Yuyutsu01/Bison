"""
Unit Tests for Position Sizing Engine.
"""

import pytest
from decimal import Decimal
from app.domains.strategies.schemas import PositionSizing, PositionSizingType
from app.domains.portfolio.sizing import PositionSizingEngine
from app.domains.orders.models import OrderValidationError


def test_fixed_quantity_sizing():
    sizing = PositionSizing(type=PositionSizingType.FIXED_QUANTITY, value=50.0)
    qty = PositionSizingEngine.calculate_quantity(
        position_sizing=sizing,
        available_cash=Decimal("100000.0"),
        reference_price=Decimal("24000.0"),
        lot_size=Decimal("25")
    )
    assert qty == Decimal("50")


def test_percent_of_capital_sizing():
    sizing = PositionSizing(type=PositionSizingType.PERCENT_OF_CAPITAL, value=20.0)  # 20% of 100,000 = 20,000
    qty = PositionSizingEngine.calculate_quantity(
        position_sizing=sizing,
        available_cash=Decimal("100000.0"),
        reference_price=Decimal("400.0"),  # 20,000 / 400 = 50 shares
        lot_size=Decimal("1")
    )
    assert qty == Decimal("50")


def test_lot_size_normalization():
    sizing = PositionSizing(type=PositionSizingType.PERCENT_OF_CAPITAL, value=25.0)  # 25,000 allocated
    qty = PositionSizingEngine.calculate_quantity(
        position_sizing=sizing,
        available_cash=Decimal("100000.0"),
        reference_price=Decimal("400.0"),  # 25,000 / 400 = 62 shares -> rounded down to 50 (lot size 25)
        lot_size=Decimal("25")
    )
    assert qty == Decimal("50")


def test_insufficient_capital_error():
    sizing = PositionSizing(type=PositionSizingType.PERCENT_OF_CAPITAL, value=150.0)
    with pytest.raises(OrderValidationError):
        PositionSizingEngine.calculate_quantity(
            position_sizing=sizing,
            available_cash=Decimal("1000.0"),
            reference_price=Decimal("5000.0")
        )
