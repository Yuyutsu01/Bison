# Order & Execution Model Architecture

## 1. Executive Overview

The **Order & Execution Simulation Domain** forms the boundary between signal generation (the strategy logic) and trade management. It converts abstract signals (`BUY`, `SELL`, `EXIT`) into strongly typed, validated `Order` objects and simulates their execution against historical or live price feeds with strict temporal invariants.

```text
Historical Market Data (OHLCV)
        ↓
Indicator Engine
        ↓
Strategy / Signal Engine (Evaluated at bar t Close)
        ↓
Signal
        ↓
Order Factory (Converts Signal -> Order eligible at bar t+1)
        ↓
Order Validation (Quantity, Lot Size, Session, Order Type)
        ↓
Execution Simulator (Bar t+1 Open + Slippage + Tick Normalization)
        ↓
Execution Record
```

---

## 2. Temporal Invariant & Execution Policies

### Zero Look-Ahead Bias
All strategy signals generated from bar $t$ price data evaluate strictly at bar $t$ **Close**.
Under the default execution policy (`NEXT_BAR_OPEN`):
- **Order Created**: Bar $t$ Close.
- **Order Eligible**: Bar $t+1$ Open.
- **Execution Price**: Bar $t+1$ Open $\pm$ Slippage, normalized to instrument tick size.

Orders can never fill using bar $t$ Close price data.

---

## 3. Order Lifecycle & State Machine

```text
CREATED
   ↓
PENDING
   ├── FILLED
   ├── CANCELLED
   ├── REJECTED
   └── EXPIRED
```

### State Machine Rules
- **`CREATED` -> `PENDING`**: Order queued for execution eligibility.
- **`PENDING` -> `FILLED`**: Order executed successfully against incoming bar $t+1$ Open.
- **`PENDING` -> `REJECTED`**: Order rejected due to invalid parameters, lot size mismatch, or unsupported order type.
- **`CREATED` / `PENDING` -> `EXPIRED`**: Triggered when a signal occurs on the final historical candle without a subsequent $t+1$ bar.
- Terminal states (`FILLED`, `CANCELLED`, `REJECTED`, `EXPIRED`) cannot transition to any other state. Attempting an invalid state transition raises `InvalidStateTransitionError`.

---

## 4. Slippage Models & Pricing Normalization

### Supported Slippage Models
1. **`ZeroSlippage`**: `slippage = 0.0`
2. **`FixedPointsSlippage`**: Fixed price movement against order direction (`BUY` adds points, `SELL` subtracts points).
3. **`PercentageSlippage`**: Percentage price impact against reference price.

### Tick Size Normalization
Execution prices are rounded to valid tick increments (e.g. ₹0.05 for NSE) using exact financial `Decimal` arithmetic:
$$\text{ticks} = \text{round\_half\_up}\left(\frac{\text{price}}{\text{tick\_size}}\right)$$
$$\text{execution\_price} = \text{ticks} \times \text{tick\_size}$$

---

## 5. Idempotency & Duplicate Protection

Order idempotency keys are generated deterministically as:
$$\text{idempotency\_key} = \text{sha256}(\text{strategy\_version\_id} : \text{signal\_timestamp} : \text{symbol} : \text{side})[0:16]$$
Submitting a duplicate signal produces the existing order. Re-submitting a `FILLED` order to `ExecutionSimulator` returns the cached `Execution` object without creating duplicate fills.
