"""
Unit Tests for Slippage Models and Tick Size Normalization.
"""

import pytest
from decimal import Decimal
from app.domains.orders.models import OrderSide
from app.domains.execution.slippage import ZeroSlippage, FixedPointsSlippage, PercentageSlippage
from app.domains.execution.pricing import normalize_to_tick_size


def test_tick_size_normalization():
    tick_size = Decimal("0.05")
    # 24120.03 -> 24120.05
    assert normalize_to_tick_size(Decimal("24120.03"), tick_size) == Decimal("24120.05")
    # 24120.02 -> 24120.00
    assert normalize_to_tick_size(Decimal("24120.02"), tick_size) == Decimal("24120.00")
    # Exact tick 24120.10
    assert normalize_to_tick_size(Decimal("24120.10"), tick_size) == Decimal("24120.10")


def test_zero_slippage_model():
    model = ZeroSlippage()
    price = Decimal("24120.00")
    assert model.calculate_slippage(price, OrderSide.BUY) == Decimal("0.0")
    assert model.calculate_slippage(price, OrderSide.SELL) == Decimal("0.0")


def test_fixed_points_slippage_model():
    model = FixedPointsSlippage(Decimal("2.5"))
    price = Decimal("24120.00")
    assert model.calculate_slippage(price, OrderSide.BUY) == Decimal("2.5")
    assert model.calculate_slippage(price, OrderSide.SELL) == Decimal("2.5")


def test_percentage_slippage_model():
    model = PercentageSlippage(Decimal("0.001"))  # 0.1%
    price = Decimal("20000.00")
    assert model.calculate_slippage(price, OrderSide.BUY) == Decimal("20.00")
