# Iteration 5: Order & Execution Simulator — Implementation Report

## 1. What Was Implemented

Iteration 5 delivers a production-grade **Order & Execution Simulation Domain** for Bison, sitting between the Signal Engine and the future Portfolio/Risk Engine.

Key deliverables completed:
- **Order Domain & State Machine**: Strongly typed `Order` entity, enums (`OrderSide`, `OrderType`, `OrderStatus`), domain exceptions, state machine transition validation (`CREATED` -> `PENDING` -> `FILLED`), and `OrderFactory` with lot size and quantity checks.
- **Execution Simulator & Policies**: Pure domain `ExecutionSimulator` engine enforcing the `NEXT_BAR_OPEN` execution policy.
- **Slippage Models**: Pluggable `SlippageModel` interface with `ZeroSlippage`, `FixedPointsSlippage`, and `PercentageSlippage`.
- **Pricing & Tick-Size Handling**: `normalize_to_tick_size` utility using exact `Decimal` arithmetic.
- **Idempotency Protection**: Deterministic SHA-256 idempotency key generation preventing duplicate order creation or double fills.
- **Edge Case Protection**: Missing next bar handling (signals on final candle transition order to `EXPIRED`).
- **Database & API Integration**: `OrderModel` and `ExecutionModel` ORM schema, Alembic migration `003_orders_and_executions.py`, and REST endpoints (`GET /api/v1/backtests/{id}/orders`, `GET /api/v1/backtests/{id}/executions`).
- **Test Verification**: 31 unit, integration, zero look-ahead leakage, and determinism tests passed.

---

## 2. Order Architecture

The Order domain is isolated inside [`app/domains/orders/`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/orders/):

- **[`models.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/orders/models.py)**:
  - **`OrderSide`**: `BUY`, `SELL`, `LONG_ENTRY`, `LONG_EXIT`, `SHORT_ENTRY`, `SHORT_EXIT`.
  - **`OrderType`**: `MARKET` (supported in Iteration 5), `LIMIT`, `STOP`, `STOP_LIMIT`.
  - **`OrderStatus`**: `CREATED`, `PENDING`, `FILLED`, `CANCELLED`, `REJECTED`, `EXPIRED`.
  - **State Machine (`LEGAL_TRANSITIONS`)**: Defines valid state transitions and raises `InvalidStateTransitionError` on illegal moves.
- **[`factory.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/orders/factory.py)**:
  - **`OrderFactory`**: Converts strategy `Signal` objects into `Order` entities. Enforces quantity $> 0$ and divisibility by instrument `lot_size`.

---

## 3. Execution Architecture

The Execution domain is isolated inside [`app/domains/execution/`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/execution/):

- **[`models.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/execution/models.py)**: `Execution` domain model recording `reference_price`, `execution_price`, `slippage`, and `status`.
- **[`simulator.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/execution/simulator.py)**: `ExecutionSimulator` pure domain engine. Evaluates orders against market price bars without database, web framework, or external dependencies.

---

## 4. Execution Semantics

Iteration 5 strictly enforces **Zero Look-Ahead Bias**:

```text
Bar t Close
    ↓
Strategy Rule Evaluation
    ↓
Signal Generated at Bar t Close
    ↓
Order Created (Eligible at Bar t+1 Open)
    ↓
Bar t+1 Open Arrival
    ↓
Execution Fills at Bar t+1 Open ± Slippage (Tick-Normalized)
```

- Signal generated at bar $t$ Close can **never** execute using bar $t$ Close prices.
- Default policy is **`NEXT_BAR_OPEN`**.

---

## 5. Slippage Models

Defined in [`app/domains/execution/slippage.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/execution/slippage.py):

1. **`ZeroSlippage`**: `slippage = Decimal("0.0")`
2. **`FixedPointsSlippage(points)`**:
   - `BUY` execution price = `reference_price + points`
   - `SELL` execution price = `reference_price - points`
3. **`PercentageSlippage(pct)`**:
   - `BUY` execution price = `reference_price * (1 + pct)`
   - `SELL` execution price = `reference_price * (1 - pct)`

---

## 6. Tick-Size Handling

Defined in [`app/domains/execution/pricing.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/execution/pricing.py):

```python
def normalize_to_tick_size(price: Decimal, tick_size: Decimal) -> Decimal:
    ticks = (price / tick_size).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return ticks * tick_size
```

- Converts floating point inputs to `Decimal`.
- Quantizes prices to valid tick boundaries (e.g. ₹0.05 for NSE) using `ROUND_HALF_UP` arithmetic.

---

## 7. Session Handling

- Orders verify eligibility timestamps against incoming market bar timestamps.
- If an order becomes eligible outside session bounds or market hours, execution is rejected or deferred per session rules.

---

## 8. Idempotency Approach

- **Order Idempotency Key**:
  $$\text{idempotency\_key} = \text{sha256}(\text{strategy\_version\_id} : \text{signal\_timestamp} : \text{symbol} : \text{side})[0:16]$$
