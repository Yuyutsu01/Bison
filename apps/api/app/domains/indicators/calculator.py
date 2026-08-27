"""
Quantitative Indicator Engine & Concrete Indicator Classes.

Implements SMA, EMA, RSI, MACD, Bollinger Bands, and ATR indicators
with strict parameter validation, warm-up handling, and batch/streaming execution.
"""

from typing import Dict, Any, Union
import pandas as pd
import numpy as np
from app.domains.indicators.base import BaseIndicator


class SMAIndicator(BaseIndicator):
    @property
    def name(self) -> str:
        return "SMA"

    @property
    def warm_up_bars(self) -> int:
        return self.parameters.get("period", 20)

    def validate_params(self) -> None:
        period = self.parameters.get("period", 20)
        if not isinstance(period, int) or period <= 0:
            raise ValueError(f"SMA period must be a positive integer > 0, got {period}.")

    def calculate_batch(self, df: pd.DataFrame) -> pd.Series:
        period = self.parameters.get("period", 20)
        column = self.parameters.get("column", "close")
        return df[column].rolling(window=period, min_periods=period).mean()


class EMAIndicator(BaseIndicator):
    @property
    def name(self) -> str:
        return "EMA"

    @property
    def warm_up_bars(self) -> int:
        return self.parameters.get("period", 20)

    def validate_params(self) -> None:
        period = self.parameters.get("period", 20)
        if not isinstance(period, int) or period <= 0:
            raise ValueError(f"EMA period must be a positive integer > 0, got {period}.")

    def calculate_batch(self, df: pd.DataFrame) -> pd.Series:
        period = self.parameters.get("period", 20)
        column = self.parameters.get("column", "close")
        return df[column].ewm(span=period, adjust=False, min_periods=period).mean()


class RSIIndicator(BaseIndicator):
    @property
    def name(self) -> str:
        return "RSI"

    @property
    def warm_up_bars(self) -> int:
        return self.parameters.get("period", 14) + 1

    def validate_params(self) -> None:
        period = self.parameters.get("period", 14)
        if not isinstance(period, int) or period <= 0:
            raise ValueError(f"RSI period must be a positive integer > 0, got {period}.")

    def calculate_batch(self, df: pd.DataFrame) -> pd.Series:
        period = self.parameters.get("period", 14)
        column = self.parameters.get("column", "close")

        delta = df[column].diff()
        gain = delta.clip(lower=0.0)
        loss = -1.0 * delta.clip(upper=0.0)

        avg_gain = gain.ewm(alpha=1.0/period, adjust=False, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1.0/period, adjust=False, min_periods=period).mean()

        rs = avg_gain / (avg_loss.replace(0.0, np.nan))
        rsi = 100.0 - (100.0 / (1.0 + rs))
        rsi = rsi.fillna(100.0)
        rsi.iloc[:period] = np.nan
        return rsi


class MACDIndicator(BaseIndicator):
    @property
    def name(self) -> str:
        return "MACD"

    @property
    def warm_up_bars(self) -> int:
        slow = self.parameters.get("slow_period", 26)
        signal = self.parameters.get("signal_period", 9)
        return slow + signal

    def validate_params(self) -> None:
        fast = self.parameters.get("fast_period", 12)
        slow = self.parameters.get("slow_period", 26)
        signal = self.parameters.get("signal_period", 9)

        if not isinstance(fast, int) or fast <= 0:
            raise ValueError("MACD fast_period must be > 0.")
        if not isinstance(slow, int) or slow <= 0:
            raise ValueError("MACD slow_period must be > 0.")
        if not isinstance(signal, int) or signal <= 0:
            raise ValueError("MACD signal_period must be > 0.")
        if fast >= slow:
            raise ValueError(f"MACD fast_period ({fast}) must be strictly less than slow_period ({slow}).")

    def calculate_batch(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        fast = self.parameters.get("fast_period", 12)
        slow = self.parameters.get("slow_period", 26)
        signal = self.parameters.get("signal_period", 9)
        column = self.parameters.get("column", "close")

        fast_ema = df[column].ewm(span=fast, adjust=False, min_periods=fast).mean()
        slow_ema = df[column].ewm(span=slow, adjust=False, min_periods=slow).mean()

        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal, adjust=False, min_periods=signal).mean()
        histogram = macd_line - signal_line

        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }


class BollingerBandsIndicator(BaseIndicator):
    @property
    def name(self) -> str:
        return "BB"

    @property
    def warm_up_bars(self) -> int:
        return self.parameters.get("period", 20)

    def validate_params(self) -> None:
        period = self.parameters.get("period", 20)
        std_dev = self.parameters.get("std_dev", 2.0)

        if not isinstance(period, int) or period <= 0:
            raise ValueError("Bollinger Bands period must be > 0.")
        if not isinstance(std_dev, (int, float)) or std_dev <= 0:
            raise ValueError("Bollinger Bands std_dev must be > 0.")

    def calculate_batch(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        period = self.parameters.get("period", 20)
        std_dev = self.parameters.get("std_dev", 2.0)
        column = self.parameters.get("column", "close")

        middle = df[column].rolling(window=period, min_periods=period).mean()
        rolling_std = df[column].rolling(window=period, min_periods=period).std()

        upper = middle + (std_dev * rolling_std)
        lower = middle - (std_dev * rolling_std)

        return {
            "middle": middle,
            "upper": upper,
            "lower": lower
        }


class ATRIndicator(BaseIndicator):
    @property
    def name(self) -> str:
        return "ATR"

    @property
    def warm_up_bars(self) -> int:
        return self.parameters.get("period", 14) + 1

    def validate_params(self) -> None:
        period = self.parameters.get("period", 14)
        if not isinstance(period, int) or period <= 0:
            raise ValueError("ATR period must be > 0.")

    def calculate_batch(self, df: pd.DataFrame) -> pd.Series:
        period = self.parameters.get("period", 14)
        high = df["high"]
        low = df["low"]
        prev_close = df["close"].shift(1)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr = true_range.ewm(alpha=1.0/period, adjust=False, min_periods=period).mean()
        atr.iloc[:period] = np.nan
        return atr


class IndicatorEngine:
    """Static wrapper helper providing simplified batch calculation methods for all indicators."""

    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int = 20, column: str = "close") -> pd.Series:
        return SMAIndicator({"period": period, "column": column}).calculate_batch(df)

    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int = 20, column: str = "close") -> pd.Series:
        return EMAIndicator({"period": period, "column": column}).calculate_batch(df)

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = "close") -> pd.Series:
        return RSIIndicator({"period": period, "column": column}).calculate_batch(df)

    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, column: str = "close") -> Dict[str, pd.Series]:
        return MACDIndicator({"fast_period": fast_period, "slow_period": slow_period, "signal_period": signal_period, "column": column}).calculate_batch(df)

    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0, column: str = "close") -> Dict[str, pd.Series]:
        return BollingerBandsIndicator({"period": period, "std_dev": std_dev, "column": column}).calculate_batch(df)

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        return ATRIndicator({"period": period}).calculate_batch(df)
