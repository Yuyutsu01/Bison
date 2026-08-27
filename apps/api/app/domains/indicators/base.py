"""
Abstract Indicator Base Class & Interface.

Defines standard interface for technical indicators including parameter validation,
warm-up periods, batch vectorized calculations, and single-bar streaming calculations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Union
import pandas as pd


class BaseIndicator(ABC):
    """Abstract base class for all technical quantitative indicators."""

    def __init__(self, parameters: Dict[str, Any]):
        self.parameters = parameters
        self.validate_params()

    @property
    @abstractmethod
    def name(self) -> str:
        """Indicator symbol name (e.g. SMA, EMA, RSI)."""
        pass

    @property
    @abstractmethod
    def warm_up_bars(self) -> int:
        """Minimum number of historical bars required for valid calculation."""
        pass

    @abstractmethod
    def validate_params(self) -> None:
        """Validates parameter types and numerical ranges."""
        pass

    @abstractmethod
    def calculate_batch(self, df: pd.DataFrame) -> Union[pd.Series, Dict[str, pd.Series]]:
        """Calculates indicator values over an entire OHLCV DataFrame time series."""
        pass
