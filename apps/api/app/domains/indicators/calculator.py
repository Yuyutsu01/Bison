"""
Quantitative Indicator Engine.

Calculates technical analysis indicators (SMA, EMA, RSI, MACD, Bollinger Bands, ATR)
over OHLCV price time series data with precision and zero look-ahead bias.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


class IndicatorEngine:
    """Calculates quantitative technical indicators on pandas DataFrame containing OHLCV candles."""

    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int = 20, column: str = "close") -> pd.Series:
        """Simple Moving Average: arithmetic mean over rolling window of size `period`."""
        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found in DataFrame.")
        return df[column].rolling(window=period, min_periods=period).mean()

    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int = 20, column: str = "close") -> pd.Series:
        """Exponential Moving Average: weighted average with decay factor alpha = 2 / (period + 1)."""
        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found in DataFrame.")
        return df[column].ewm(span=period, adjust=False, min_periods=period).mean()

    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = "close") -> pd.Series:
        """
        Relative Strength Index (RSI):
        Measures speed and change of price movements on a scale from 0 to 100.
        Uses Wilder's Exponential Smoothing method for gain and loss averages.
        """
        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found in DataFrame.")

        delta = df[column].diff()
        gain = delta.clip(lower=0.0)
        loss = -1.0 * delta.clip(upper=0.0)

        # Wilder's Exponential Smoothing (alpha = 1 / period)
        avg_gain = gain.ewm(alpha=1.0/period, adjust=False, min_periods=period).mean()
        avg_loss = loss.ewm(alpha=1.0/period, adjust=False, min_periods=period).mean()

        rs = avg_gain / (avg_loss.replace(0.0, np.nan))
        rsi = 100.0 - (100.0 / (1.0 + rs))

        # Handle zero loss case (RSI = 100)
        rsi = rsi.fillna(100.0)
        # Handle early warm-up NaN values
        rsi.iloc[:period] = np.nan
        return rsi

    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        column: str = "close"
    ) -> Dict[str, pd.Series]:
        """
        MACD (Moving Average Convergence Divergence):
        Returns dict containing 'macd', 'signal', and 'histogram' series.
        """
        fast_ema = IndicatorEngine.calculate_ema(df, period=fast_period, column=column)
        slow_ema = IndicatorEngine.calculate_ema(df, period=slow_period, column=column)

        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False, min_periods=signal_period).mean()
        histogram = macd_line - signal_line

        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram
        }

    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        column: str = "close"
    ) -> Dict[str, pd.Series]:
        """
        Bollinger Bands:
        Returns dict with 'middle' (SMA), 'upper', and 'lower' band series.
        """
        middle_band = IndicatorEngine.calculate_sma(df, period=period, column=column)
        rolling_std = df[column].rolling(window=period, min_periods=period).std()

        upper_band = middle_band + (std_dev * rolling_std)
        lower_band = middle_band - (std_dev * rolling_std)

        return {
            "middle": middle_band,
            "upper": upper_band,
            "lower": lower_band
        }

    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Average True Range (ATR):
        Measures market volatility based on high, low, and previous close prices.
        """
        required_cols = {"high", "low", "close"}
        if not required_cols.issubset(df.columns):
            raise KeyError(f"DataFrame missing required OHLC columns: {required_cols - set(df.columns)}")

        high = df["high"]
        low = df["low"]
        prev_close = df["close"].shift(1)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Wilder's smoothing for ATR
        atr = true_range.ewm(alpha=1.0/period, adjust=False, min_periods=period).mean()
        atr.iloc[:period] = np.nan
        return atr
