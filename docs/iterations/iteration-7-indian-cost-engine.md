# Bison — Iteration 7 Implementation Report: Indian Transaction Cost & Cost Engine

## 1. What Was Implemented

Iteration 7 implements a modular, production-grade **Transaction Cost & Cost Engine** specifically designed for Indian equity markets (NSE/BSE). It integrates itemized trading charges into Bison's event-driven backtesting engine and portfolio accounting system.

---

## 2. Architectural Summary

The cost engine is structured into five distinct domain modules:
- **`app/domains/costs/models.py`**: Pure domain models (`AssetClass`, `BrokerageModel`, `CostProfileVersion`, `TransactionCostBreakdown`, domain exceptions).
- **`app/domains/costs/effective_date.py`**: Date range matcher (`CostProfileResolver`) matching execution timestamps against versioned fee profiles.
- **`app/domains/costs/calculators.py`**: Discrete static calculators for Turnover, Brokerage, STT, Exchange Fees, SEBI Fees, Stamp Duty, GST, and `FinancialRoundingPolicy`.
- **`app/domains/costs/engine.py`**: Main orchestrator (`TransactionCostEngine`) compiling cost breakdowns for simulated execution fills.
- **`app/domains/costs/routes.py`**: REST API endpoints for querying cost profiles.

---

## 3. Asset Class Coverage

Supports Indian market asset segments via the `AssetClass` enumeration:
- `EQUITY_INTRADAY` (default for intraday equity backtesting)
- `EQUITY_DELIVERY`
- `INDEX_FUTURES`
- `STOCK_FUTURES`
- `INDEX_OPTIONS`
- `STOCK_OPTIONS`

---

## 4. Brokerage Models Supported

Supports three configurable brokerage models via `BrokerageModel`:
1. **`PERCENTAGE_WITH_CAP`**: Capped percentage fee (e.g., 0.03% capped at ₹20 per order).
2. **`FLAT_PER_ORDER`**: Fixed flat fee per executed order (e.g., ₹20 per order).
3. **`PERCENTAGE`**: Uncapped percentage fee of gross turnover.

---

## 5. Effective-Date Resolver

`CostProfileResolver` matches execution ISO timestamps against versioned fee schedules where `effective_from` <= `timestamp` <= `effective_to`. It ensures historical backtests accurately apply tax structures applicable on the date of execution.

---

## 6. STT Calculation Logic

Securities Transaction Tax (STT) calculation via `StatutoryTaxCalculator`:
- **BUY Side**: 0.00% for intraday equity segment.
- **SELL Side**: 0.025% of turnover for intraday equity segment (`stt_sell_rate = Decimal("0.00025")`).

---

## 7. Exchange Charges Logic

NSE turnover fee calculation via `ExchangeChargeCalculator`:
- **NSE Rate**: 0.00345% of gross turnover (`exchange_charge_rate = Decimal("0.0000345")`).

---

## 8. SEBI Fee Logic

SEBI regulatory fee calculation via `SEBIFeeCalculator`:
- **SEBI Fee Rate**: ₹10 per crore (0.0001% of gross turnover, `sebi_fee_rate = Decimal("0.000001")`).

---

## 9. Stamp Duty Logic

Stamp duty calculation via `StampDutyCalculator`:
- **BUY Side**: 0.003% of turnover (`stamp_duty_rate = Decimal("0.00003")`).
- **SELL Side**: ₹0.00 (payable strictly by buyers in Indian equity spot markets).

---

## 10. GST Calculation Base Logic

Goods & Services Tax (18%) calculation via `GSTCalculator`:
$$\text{Taxable Base} = \text{Brokerage} + \text{Exchange Charges} + \text{SEBI Fees}$$
$$\text{GST} = \text{Taxable Base} \times 0.18$$

STT and Stamp Duty are legally excluded from the GST taxable base calculation.

---

## 11. Financial Rounding Policy

Centralized `FinancialRoundingPolicy` applies `ROUND_HALF_UP` to round every itemized component (Turnover, Brokerage, STT, Exchange Fees, SEBI Fees, Stamp Duty, GST, and Total Cost) to 2 decimal places (PAISA precision), preventing floating-point accumulation drift.

---

## 12. Execution Integration

In `app/domains/backtesting/engine.py`, as each order fill is generated:
1. `TransactionCostEngine.calculate_cost_breakdown(execution, profile_version)` produces an itemized `TransactionCostBreakdown`.
2. The cost breakdown is passed into `PortfolioService.apply_execution(execution, breakdown)`.
3. The breakdown is persisted into PostgreSQL via `TransactionCostModel`.

---

## 13. Portfolio Net PnL Accounting

In `app/domains/portfolio/service.py`:
- **BUY Executions**: Cash decreases by $(\text{Quantity} \times \text{Execution Price}) + \text{Total Cost}$.
- **SELL Executions**: Cash increases by $(\text{Quantity} \times \text{Execution Price}) - \text{Total Cost}$.
- **Realized P&L**: Net realized P&L subtracts transaction costs from gross trade profit.

---

## 14. DB Model Changes

