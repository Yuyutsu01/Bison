# Portfolio Engine Architecture

## 1. Overview & Source of Truth Principle

The **Portfolio Engine** is a deterministic financial accounting subsystem for Bison. It maintains the exact account balance, cash, positions, valuation, exposure, and P&L of a strategy backtest.

```text
Signal (Analytical Intent)
    ↓
Order (Instruction)
    ↓
Execution (Simulated Fill)
    ↓
Portfolio Service (Applies Fill -> Updates Positions, Cash, Realized P&L)
    ↓
Mark-to-Market Valuation (Recalculates Unrealized P&L & Equity Snapshot)
    ↓
Risk Engine (Evaluates Risk Rules -> Emits Exit Orders to Order Engine)
```

### Core Invariant
> **Executions are the sole source of truth for portfolio updates.**
> Signals or orders NEVER alter portfolio balances or position sizes directly.

---

## 2. Financial Accounting Model

### Accounting Invariants
$$\text{Equity} = \text{Cash} + \text{Gross Exposure (Market Value of Open Positions)}$$
$$\text{Total PnL} = \text{Realized PnL} + \text{Unrealized PnL} = \text{Equity} - \text{Initial Capital}$$

### Weighted Average Entry Price
When adding to an existing position:
$$\text{Average Entry Price} = \frac{(Q_{\text{existing}} \times P_{\text{existing}}) + (Q_{\text{new}} \times P_{\text{new}})}{Q_{\text{existing}} + Q_{\text{new}}}$$

### P&L Formulas
- **Long Unrealized P&L**: $(P_{\text{current}} - P_{\text{avg\_entry}}) \times Q$
- **Long Realized P&L**: $(P_{\text{exit}} - P_{\text{avg\_entry}}) \times Q_{\text{closed}}$
- **Short Unrealized P&L**: $(P_{\text{avg\_entry}} - P_{\text{current}}) \times Q$
- **Short Realized P&L**: $(P_{\text{avg\_entry}} - P_{\text{exit}}) \times Q_{\text{closed}}$

---

## 3. Position Sizing Policy

Defined in `app.domains.portfolio.sizing.PositionSizingEngine`:
- **`FIXED_QUANTITY`**: Fixed share/contract quantity.
- **`FIXED_CAPITAL`**: Quantity = $\lfloor \text{Capital Amount} / P_{\text{reference}} \rfloor$.
- **`PERCENT_OF_CAPITAL`**: Quantity = $\lfloor (\text{Available Cash} \times (\text{Allocation \%} / 100)) / P_{\text{reference}} \rfloor$.
- All quantities are normalized to integer multiples of the instrument `lot_size`.
