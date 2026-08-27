# Walkthrough - Build Iteration 1: Indian Algorithmic Trading Platform (Bison)

We have successfully implemented **Build Iteration 1** of **Bison**, a production-grade algorithmic trading and backtesting platform built for Indian market traders (NIFTY, BANKNIFTY, and NSE/BSE Equities).

---

## 🏛️ Architecture & Accomplishments

### 1. Repository Structure (Monorepo)
```text
Bison/
├── apps/
│   ├── api/                   # Python FastAPI, SQLAlchemy 2.0, Pydantic, pytest
│   │   ├── app/
│   │   │   ├── main.py        # FastAPI server & CORS middleware
│   │   │   ├── core/          # Security, JWT tokens, logging
│   │   │   ├── db/            # Async SQLAlchemy engine & models
│   │   │   └── domains/       # Domain boundaries
│   │   │       ├── auth/      # User registration & JWT login
│   │   │       ├── strategies/# Formal Strategy DSL schemas & validator
│   │   │       ├── instruments/# NSE/BSE instrument metadata
│   │   │       ├── market_data/# OHLCV ingestion & data quality validator
│   │   │       ├── indicators/ # SMA, EMA, RSI, MACD, Bollinger Bands, ATR
│   │   │       ├── backtesting/# Zero look-ahead event-driven simulator & Indian friction model
│   │   │       └── jobs/      # Async background backtest job worker
│   │   └── tests/             # Pytest unit & API integration tests
│   │
│   └── web/                   # Next.js 14 TypeScript Frontend
│       ├── app/               # App Router pages (/login, /register, /builder, /backtests/[id])
│       ├── components/        # Navbar, VisualBuilder, PerformanceDashboard
│       ├── lib/               # Axios API client & TypeScript interfaces
│       └── globals.css        # Glassmorphic UI theme & Tailwind tokens
│
├── data/
│   └── fixtures/              # Deterministic market data fixtures (NIFTY 5m)
├── docs/                      # Architecture docs & ADRs
├── docker-compose.yml         # Full-stack containerization (PostgreSQL, Redis, API, Worker, Web)
├── Makefile                   # Developer convenience commands
└── README.md                  # Comprehensive documentation & roadmap
```

---

## ⚡ Core Domain Features Implemented

### 1. Strategy DSL & Validation Engine
- **Formal JSON Schema**: Typed definition for entry rules, exit rules, risk management (stop-loss, target, trailing stop, max holding bars, end-of-day exit), and position sizing (`FIXED_QUANTITY`, `PERCENT_OF_CAPITAL`).
- **Structured Error Diagnostics**: Validates indicator periods, parameter bounds, missing entry rules, and operand compatibility before saving or executing.

### 2. Zero Look-Ahead Bias Backtesting Engine
- **Bar $t+1$ Open Fill**: Orders generated at bar $t$ close execute strictly on bar $t+1$'s `Open` price.
- **Indian Market Statutory Costs**: Brokerage (₹20 cap), STT ($0.025\%$ intraday sell), Exchange charges ($0.00345\%$), SEBI turnover fees, Stamp duty ($0.003\%$ buy), GST ($18\%$), and basis-point slippage.

### 3. Web Dashboard & Trade Inspector
- **Visual Strategy Builder**: Interactive canvas to build logic conditions (`IF` ... `CROSS_ABOVE` / `GREATER_THAN` ... `THEN`).
- **Quantitative Analytics Dashboard**: Recharts portfolio mark-to-market equity curve, drawdown charts, financial metric summary cards (Sharpe ratio, max drawdown %, win rate %, profit factor, total return), and filterable trade logs table.
- **Trade Inspector Drawer**: Inspect entry/exit timestamps, executed prices, gross vs net P&L, friction breakdown, and pre-calculated indicator snapshot values.

---

## 🧪 Verification & Test Results

### Backend Test Suite (`pytest`)
All **13 unit, domain, and API integration tests** passed cleanly:
```text
tests/test_api.py::test_health_check PASSED
tests/test_api.py::test_ready_check PASSED
tests/test_api.py::test_list_instruments PASSED
tests/test_api.py::test_auth_and_strategy_workflow PASSED
tests/test_backtest_engine.py::test_zero_lookahead_bias_execution PASSED
tests/test_indicators.py::test_sma_calculation PASSED
tests/test_indicators.py::test_ema_calculation PASSED
tests/test_indicators.py::test_rsi_calculation PASSED
tests/test_indicators.py::test_bollinger_bands PASSED
tests/test_indicators.py::test_atr_calculation PASSED
tests/test_strategy_validator.py::test_valid_strategy_validation PASSED
tests/test_strategy_validator.py::test_invalid_strategy_validation_errors PASSED
tests/test_transaction_costs.py::test_indian_transaction_cost_breakdown PASSED

======================= 13 passed in 3.88s =======================
```

---

## 🚀 How to Run Locally

### 1. Backend Service
```bash
cd apps/api
python -m pip install -r requirements.txt
python -m pytest tests/ -v
uvicorn app.main:app --reload --port 8000
```
OpenAPI documentation will be available at `http://localhost:8000/docs`.

### 2. Frontend Web Application
```bash
cd apps/web
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

### 3. Docker Compose (Full Stack)
```bash
docker-compose up --build
```
