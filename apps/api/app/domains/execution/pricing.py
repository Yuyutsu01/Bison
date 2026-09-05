"""
Financial Pricing & Tick Size Utilities.

Provides exact Decimal rounding to tick size boundaries (e.g. 0.05 for NSE).
"""

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


def normalize_to_tick_size(price: Decimal, tick_size: Decimal) -> Decimal:
    """
    Normalizes execution price to nearest valid tick size step.

    Examples:
    - price = 24120.03, tick_size = 0.05 -> 24120.05
    - price = 24120.02, tick_size = 0.05 -> 24120.00
    - price = 24122.14, tick_size = 0.05 -> 24122.15

    Important Logic:
    - Avoids floating point binary inaccuracies by converting floats or strings to Decimal.
    - Uses ROUND_HALF_UP for deterministic financial tick rounding.
    """
    if not isinstance(price, Decimal):
        price = Decimal(str(price))
    if not isinstance(tick_size, Decimal):
        tick_size = Decimal(str(tick_size))

    if tick_size <= Decimal("0"):
        return price

    # Number of ticks = price / tick_size
    ticks = (price / tick_size).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return ticks * tick_size
