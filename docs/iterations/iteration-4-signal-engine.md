# Iteration 4: Signal Engine

## Overview
Transforms market data, indicators, and Strategy DSL rule groups into a deterministic chronological stream of trading signals (`BUY`, `SELL`, `EXIT`).

---

## 🏛️ Components Implemented

### 1. Pipeline Architecture
```text
Market Data (OHLCV)
       ↓
Indicators (Pre-calculated series)
       ↓
Conditions Evaluation (Left vs Right operand)
       ↓
Logical Group Evaluation (AND / OR / NOT)
       ↓
Signal Event Generation (BUY / SELL / EXIT)
```

### 2. Supported Operators
- **Comparison**: `GREATER_THAN` (`>`), `LESS_THAN` (`<`), `GREATER_THAN_EQUAL` (`>=`), `LESS_THAN_EQUAL` (`<=`), `EQUAL` (`=`), `NOT_EQUAL` (`!=`).
- **Crossover**: `CROSS_ABOVE`, `CROSS_BELOW`.
- **Logical**: `AND`, `OR`, `NOT`.

### 3. Signal Event Model
Defined in [`models.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/signals/models.py):
- **`Signal`**: `signal_id`, `timestamp`, `symbol`, `signal_type` (`BUY`/`SELL`/`EXIT`), `bar_index`, `trigger_price`, `reason`, `indicator_snapshot`.

### 4. Zero Look-Ahead & Warm-up Protection
- Signals evaluate prices and pre-calculated indicators strictly at bar $t$ close.
- Initial indicator warm-up bars containing `NaN` return `False`, preventing invalid early signal triggers.

---

## 🚀 Deliverable Verification
Unit tests in [`test_signal_engine.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/test_signal_engine.py) verify crossover evaluation, multiple condition groups, `NOT` operator logic, warm-up protection, and deterministic signal generation.
