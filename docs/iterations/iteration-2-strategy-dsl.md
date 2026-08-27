# Iteration 2: Strategy DSL & Validation Engine

## Overview
Creates the formal, serializable domain language (DSL) for quantitative trading strategies and a multi-level validator.

---

## 🏛️ Components Implemented

### 1. Pydantic Strategy DSL Schemas
Defined in [`schemas.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/strategies/schemas.py):
- **`InstrumentSpec`**: Symbol, exchange (`NSE`/`BSE`), timeframe (`1m`, `5m`, `15m`, `1h`, `1d`).
- **`Operand`**: `PriceOperand`, `IndicatorOperand` (name + parameters), `ConstantOperand`.
- **`Condition`**: `left`, `operator`, `right`.
- **`RuleGroup`**: Logical operator (`AND`, `OR`, `NOT`) + condition list.
- **`RiskManagement`**: Stop-Loss %, Target %, Trailing Stop %, Max Holding Bars, End-of-Day exit.
- **`PositionSizing`**: `FIXED_QUANTITY` and `PERCENT_OF_CAPITAL`.
- **`StrategyDSL`**: Full serializable strategy object.

### 2. Strategy Versioning
- **Database Model**: [`StrategyVersionModel`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/db/models.py) storing version number (`v1`, `v2`, `v3`), strategy ID, created timestamp, and raw `dsl_json`.
- **Immutable References**: Backtest runs reference an immutable `StrategyVersionModel` ID to guarantee reproducibility.

### 3. Multi-Level Strategy Validator
Implemented in [`validator.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/strategies/validator.py):
- Validates missing entry conditions.
- Validates indicator names against supported registry (`SMA`, `EMA`, `RSI`, `MACD`, `BB`, `ATR`).
- Validates indicator parameters (period > 0, fast < slow for MACD, std_dev > 0 for Bollinger Bands).
- Validates risk rules (stop-loss % > 0, target % > 0).
- Validates position sizing value > 0.
- Returns structured diagnostic error lists (e.g. `Entry Condition #1: Indicator 'RSI' parameter 'period' must be a positive integer > 0`).

---

## 🚀 Deliverable Verification
Bison represents, validates, and versions trading strategies completely independent of HTTP transport or frontend UI state.
