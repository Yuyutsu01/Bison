"""
Order Factory for Signal to Order Mapping.

Converts strategy Signals into validated Order entities.
Enforces lot size rules, quantity checks, and deterministic timestamp calculation.
"""

import uuid
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, Any

from app.domains.signals.models import Signal, SignalType
from app.domains.orders.models import (
    Order,
    OrderSide,
    OrderType,
    OrderStatus,
    OrderValidationError
)


class OrderFactory:
    """Factory service creating Order objects from Signal events."""

    @staticmethod
    def create_order_from_signal(
        signal: Signal,
        strategy_id: str,
        strategy_version_id: str,
        quantity: Decimal,
        eligible_at_timestamp: str,
        instrument_id: str = "DEFAULT",
        lot_size: Decimal = Decimal("1"),
        execution_policy: str = "NEXT_BAR_OPEN",
        order_type: OrderType = OrderType.MARKET,
        requested_price: Optional[Decimal] = None
    ) -> Order:
        """
        Constructs and validates an Order from a Signal event.

        Important Logic:
        - Validates that quantity is positive (> 0).
        - Validates lot size divisibility (quantity % lot_size == 0).
        - Maps SignalType (BUY, SELL, EXIT) to corresponding OrderSide.
        - Generates deterministic idempotency key for duplicate signal protection.
        """
        # Validate quantity
        if not isinstance(quantity, Decimal):
            try:
                quantity = Decimal(str(quantity))
            except (InvalidOperation, TypeError):
                raise OrderValidationError(f"Invalid quantity value: {quantity}")

        if quantity <= Decimal("0"):
            raise OrderValidationError(f"Order quantity must be positive. Received: {quantity}")

        if not isinstance(lot_size, Decimal):
            lot_size = Decimal(str(lot_size))

        if lot_size > Decimal("0"):
            if quantity % lot_size != Decimal("0"):
                raise OrderValidationError(
                    f"Quantity {quantity} is not a valid multiple of instrument lot size {lot_size}."
                )

        # Map SignalType to OrderSide
        if signal.signal_type == SignalType.BUY:
            side = OrderSide.BUY
        elif signal.signal_type == SignalType.SELL:
            side = OrderSide.SELL
        elif signal.signal_type == SignalType.EXIT:
            # Map EXIT to SELL if position context is long; default to SELL for exit
            side = OrderSide.SELL
        else:
            raise OrderValidationError(f"Unknown signal type: {signal.signal_type}")

        order_id = f"ORD_{uuid.uuid4().hex[:12]}"
        idempotency_key = Order.generate_idempotency_key(
            strategy_version_id=strategy_version_id,
            signal_timestamp=signal.timestamp,
            symbol=signal.symbol,
            side=side.value
        )

        return Order(
            id=order_id,
            strategy_id=strategy_id,
            strategy_version_id=strategy_version_id,
            signal_id=signal.signal_id,
            instrument_id=instrument_id,
            symbol=signal.symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            created_at=signal.timestamp,
            eligible_at=eligible_at_timestamp,
            status=OrderStatus.CREATED,
            requested_price=requested_price,
            execution_policy=execution_policy,
            idempotency_key=idempotency_key,
            metadata={
                "signal_reason": signal.reason,
                "trigger_price": signal.trigger_price,
                "bar_index": signal.bar_index
            }
        )
