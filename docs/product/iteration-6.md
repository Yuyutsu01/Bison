# Iteration 6: Portfolio & Risk Engine

## Overview
Iteration 6 delivers a production-grade **Portfolio & Risk Engine** for Bison. It consumes simulated `Execution` records from Iteration 5 and maintains exact financial state (Positions, Cash, Equity, Realized/Unrealized P&L, Exposure) and automated risk controls.

---

## 🏛️ Key Features Implemented

### 1. Portfolio Accounting & Position State
- **Source of Truth Principle**: Only Executions modify cash, position quantity, or average entry price.
- **Weighted Average Entry Pricing**: Recalculates average price when adding to positions.
- **Mark-to-Market Valuation**: Revalues unrealized P&L and total equity on every bar.
- **Accounting Invariants**: Guarantees $\text{Equity} = \text{Cash} + \text{Market Value}$ and $\text{Total PnL} = \text{Realized PnL} + \text{Unrealized PnL}$.

### 2. Position Sizing Engine
- Supports `FIXED_QUANTITY`, `FIXED_CAPITAL`, and `PERCENT_OF_CAPITAL`.
- Enforces instrument `lot_size` rounding.

### 3. Risk Engine & Intrabar/Gap Policies
- Automated risk rules: `StopLoss`, `Target`, `TrailingStop`, `MaxHoldingBars`, `EODExit`, `MaxSimultaneousPositions`.
- Non-mutation invariant: Risk rules emit exit orders, never mutating positions directly.
- **Intrabar Conflict Policy**: Conservative assumption (Stop-Loss wins) when both SL and Target are touched in the same bar.
- **Gap Execution Policy**: Fills at actual next available Open price when market gaps through Stop level.

### 4. Database Persistence & API Endpoints
- ORM Models: `PortfolioModel`, `PositionModel`, `PortfolioSnapshotModel`, `RiskEventModel`.
- Alembic Migration: `004_portfolio_and_risk.py`.
- REST endpoints:
  - `GET /api/v1/backtests/{id}/portfolio`
  - `GET /api/v1/backtests/{id}/positions`
  - `GET /api/v1/backtests/{id}/equity`
  - `GET /api/v1/backtests/{id}/risk-events`

---

## 🚀 Test Verification & Coverage

Full test suite passes with 45 unit, integration, zero look-ahead leakage, determinism, and accounting invariant tests:
- `test_portfolio_accounting.py`: Cash, equity, average entry price, realized/unrealized PnL.
- `test_position_sizing.py`: Sizing policies and lot size rounding.
- `test_risk_engine.py`: Stop-Loss, Target, Trailing Stop, Max Holding, EOD, Max Positions.
- `test_intrabar_and_gap.py`: Intrabar conflict policy & gap execution.
- `test_accounting_invariants.py`: Invariant verification (`Equity == Cash + Market Value`).
