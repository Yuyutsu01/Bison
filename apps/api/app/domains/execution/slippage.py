"""
Slippage Models for Order Execution Simulation.

Supports Zero, Fixed Points, and Percentage slippage models with exact Decimal arithmetic.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from app.domains.orders.models import OrderSide


class SlippageModel(ABC):
    """Abstract interface for execution slippage calculations."""

    @abstractmethod
    def calculate_slippage(self, reference_price: Decimal, side: OrderSide) -> Decimal:
        """
        Calculates price impact slippage.

        Returns:
            Decimal: Positive slippage amount to add (BUY) or subtract (SELL).
        """
        pass


class ZeroSlippage(SlippageModel):
    """Zero slippage model."""

    def calculate_slippage(self, reference_price: Decimal, side: OrderSide) -> Decimal:
        return Decimal("0.0")


class FixedPointsSlippage(SlippageModel):
    """
    Fixed points slippage model (e.g. 2.0 points).

    BUY execution price = reference_price + points
    SELL execution price = reference_price - points
    """

    def __init__(self, points: Decimal = Decimal("0.0")):
        if not isinstance(points, Decimal):
            points = Decimal(str(points))
        if points < Decimal("0"):
            raise ValueError("Slippage points cannot be negative.")
        self.points = points

    def calculate_slippage(self, reference_price: Decimal, side: OrderSide) -> Decimal:
        return self.points


class PercentageSlippage(SlippageModel):
    """
    Percentage slippage model (e.g. 0.05% = 0.0005).

    BUY execution price = reference_price * (1 + pct)
    SELL execution price = reference_price * (1 - pct)
    """

    def __init__(self, percentage: Decimal = Decimal("0.0")):
        if not isinstance(percentage, Decimal):
            percentage = Decimal(str(percentage))
        if percentage < Decimal("0"):
            raise ValueError("Slippage percentage cannot be negative.")
        # If percentage passed as percentage (e.g., 0.05%), convert if > 1 or keep as fraction
        self.percentage = percentage

    def calculate_slippage(self, reference_price: Decimal, side: OrderSide) -> Decimal:
        if not isinstance(reference_price, Decimal):
            reference_price = Decimal(str(reference_price))
        return reference_price * self.percentage
