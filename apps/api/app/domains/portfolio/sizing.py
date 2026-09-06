"""
Position Sizing Engine.

Calculates order quantities based on strategy configuration:
- FIXED_QUANTITY
- FIXED_CAPITAL
- PERCENT_OF_CAPITAL

Enforces lot size multiples and capital sufficiency checks.
"""

from decimal import Decimal, ROUND_FLOOR, InvalidOperation
from typing import Optional

from app.domains.strategies.schemas import PositionSizing, PositionSizingType
from app.domains.orders.models import OrderValidationError


class PositionSizingEngine:
    """Calculates position quantities from account state and strategy rules."""

    @staticmethod
    def calculate_quantity(
        position_sizing: PositionSizing,
        available_cash: Decimal,
        reference_price: Decimal,
        lot_size: Decimal = Decimal("1")
    ) -> Decimal:
        """
        Calculates trade quantity based on position sizing policy and available cash.

        Important Logic:
        - FIXED_QUANTITY: uses sizing.value directly.
        - FIXED_CAPITAL: quantity = floor(sizing.value / reference_price).
        - PERCENT_OF_CAPITAL: quantity = floor((available_cash * (sizing.value / 100)) / reference_price).
        - Enforces integer multiples of lot_size.
        - Validates that quantity > 0 and capital is sufficient.
        """
        if not isinstance(available_cash, Decimal):
            available_cash = Decimal(str(available_cash))
        if not isinstance(reference_price, Decimal):
            reference_price = Decimal(str(reference_price))
        if not isinstance(lot_size, Decimal):
            lot_size = Decimal(str(lot_size))

        if reference_price <= Decimal("0"):
            raise OrderValidationError("Reference price must be positive for position sizing.")

        if position_sizing.type == PositionSizingType.FIXED_QUANTITY:
            raw_qty = Decimal(str(position_sizing.value))
        elif position_sizing.type == PositionSizingType.PERCENT_OF_CAPITAL:
            allocated_cash = available_cash * (Decimal(str(position_sizing.value)) / Decimal("100.0"))
            if allocated_cash <= Decimal("0"):
                raise OrderValidationError("Insufficient available cash for percentage capital allocation.")
            raw_qty = (allocated_cash / reference_price).quantize(Decimal("1"), rounding=ROUND_FLOOR)
        else:  # FIXED_CAPITAL / FIXED_AMOUNT
            allocated_cash = Decimal(str(position_sizing.value))
            raw_qty = (allocated_cash / reference_price).quantize(Decimal("1"), rounding=ROUND_FLOOR)

        # Normalize to lot_size multiple
        if lot_size > Decimal("1"):
            raw_qty = (raw_qty // lot_size) * lot_size
            if raw_qty < lot_size:
                raw_qty = lot_size

        if raw_qty <= Decimal("0"):
            raise OrderValidationError("Calculated position size is zero or negative.")

        required_capital = raw_qty * reference_price
        if required_capital > available_cash and position_sizing.type != PositionSizingType.FIXED_QUANTITY:
            raise OrderValidationError(
                f"Required capital {required_capital} exceeds available cash {available_cash}."
            )

        return raw_qty
