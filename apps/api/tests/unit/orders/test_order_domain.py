"""
Unit Tests for Order Domain Models, State Machine, and OrderFactory.
"""

import pytest
from decimal import Decimal
from app.domains.signals.models import Signal, SignalType
from app.domains.orders.models import (
    Order, OrderSide, OrderType, OrderStatus,
    InvalidStateTransitionError, OrderValidationError
)
from app.domains.orders.factory import OrderFactory


def test_order_creation_and_defaults():
    order = Order(
        id="ORD_001",
        strategy_id="STRAT_1",
        strategy_version_id="VER_1",
        signal_id="SIG_001",
        instrument_id="NIFTY",
        symbol="NIFTY",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("50"),
        created_at="2026-01-01T10:05:00",
        eligible_at="2026-01-01T10:10:00"
    )
    assert order.status == OrderStatus.CREATED
    assert order.execution_policy == "NEXT_BAR_OPEN"
    assert len(order.idempotency_key) > 0


def test_state_machine_legal_transitions():
    order = Order(
        id="ORD_002",
        strategy_id="STRAT_1",
        strategy_version_id="VER_1",
        signal_id="SIG_002",
        instrument_id="NIFTY",
        symbol="NIFTY",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("50"),
        created_at="10:05",
        eligible_at="10:10"
    )
    # CREATED -> PENDING
    order.transition_to(OrderStatus.PENDING)
    assert order.status == OrderStatus.PENDING

    # PENDING -> FILLED
    order.transition_to(OrderStatus.FILLED)
    assert order.status == OrderStatus.FILLED


def test_state_machine_illegal_transitions():
    order = Order(
        id="ORD_003",
        strategy_id="STRAT_1",
        strategy_version_id="VER_1",
        signal_id="SIG_003",
        instrument_id="NIFTY",
        symbol="NIFTY",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("50"),
        created_at="10:05",
        eligible_at="10:10",
        status=OrderStatus.FILLED
    )
    # Terminal state FILLED -> PENDING is illegal
    with pytest.raises(InvalidStateTransitionError):
        order.transition_to(OrderStatus.PENDING)


def test_order_factory_valid_signal_conversion():
    signal = Signal(
        signal_id="SIG_100",
        timestamp="2026-01-01T10:05:00",
        symbol="NIFTY",
        signal_type=SignalType.BUY,
        bar_index=5,
        trigger_price=24100.0,
        reason="EMA_CROSSOVER"
    )
    order = OrderFactory.create_order_from_signal(
        signal=signal,
        strategy_id="STRAT_1",
        strategy_version_id="VER_1",
        quantity=Decimal("50"),
        eligible_at_timestamp="2026-01-01T10:10:00",
        instrument_id="NIFTY",
        lot_size=Decimal("25")
    )
    assert order.symbol == "NIFTY"
    assert order.side == OrderSide.BUY
    assert order.quantity == Decimal("50")
    assert order.eligible_at == "2026-01-01T10:10:00"
    assert order.status == OrderStatus.CREATED


def test_order_factory_invalid_quantity_and_lot_size():
    signal = Signal(
        signal_id="SIG_101",
        timestamp="10:05",
        symbol="NIFTY",
        signal_type=SignalType.BUY,
        bar_index=1,
        trigger_price=24100.0,
        reason="BUY_SIGNAL"
    )
    # Negative quantity raises validation error
    with pytest.raises(OrderValidationError):
        OrderFactory.create_order_from_signal(
            signal=signal,
            strategy_id="S1",
            strategy_version_id="V1",
            quantity=Decimal("-10"),
            eligible_at_timestamp="10:10"
        )

    # Quantity non-multiple of lot size raises validation error
    with pytest.raises(OrderValidationError):
        OrderFactory.create_order_from_signal(
            signal=signal,
            strategy_id="S1",
            strategy_version_id="V1",
            quantity=Decimal("37"),
            eligible_at_timestamp="10:10",
            lot_size=Decimal("25")
        )
