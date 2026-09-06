# Risk Engine Architecture

## 1. Overview & Non-Mutation Invariant

The **Risk Engine** continuously monitors open positions and account state against strategy risk rules.

```text
Market Bar t
    ↓
Portfolio State
    ↓
Risk Engine Evaluation
    ↓
Risk Event Logged
    ↓
Exit Signal -> Order Engine
```

### Core Invariant
> **The Risk Engine never mutates positions or portfolio balances directly.**
> When a risk rule breaches, the Risk Engine generates an **Exit Order** that is processed through the canonical pipeline (`Order -> Execution -> Portfolio`).

---

## 2. Risk Controls Implemented

1. **Stop-Loss**: Triggers exit order if market price breaches Stop-Loss threshold (for Long: `bar_low <= sl_price`).
2. **Target (Take Profit)**: Triggers exit order if market price touches Target threshold (for Long: `bar_high >= target_price`).
3. **Trailing Stop**: Tracks `highest_price_since_entry` for Long positions and triggers exit if price drops below `highest_price * (1 - trailing_percent)`. The trailing reference level moves strictly in favorable direction.
4. **Max Holding Period**: Triggers exit order when `holding_bars >= max_holding_bars`.
5. **End-of-Day Exit**: Triggers exit order on session close.
6. **Max Simultaneous Positions**: Rejects new entry orders if active open positions count reaches `max_positions`.

---

## 3. Intrabar Conflict & Gap Execution Policies

### Intrabar Conflict Policy
When both Stop-Loss and Target thresholds are breached within the same OHLC bar:
- **Policy**: Conservative assumption -> The **adverse event (Stop-Loss)** is assumed to have occurred first.
- **Log**: Recorded with `intrabar_conflict: True` in `RiskEvent` metadata.

### Gap Execution Policy
When the market opens beyond a Stop-Loss threshold (e.g. Stop at ₹95, Next Open at ₹90):
- **Policy**: Trigger price is set to `bar_open` (actual next available price ₹90), preventing fake fills at impossible stop prices.
