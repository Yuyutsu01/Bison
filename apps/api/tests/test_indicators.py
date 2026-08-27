import pytest
import pandas as pd
import numpy as np
from app.domains.indicators.calculator import IndicatorEngine


@pytest.fixture
def sample_ohlcv_data():
    dates = pd.date_range("2026-01-01", periods=30, freq="1D")
    prices = [100.0 + i * 2.0 for i in range(30)]  # Steady uptrend
    return pd.DataFrame({
        "timestamp": dates,
        "open": prices,
        "high": [p + 1.0 for p in prices],
        "low": [p - 1.0 for p in prices],
        "close": prices,
        "volume": [10000] * 30
    })


def test_sma_calculation(sample_ohlcv_data):
    sma = IndicatorEngine.calculate_sma(sample_ohlcv_data, period=10)
    assert pd.isna(sma.iloc[8])
    assert not pd.isna(sma.iloc[9])
    # Mean of 100, 102, 104, 106, 108, 110, 112, 114, 116, 118 = 109.0
    assert pytest.approx(sma.iloc[9], 0.01) == 109.0


def test_ema_calculation(sample_ohlcv_data):
    ema = IndicatorEngine.calculate_ema(sample_ohlcv_data, period=10)
    assert pd.isna(ema.iloc[8])
    assert not pd.isna(ema.iloc[9])
    assert ema.iloc[29] > ema.iloc[10]  # EMA follows uptrend


def test_rsi_calculation(sample_ohlcv_data):
    rsi = IndicatorEngine.calculate_rsi(sample_ohlcv_data, period=14)
    # In a pure uptrend, RSI should approach 100
    assert rsi.iloc[29] > 90.0


def test_bollinger_bands(sample_ohlcv_data):
    bb = IndicatorEngine.calculate_bollinger_bands(sample_ohlcv_data, period=20, std_dev=2.0)
    assert "middle" in bb and "upper" in bb and "lower" in bb
    assert bb["upper"].iloc[25] > bb["middle"].iloc[25]
    assert bb["lower"].iloc[25] < bb["middle"].iloc[25]


def test_atr_calculation(sample_ohlcv_data):
    atr = IndicatorEngine.calculate_atr(sample_ohlcv_data, period=14)
    assert not pd.isna(atr.iloc[15])
    assert atr.iloc[15] > 0.0
