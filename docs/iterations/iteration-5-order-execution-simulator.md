# Iteration 5: Order & Execution Simulator

## Overview
Transforms strategy signals into strongly typed `Order` objects and deterministically simulates their execution on subsequent price bars with `NEXT_BAR_OPEN` policy, slippage models, tick size normalization, state machine lifecycle management, and idempotency protection.

---

## 🏛️ Components Implemented

### 1. Pure Domain Order Architecture
- **`Order` Model**: Strongly typed domain dataclass with `Decimal` quantities, prices, state machine transitions, and SHA-256 idempotency key.
- **`OrderFactory`**: Maps `Signal` events into `Order` entities with lot size and quantity validation.

### 2. Execution Simulator & Policies
- **`ExecutionSimulator`**: Pure domain component simulating fills against market price bars.
- **`NEXT_BAR_OPEN` Execution Policy**: Guarantees zero look-ahead bias by executing signals generated on bar $t$ Close strictly on bar $t+1$ Open.
- **Slippage Models**: `ZeroSlippage`, `FixedPointsSlippage`, `PercentageSlippage`.
- **Pricing Normalization**: Tick size rounding using `Decimal` arithmetic.

### 3. Persistence & API Layer
- **SQLAlchemy ORM**: `OrderModel` and `ExecutionModel`.
- **Alembic Migration**: `003_orders_executions`.
- **REST Endpoints**:
  - `GET /api/v1/backtests/{id}/orders`
  - `GET /api/v1/backtests/{id}/executions`

---

## 🚀 Deliverable Verification
Unit and integration tests in `apps/api/tests/` verify:
- Order state machine transitions & illegal transition prevention.
- `NEXT_BAR_OPEN` fill execution & missing next bar expiry handling.
- Look-ahead leakage prevention tests.
- Double-run determinism tests.
