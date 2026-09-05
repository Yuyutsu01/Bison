# Iteration 5: Order & Execution Simulator

## Overview
Iteration 5 implements a production-grade **Order & Execution Simulation Domain** for Bison. It decouples strategy signal generation from order routing, state machine lifecycle management, slippage modeling, tick size pricing normalization, and execution simulation.

---

## 🏛️ Key Features Implemented

### 1. Pure Domain Order & Execution Models
- **Enums**: `OrderSide` (`BUY`, `SELL`, `LONG_ENTRY`, `LONG_EXIT`, `SHORT_ENTRY`, `SHORT_EXIT`), `OrderType` (`MARKET`, `LIMIT`, `STOP`, `STOP_LIMIT`), `OrderStatus` (`CREATED`, `PENDING`, `FILLED`, `CANCELLED`, `REJECTED`, `EXPIRED`), `ExecutionPolicy` (`NEXT_BAR_OPEN`).
- **Order State Machine**: Enforces strict legal transitions (`CREATED` -> `PENDING` -> `FILLED`) and throws domain errors on invalid transitions.
- **Idempotency Protection**: Deterministic SHA-256 idempotency key prevents duplicate order creation or double execution fills.

### 2. Execution Policies & Slippage Models
- **`NEXT_BAR_OPEN` Execution Policy**: Guarantees zero look-ahead bias by executing signals generated on bar $t$ Close strictly on bar $t+1$ Open.
- **Slippage Models**: Supported `ZeroSlippage`, `FixedPointsSlippage`, and `PercentageSlippage`.
- **Financial Precision & Tick Normalization**: `Decimal` arithmetic rounding execution prices to exact instrument tick sizes (e.g. ₹0.05).

### 3. Edge Case Handling
- **Missing Next Bar**: Final candle signals without a subsequent bar transition to `EXPIRED`.
- **Lot Size & Quantity Validation**: Enforces quantity $> 0$ and integer multiples of lot sizes (e.g., 50 for NIFTY).

### 4. Database Persistence & API Exposure
- **SQLAlchemy ORM Models**: `OrderModel` and `ExecutionModel`.
- **Alembic Migration**: `003_orders_executions`.
- **REST Endpoints**:
  - `GET /api/v1/backtests/{id}/orders`
  - `GET /api/v1/backtests/{id}/executions`

---

## 🚀 Test Verification & Coverage

Full test suite in `apps/api/tests/` passes with 31 unit, integration, look-ahead leakage, and determinism tests:
- `test_order_domain.py`: Order creation, state transitions, factory lot size checks.
- `test_execution_simulator.py`: `NEXT_BAR_OPEN` fills, missing bar `EXPIRED` status, idempotency.
- `test_slippage_and_pricing.py`: Slippage models and tick size rounding.
- `test_look_ahead_prevention.py`: Proves bar $t$ signal cannot execute on bar $t$ Close.
- `test_determinism.py`: Proves double backtest runs produce identical orders and executions.
