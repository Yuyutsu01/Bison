"""
Order Execution Simulator Engine.

Simulates order execution deterministically against market price bars.
Enforces NEXT_BAR_OPEN policy, slippage models, tick size normalization,
order lifecycle state machine, and idempotency protection.
"""

import uuid
from decimal import Decimal
from typing import Optional, Dict, Any, Union

from app.domains.orders.models import (
    Order,
    OrderStatus,
    OrderType,
    UnsupportedOrderTypeError
)
from app.domains.execution.models import (
    Execution,
    ExecutionPolicy,
    ExecutionStatus
)
from app.domains.execution.slippage import SlippageModel, ZeroSlippage
from app.domains.execution.pricing import normalize_to_tick_size


class ExecutionSimulator:
    """Pure domain component for deterministic simulated execution."""

    def __init__(self, slippage_model: Optional[SlippageModel] = None):
        self.slippage_model = slippage_model or ZeroSlippage()
        self._execution_cache: Dict[str, Execution] = {}

    def simulate_execution(
        self,
        order: Order,
        bar: Optional[Dict[str, Any]] = None,
        tick_size: Decimal = Decimal("0.05")
    ) -> Optional[Execution]:
        """
        Simulates order execution against an incoming market price bar.

        Important Logic:
        1. Idempotency Protection: If order is already FILLED, returns cached execution without re-filling.
        2. Status Transition Checks: Rejects invalid or terminal states.
        3. Missing Next Bar Handling: If bar is None, transitions order to EXPIRED.
        4. Order Type Verification: Rejects unsupported order types (e.g., LIMIT, STOP).
        5. Execution Policy: Executes at bar Open under NEXT_BAR_OPEN.
        6. Slippage & Tick Rounding: Applies slippage model and normalizes to tick_size.
        """
        # 1. Idempotency Check: Return existing execution if order was already executed
        if order.idempotency_key in self._execution_cache:
            return self._execution_cache[order.idempotency_key]

        if order.status == OrderStatus.FILLED:
            # If already filled, fetch cached execution or return None
            return self._execution_cache.get(order.idempotency_key)

        if order.status in (OrderStatus.CANCELLED, OrderStatus.REJECTED, OrderStatus.EXPIRED):
            return None

        # 2. Missing Next Bar handling (signal on last candle)
        if bar is None:
            order.transition_to(OrderStatus.EXPIRED, reason="NO_NEXT_BAR_AVAILABLE")
            return None

        # 3. Order Type Verification
        if order.order_type != OrderType.MARKET:
            order.transition_to(OrderStatus.REJECTED, reason="UNSUPPORTED_ORDER_TYPE")
            raise UnsupportedOrderTypeError(
                f"Execution policy does not support order type '{order.order_type.value}' yet."
            )

        # 4. Transition CREATED -> PENDING
        if order.status == OrderStatus.CREATED:
            order.transition_to(OrderStatus.PENDING)

        # 5. Extract Reference Price from Bar Open
        bar_open_raw = bar.get("open")
        if bar_open_raw is None:
            order.transition_to(OrderStatus.REJECTED, reason="INVALID_PRICE_BAR")
            return None

        reference_price = Decimal(str(bar_open_raw))
        bar_timestamp = str(bar.get("timestamp", order.eligible_at))

        # 6. Calculate Slippage
        slippage_delta = self.slippage_model.calculate_slippage(reference_price, order.side)

        # 7. Apply Slippage directionally based on order side
        if order.side.is_buy_side:
            # BUY side receives a worse (higher) execution price
            raw_execution_price = reference_price + slippage_delta
        else:
            # SELL side receives a worse (lower) execution price
            raw_execution_price = reference_price - slippage_delta

        # 8. Tick Size Normalization
        execution_price = normalize_to_tick_size(raw_execution_price, tick_size)
        actual_slippage = abs(execution_price - reference_price)

        # 9. Transition Order state to FILLED
        order.transition_to(OrderStatus.FILLED)

        execution_id = f"EXEC_{uuid.uuid4().hex[:12]}"
        execution = Execution(
            id=execution_id,
            order_id=order.id,
            instrument_id=order.instrument_id,
            symbol=order.symbol,
            timestamp=bar_timestamp,
            side=order.side.value,
            quantity=order.quantity,
            reference_price=reference_price,
            execution_price=execution_price,
            slippage=actual_slippage,
            status=ExecutionStatus.SUCCESS,
            metadata={
                "execution_policy": ExecutionPolicy.NEXT_BAR_OPEN.value,
                "tick_size": str(tick_size),
                "idempotency_key": order.idempotency_key
            }
        )

        # Cache execution for idempotency lookup
        self._execution_cache[order.idempotency_key] = execution
        return execution