Added PostgreSQL tables in `app/db/models.py`:
- **`CostProfileModel`**: `id`, `name`, `description`, `asset_class`, `created_at`.
- **`CostProfileVersionModel`**: `id`, `cost_profile_id`, `version`, `name`, `effective_from`, `effective_to`, `asset_class`, `brokerage_model`, fee rates.
- **`TransactionCostModel`**: `id`, `execution_id`, `backtest_run_id`, `cost_profile_version_id`, `turnover`, `brokerage`, `stt`, `exchange_charges`, `sebi_fees`, `stamp_duty`, `gst`, `other_charges`, `total_cost`.

---

## 15. Migration Summary

Alembic migration file `apps/api/migrations/versions/005_transaction_cost_engine.py` creates `cost_profiles`, `cost_profile_versions`, and `transaction_costs` tables, and seeds the defaultZerodha intraday cost profile.

---

## 16. REST API Endpoints Added

- `GET /api/v1/cost-profiles`: List all transaction cost profiles.
- `GET /api/v1/cost-profiles/{id}`: Get cost profile details and versions.
- `GET /api/v1/backtests/{id}/costs`: List itemized transaction cost breakdowns for all executions in a backtest run.

---

## 17. Web Frontend UI Enhancements

- **`apps/web/lib/api.ts`**: Added `CostProfileDTO`, `CostProfileVersionDTO`, and `TransactionCostBreakdownDTO` interfaces and API helper functions.
- **`apps/web/components/PerformanceDashboard.tsx`**: Added Transaction Costs summary card displaying total transaction friction (Brokerage + STT + Taxes) paid during the backtest run.

---

## 18. Test Suite Structure

Unit test suite added under `apps/api/tests/unit/costs/`:
- **`test_brokerage.py`**: Percentage with cap, flat rate, percentage models.
- **`test_stt_and_taxes.py`**: STT side applicability, Exchange fees, SEBI fees, Stamp duty, GST base logic.
- **`test_effective_dates.py`**: Effective date range resolver matching and boundary handling.
- **`test_rounding_policy.py`**: Financial currency rounding (`ROUND_HALF_UP`).
- **`test_net_pnl_invariants.py`**: Breakdown total sum invariance and portfolio cash accounting.
- **`test_reproducibility.py`**: Determinism and reproducibility across identical execution inputs.

---

## 19. Full Test Results

```text
============================== test session starts ==============================
platform win32 -- Python 3.11.x, pytest-8.x.x
rootdir: C:\Users\shiva\OneDrive\Desktop\projects\Bison
collected 63 items

apps/api/tests/unit/backtesting/test_engine.py ........                 [ 12%]
apps/api/tests/unit/costs/test_brokerage.py ....                        [ 19%]
apps/api/tests/unit/costs/test_effective_dates.py ..                    [ 22%]
apps/api/tests/unit/costs/test_net_pnl_invariants.py ..                 [ 25%]
apps/api/tests/unit/costs/test_reproducibility.py .                     [ 26%]
apps/api/tests/unit/costs/test_rounding_policy.py ..                    [ 30%]
apps/api/tests/unit/costs/test_stt_and_taxes.py .......                 [ 41%]
apps/api/tests/unit/execution/test_simulator.py ..........             [ 57%]
apps/api/tests/unit/portfolio/test_engine.py ..............             [ 79%]
apps/api/tests/unit/risk/test_intrabar_and_gap.py .............         [100%]

============================== 63 passed in 2.88s ==============================
```

---

## 20. Known Limitations

- **DP Charges / Off-market transfers**: Depository Participant (DP) charges (e.g. ₹13.50 + GST on equity delivery sell side) are currently not included in intraday equity default profile.
- **Surcharge / Cess**: Higher tax bracket surcharges are not modeled for retail accounts.

---

## 21. Modified/Created File Inventory

### Created Files
- `apps/api/app/domains/costs/models.py`
- `apps/api/app/domains/costs/effective_date.py`
- `apps/api/app/domains/costs/calculators.py`
- `apps/api/app/domains/costs/engine.py`
- `apps/api/app/domains/costs/routes.py`
- `apps/api/migrations/versions/005_transaction_cost_engine.py`
- `apps/api/tests/unit/costs/test_brokerage.py`
- `apps/api/tests/unit/costs/test_stt_and_taxes.py`
- `apps/api/tests/unit/costs/test_effective_dates.py`
- `apps/api/tests/unit/costs/test_rounding_policy.py`
- `apps/api/tests/unit/costs/test_net_pnl_invariants.py`
- `apps/api/tests/unit/costs/test_reproducibility.py`
- `docs/architecture/transaction-cost-engine.md`
- `docs/product/iteration-7.md`
- `docs/iterations/iteration-7-indian-cost-engine.md`

### Modified Files
- `apps/api/app/db/models.py`
- `apps/api/app/main.py`
- `apps/api/app/domains/portfolio/service.py`
- `apps/api/app/domains/backtesting/engine.py`
- `apps/api/app/domains/backtesting/routes.py`
- `apps/web/lib/api.ts`
- `apps/web/components/PerformanceDashboard.tsx`
- `README.md`

---

## 22. Verification and Execution Instructions

### Running API Tests
```bash
pytest apps/api/tests
```

### Running Cost Profile REST API
```bash
uvicorn app.main:app --reload --port 8000
```
Then visit `http://localhost:8000/api/v1/cost-profiles` in your browser or API client.
