# Backtesting Engine Architecture

## Core Execution Semantics & Zero Look-Ahead Bias

The backtesting engine is designed as a deterministic event-driven chronological simulator.

```text
Bar t Close
    ↓
Indicator Calculation
    ↓
Strategy Rule Evaluation
    ↓
Signal Generation
    ↓
Order Factory Creation (Eligible at Bar t+1)
    ↓
Bar t+1 Open Arrival
    ↓
Execution Simulator (Fills at Bar t+1 Open + Slippage + Tick Normalization)
    ↓
Indian Friction & Cost Accounting
```

### Bar Event Sequence

For each bar $t$ in chronological order:
1. **Process Eligible Pending Orders**: Any pending order generated on bar $t-1$ evaluates against bar $t$ `Open` via `ExecutionSimulator`.
2. **Evaluate Active Position Exits**: Check Stop-Loss, Target, Max Holding Bars, Strategy Exit Rules, or End-of-Day exit triggers.
3. **Evaluate Strategy Entry Rules**: Evaluate rules strictly using price & indicator data available up to bar $t$ `Close`.
4. **Generate Signal & Create Order**: Convert triggered signal into a validated `Order` via `OrderFactory` marked eligible for bar $t+1$.
5. **Mark-to-Market Equity Point**: Record current equity, cash, and drawdown metrics.

---

### Indian Cost Model Accounting
For each executed trade, transaction friction is calculated:
- **Brokerage**: Flat ₹20 per trade or 0.03% (whichever is lower).
- **STT (Securities Transaction Tax)**: 0.025% on sell side (intraday) / 0.1% on buy+sell (delivery).
- **Exchange Turnover Charge**: 0.00345% (NSE).
- **GST**: 18% on (Brokerage + Exchange Charges).
- **SEBI Charges**: ₹10 per crore (0.0001%).
- **Stamp Duty**: 0.003% on buy side.
- **Slippage**: `ZeroSlippage`, `FixedPointsSlippage`, or `PercentageSlippage`.
