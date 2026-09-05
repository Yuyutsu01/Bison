"""
Unit Tests for Execution Simulator Engine.
"""

import pytest
from decimal import Decimal
from app.domains.orders.models import (
    Order, OrderSide, OrderType, OrderStatus, UnsupportedOrderTypeError
)
from app.domains.execution.models import ExecutionStatus
from app.domains.execution.slippage import FixedPointsSlippage, ZeroSlippage
from app.domains.execution.simulator import ExecutionSimulator


def test_next_bar_open_execution_buy():
    order = Order(
        id="ORD_BUY_1",
        strategy_id="S1",
        strategy_version_id="V1",
        signal_id="SIG_1",
        instrument_id="NIFTY",
        symbol="NIFTY",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("50"),
        created_at="10:05",
        eligible_at="10:10"
    )
    simulator = ExecutionSimulator(slippage_model=FixedPointsSlippage(Decimal("2.0")))
    bar = {"open": 24120.0, "high": 24150.0, "low": 24100.0, "close": 24140.0, "timestamp": "10:10"}

    exec_record = simulator.simulate_execution(order, bar=bar, tick_size=Decimal("0.05"))

    assert exec_record is not None
    assert exec_record.reference_price == Decimal("24120.0")
    # BUY execution price = 24120.0 + 2.0 = 24122.0
    assert exec_record.execution_price == Decimal("24122.0")
    assert exec_record.status == ExecutionStatus.SUCCESS
    assert order.status == OrderStatus.FILLED


def test_next_bar_open_execution_sell():
    order = Order(
        id="ORD_SELL_1",
        strategy_id="S1",
        strategy_version_id="V1",
        signal_id="SIG_2",
        instrument_id="NIFTY",
        symbol="NIFTY",
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        quantity=Decimal("50"),
        created_at="10:05",
        eligible_at="10:10"
    )
    simulator = ExecutionSimulator(slippage_model=FixedPointsSlippage(Decimal("2.0")))
    bar = {"open": 24120.0, "high": 24150.0, "low": 24100.0, "close": 24140.0, "timestamp": "10:10"}

    exec_record = simulator.simulate_execution(order, bar=bar, tick_size=Decimal("0.05"))

    assert exec_record is not None
    # SELL execution price = 24120.0 - 2.0 = 24118.0
    assert exec_record.execution_price == Decimal("24118.0")
    assert order.status == OrderStatus.FILLED


def test_missing_next_bar_transitions_order_to_expired():
    order = Order(
        id="ORD_EXP_1",
        strategy_id="S1",
        strategy_version_id="V1",
        signal_id="SIG_LAST",
        instrument_id="NIFTY",
        symbol="NIFTY",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("50"),
        created_at="15:25",
        eligible_at="15:30"
    )
    simulator = ExecutionSimulator()

    # Pass bar = None simulating missing next candle
    exec_record = simulator.simulate_execution(order, bar=None)

    assert exec_record is None
    assert order.status == OrderStatus.EXPIRED
    assert order.rejection_reason == "NO_NEXT_BAR_AVAILABLE"


def test_idempotent_execution_does_not_duplicate_fill():
    order = Order(
        id="ORD_IDEM_1",
        strategy_id="S1",
        strategy_version_id="V1",
        signal_id="SIG_IDEM",
        instrument_id="NIFTY",
        symbol="NIFTY",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("50"),
        created_at="10:05",
        eligible_at="10:10"
    )
    simulator = ExecutionSimulator(slippage_model=ZeroSlippage())
    bar = {"open": 24120.0, "timestamp": "10:10"}

    first_exec = simulator.simulate_execution(order, bar=bar)
    second_exec = simulator.simulate_execution(order, bar=bar)

    assert first_exec is not None
    assert second_exec is not None
    # Must be identical execution reference without creating a second fill
    assert first_exec.id == second_exec.id