- **Execution Protection**: `ExecutionSimulator` caches filled orders by idempotency key. Resubmitting an already `FILLED` order returns the existing `Execution` record without duplicate fills.

---

## 9. Database Changes

- **[`app/db/models.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/db/models.py)**: Added `OrderModel` (`orders` table) and `ExecutionModel` (`executions` table) with relationships to `BacktestRunModel`.
- **Migration**: [`003_orders_and_executions.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/migrations/versions/003_orders_and_executions.py) creates tables with foreign keys and cascade delete rules.

---

## 10. API Changes

Updated [`apps/api/app/domains/backtesting/routes.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/backtesting/routes.py):
- `GET /api/v1/backtests/{backtest_id}/orders`: Returns list of `OrderDTO`.
- `GET /api/v1/backtests/{backtest_id}/executions`: Returns list of `ExecutionDTO`.

---

## 11. Tests Created

1. **[`test_order_domain.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/orders/test_order_domain.py)**: Tests order creation, state machine transitions, illegal transition prevention, and lot size validation.
2. **[`test_slippage_and_pricing.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/execution/test_slippage_and_pricing.py)**: Tests zero/fixed/percentage slippage models and tick size rounding.
3. **[`test_execution_simulator.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/execution/test_execution_simulator.py)**: Tests `NEXT_BAR_OPEN` fills, missing next bar expiry, and idempotency lookup.
4. **[`test_look_ahead_prevention.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/execution/test_look_ahead_prevention.py)**: Proves signal at bar $t$ Close cannot execute on bar $t$ Close.
5. **[`test_determinism.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/execution/test_determinism.py)**: Proves double-running backtest yields bitwise identical orders and executions.

---

## 12. Full Test Results

Running `pytest apps/api/tests`:

```text
======================== 31 passed in 2.66s ========================
```

All 31 unit, integration, zero look-ahead, and determinism tests pass cleanly with zero errors.

---

## 13. Known Limitations

- **Order Types**: Iteration 5 implements `MARKET` order execution. `LIMIT`, `STOP`, and `STOP_LIMIT` raise `UnsupportedOrderTypeError` (scheduled for Iteration 6).
- **Position & Margin Engine**: Full multi-position margin tracking and portfolio risk models are deferred to Iteration 6.
- **Broker Integration**: Live broker APIs (Zerodha/Angel One) and paper trading accounts belong to later iterations.

---

## 14. Files & Modules Created or Modified

### Created Modules
- [`apps/api/app/domains/orders/models.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/orders/models.py)
- [`apps/api/app/domains/orders/factory.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/orders/factory.py)
- [`apps/api/app/domains/execution/models.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/execution/models.py)
- [`apps/api/app/domains/execution/pricing.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/execution/pricing.py)
- [`apps/api/app/domains/execution/slippage.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/execution/slippage.py)
- [`apps/api/app/domains/execution/simulator.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/execution/simulator.py)
- [`apps/api/migrations/versions/003_orders_and_executions.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/migrations/versions/003_orders_and_executions.py)
- [`apps/api/tests/unit/orders/test_order_domain.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/orders/test_order_domain.py)
- [`apps/api/tests/unit/execution/test_slippage_and_pricing.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/execution/test_slippage_and_pricing.py)
- [`apps/api/tests/unit/execution/test_execution_simulator.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/execution/test_execution_simulator.py)
- [`apps/api/tests/unit/execution/test_look_ahead_prevention.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/execution/test_look_ahead_prevention.py)
- [`apps/api/tests/unit/execution/test_determinism.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/execution/test_determinism.py)
- [`docs/architecture/execution-model.md`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/docs/architecture/execution-model.md)
- [`docs/product/iteration-5.md`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/docs/product/iteration-5.md)

### Modified Files
- [`apps/api/app/db/models.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/db/models.py)
- [`apps/api/app/domains/backtesting/engine.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/backtesting/engine.py)
- [`apps/api/app/domains/backtesting/routes.py`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/backtesting/routes.py)
- [`docs/architecture/backtesting-engine.md`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/docs/architecture/backtesting-engine.md)
- [`README.md`](file:///c:/Users/shiva/OneDrive/Desktop/projects/Bison/README.md)

---

## 15. Instructions for Running New Functionality

### Running Unit & Integration Tests
```bash
pytest apps/api/tests
```

### Running Database Migrations
```bash
cd apps/api
alembic upgrade head
```

### Launching Full Stack
```bash
docker-compose up --build
```

---

## 16. Recommended Scope for Iteration 6

### Iteration 6: Position & Portfolio Risk Engine
- **Position Tracking**: Aggregate executed fills into active positions (Long/Short, Average Entry Price, Realized vs Unrealized P&L).
- **Order Types Expansion**: Implement `LIMIT`, `STOP`, and `STOP_LIMIT` order execution logic in `ExecutionSimulator`.
- **Portfolio Sizing & Risk Management**: Account leverage, max position exposure limits, multi-asset portfolio rebalancing, and trailing stop-loss execution models.
