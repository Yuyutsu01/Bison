# Iteration 6: Portfolio & Risk Engine — Implementation Report

## 1. Portfolio Architecture

The Portfolio domain is implemented in [`app/domains/portfolio/`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/portfolio/):

- **[`models.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/portfolio/models.py)**: Defines `Portfolio` entity containing `initial_capital`, `cash`, `equity`, `realized_pnl`, `unrealized_pnl`, `total_pnl`, `gross_exposure`, `net_exposure`, `positions` dictionary, and `processed_execution_ids` set.
- **[`service.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/portfolio/service.py)**: `PortfolioService` handles execution application, average entry pricing, realized/unrealized P&L calculations, and bar-by-bar mark-to-market revaluation.

---

## 2. Position Architecture

- **`Position` Entity** ([`app/domains/portfolio/models.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/portfolio/models.py)):
  - Fields: `id`, `portfolio_id`, `instrument_id`, `symbol`, `side` (`LONG` / `SHORT`), `quantity`, `average_entry_price`, `current_price`, `realized_pnl`, `unrealized_pnl`, `opened_at`, `last_updated_at`, `holding_bars`, `status` (`OPEN` / `CLOSED`), `highest_price_since_entry`, `lowest_price_since_entry`.
  - Properties: `market_value = quantity * current_price`.
  - Methods: `update_market_price(price: Decimal)` recalculates unrealized P&L and updates trailing price trackers.

---

## 3. Cash / Accounting Model

- **Source of Truth Principle**: **Only Executions modify portfolio cash and position sizes**. Signals or orders never alter portfolio balances directly.
- **BUY / Long Entry**:
  - Cash decreases: $\text{Cash}_{\text{new}} = \text{Cash}_{\text{old}} - (\text{Quantity} \times \text{Execution Price})$
- **SELL / Long Exit**:
  - Cash increases: $\text{Cash}_{\text{new}} = \text{Cash}_{\text{old}} + (\text{Quantity}_{\text{closed}} \times \text{Execution Price})$
- **Accounting Invariants**:
  - $\text{Equity} = \text{Cash} + \text{Gross Exposure}$
  - $\text{Total PnL} = \text{Realized PnL} + \text{Unrealized PnL} = \text{Equity} - \text{Initial Capital}$

---

## 4. P&L Formulas

- **Weighted Average Entry Price** (upon position additions):
  $$\text{Average Entry Price} = \frac{(Q_{\text{old}} \times P_{\text{old}}) + (Q_{\text{exec}} \times P_{\text{exec}})}{Q_{\text{old}} + Q_{\text{exec}}}$$
- **Long Unrealized P&L**: $(P_{\text{current}} - P_{\text{avg\_entry}}) \times Q$
- **Long Realized P&L**: $(P_{\text{exit}} - P_{\text{avg\_entry}}) \times Q_{\text{closed}}$
- **Short Unrealized P&L**: $(P_{\text{avg\_entry}} - P_{\text{current}}) \times Q$
- **Short Realized P&L**: $(P_{\text{avg\_entry}} - P_{\text{exit}}) \times Q_{\text{closed}}$

---

## 5. Position-Sizing Implementation

Implemented in [`app/domains/portfolio/sizing.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/portfolio/sizing.py):

- **`FIXED_QUANTITY`**: Returns fixed quantity configured in strategy DSL.
- **`FIXED_CAPITAL`**: Quantity = $\lfloor \text{Capital Amount} / P_{\text{reference}} \rfloor$.
- **`PERCENT_OF_CAPITAL`**: Quantity = $\lfloor (\text{Available Cash} \times (\text{Allocation \%} / 100)) / P_{\text{reference}} \rfloor$.
- Normalizes quantity to instrument `lot_size` multiples and validates quantity $> 0$ and capital availability.

---

## 6. Risk-Engine Architecture

Implemented in [`app/domains/risk/engine.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/risk/engine.py):

```text
Market Bar t
    ↓
Portfolio State
    ↓
RiskEngine Evaluation
    ↓
RiskEvent Logged
    ↓
Exit Signal -> Order Engine (Never direct position mutation)
```

- **Non-Mutation Invariant**: Risk rules emit exit orders; positions are mutated only when simulated execution fills arrive.

---

## 7. Stop-Loss Implementation

- Long SL level: $P_{\text{sl}} = P_{\text{entry}} \times (1 - \text{sl\_pct} / 100)$.
- Trigger condition: `bar_low <= sl_price`.
- Emits `RiskEventType.STOP_LOSS_TRIGGERED` event.

---

## 8. Target Implementation

- Long Target level: $P_{\text{target}} = P_{\text{entry}} \times (1 + \text{target\_pct} / 100)$.
- Trigger condition: `bar_high >= target_price`.
- Emits `RiskEventType.TARGET_TRIGGERED` event.

---

## 9. Trailing-Stop Implementation

- Long Trailing Stop level: $P_{\text{trail}} = P_{\text{highest\_since\_entry}} \times (1 - \text{trailing\_pct} / 100)$.
- Trigger condition: `bar_low <= trail_stop_level`.
- `highest_price_since_entry` updates strictly in favorable direction and never loosens.
- Emits `RiskEventType.TRAILING_STOP_TRIGGERED` event.

---

## 10. Maximum-Holding Implementation

- Increments `position.holding_bars` on every bar mark-to-market.
- Trigger condition: `position.holding_bars >= max_holding_bars`.
- Emits `RiskEventType.MAX_HOLDING_TRIGGERED` event.

---

## 11. EOD Implementation

- Trigger condition: `risk_config.end_of_day_exit` and `is_final_bar`.
- Emits `RiskEventType.EOD_EXIT_TRIGGERED` event.

---

## 12. Intrabar Policy

- **Intrabar Conflict Policy**: When both Stop-Loss and Target thresholds are breached in the same bar, conservative policy assumes the **adverse event (Stop-Loss)** occurred first.
- Logged with `intrabar_conflict: True` metadata.

---

## 13. Gap Policy

- **Gap Execution Policy**: If market opens beyond a Stop-Loss threshold (e.g. Stop at ₹95, Next Open at ₹90), trigger price is set to `bar_open` (₹90), preventing fake fills at impossible stop prices.

---

## 14. Database Changes

- **[`app/db/models.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/db/models.py)**: Added `PortfolioModel`, `PositionModel`, `PortfolioSnapshotModel`, `RiskEventModel`.
- **Migration**: [`004_portfolio_and_risk.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/migrations/versions/004_portfolio_and_risk.py) creates tables with foreign keys and cascade delete rules.

---

## 15. API Changes

Updated [`apps/api/app/domains/backtesting/routes.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/backtesting/routes.py):
- `GET /api/v1/backtests/{id}/portfolio`
- `GET /api/v1/backtests/{id}/positions`
- `GET /api/v1/backtests/{id}/equity`
- `GET /api/v1/backtests/{id}/risk-events`

---

## 16. Frontend Changes

- Updated [`apps/web/lib/api.ts`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/web/lib/api.ts) with `PortfolioDTO`, `PositionDTO`, and `RiskEventDTO`.
- Display portfolio summary metrics card and active positions table in backtest results view.

---

## 17. Tests Created

1. **[`test_portfolio_accounting.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/portfolio/test_portfolio_accounting.py)**: Cash, equity, average entry price, realized/unrealized PnL.
2. **[`test_position_sizing.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/portfolio/test_position_sizing.py)**: Position sizing policies and lot size rounding.
3. **[`test_risk_engine.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/risk/test_risk_engine.py)**: Stop-Loss, Target, Trailing Stop, Max Holding, EOD, Max Positions.
4. **[`test_intrabar_and_gap.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/risk/test_intrabar_and_gap.py)**: Intrabar conflict policy & gap execution.
5. **[`test_accounting_invariants.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/portfolio/test_accounting_invariants.py)**: Accounting invariant verification (`Equity == Cash + Market Value`).

---

## 18. Test Results

Running `pytest apps/api/tests`:

```text
======================== 45 passed in 2.84s ========================
```

All 45 unit, integration, zero look-ahead leakage, determinism, and accounting invariant tests pass cleanly.

---

## 19. Known Limitations

- **Margin Engine**: Complex margin maintenance/call mechanics for short options or leveraged futures are deferred to later iterations.
- **Broker Sync**: Real-time broker account synchronization belongs to paper/live trading iterations.

---

## 20. Files / Modules Created or Modified

### Created Modules
- [`apps/api/app/domains/portfolio/models.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/portfolio/models.py)
- [`apps/api/app/domains/portfolio/service.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/portfolio/service.py)
- [`apps/api/app/domains/portfolio/sizing.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/portfolio/sizing.py)
- [`apps/api/app/domains/risk/models.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/risk/models.py)
- [`apps/api/app/domains/risk/engine.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/risk/engine.py)
- [`apps/api/migrations/versions/004_portfolio_and_risk.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/migrations/versions/004_portfolio_and_risk.py)
- [`apps/api/tests/unit/portfolio/test_portfolio_accounting.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/portfolio/test_portfolio_accounting.py)
- [`apps/api/tests/unit/portfolio/test_position_sizing.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/portfolio/test_position_sizing.py)
- [`apps/api/tests/unit/risk/test_risk_engine.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/risk/test_risk_engine.py)
- [`apps/api/tests/unit/risk/test_intrabar_and_gap.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/risk/test_intrabar_and_gap.py)
- [`apps/api/tests/unit/portfolio/test_accounting_invariants.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/tests/unit/portfolio/test_accounting_invariants.py)
- [`docs/architecture/portfolio-engine.md`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/docs/architecture/portfolio-engine.md)
- [`docs/architecture/risk-engine.md`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/docs/architecture/risk-engine.md)
- [`docs/product/iteration-6.md`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/docs/product/iteration-6.md)

### Modified Files
- [`apps/api/app/db/models.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/db/models.py)
- [`apps/api/app/domains/backtesting/engine.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/backtesting/engine.py)
- [`apps/api/app/domains/backtesting/routes.py`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/api/app/domains/backtesting/routes.py)
- [`apps/web/lib/api.ts`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/apps/web/lib/api.ts)
- [`README.md`](file:///C:/Users/shiva/OneDrive/Desktop/projects/Bison/README.md)

---

## 21. Instructions for Running the Implementation

### Running Unit & Accounting Invariant Tests
```bash
pytest apps/api/tests
```

### Running Database Migrations
```bash
cd apps/api
alembic upgrade head
```

---

## 22. Recommended Scope for Iteration 7

### Iteration 7: Transaction Cost Engine & Multi-Asset Friction Accounting
- **Statutory Fee Breakdown**: Modular tax & fee accounting for Indian exchanges (Brokerage, STT, Exchange Turnover Fees, SEBI Charges, GST, Stamp Duty).
- **Multi-Asset Cost Rules**: Support equity delivery vs intraday vs futures & options statutory fee structure.
- **Cost Impact Analytics**: Detailed reporting of net P&L vs gross P&L friction drag.
