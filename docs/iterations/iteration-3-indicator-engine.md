# Iteration 3: Quantitative Indicator Engine

## Overview
Implements mathematically correct technical indicators with strict parameter validation, warm-up bar handling, and vectorized batch calculation.

---

## 🏛️ Components Implemented

### 1. Abstract Indicator Interface
Defined in [`base.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/indicators/base.py):
- **`BaseIndicator`**: Abstract base class requiring `name`, `parameters`, `warm_up_bars`, `validate_params()`, and `calculate_batch(df)`.

### 2. Supported Indicator Classes
Implemented in [`calculator.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/indicators/calculator.py):
- **SMA (`SMAIndicator`)**: Simple Moving Average over rolling window $N$.
- **EMA (`EMAIndicator`)**: Exponential Moving Average with smoothing factor $\alpha = 2 / (N + 1)$.
- **RSI (`RSIIndicator`)**: Relative Strength Index (0 to 100) using Wilder's Exponential Smoothing method.
- **MACD (`MACDIndicator`)**: Fast EMA, Slow EMA, MACD line, Signal line, and Histogram.
- **Bollinger Bands (`BollingerBandsIndicator`)**: Middle SMA, Upper Band (+ $K \sigma$), and Lower Band (- $K \sigma$).
- **ATR (`ATRIndicator`)**: Average True Range using True Range formula and Wilder's smoothing.

### 3. Warm-up & NaN Handling
- Early bars prior to `warm_up_bars` are masked as `NaN` to prevent premature signal generation during initial indicator calculation.

### 4. Numerical Testing & Verification
- Unit test suite ([`test_indicators.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/test_indicators.py)) verifies calculations against standard quantitative reference outputs.

---

## 🚀 Deliverable Verification
Given identical market data, Bison produces deterministic, mathematically accurate indicator values.
