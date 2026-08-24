# Institutional Algorithmic Trading Platform – Phase 1

Phase 1 deliverable for an event-driven algorithmic trading platform built with a **Python FastAPI** backend engine and a **Next.js 14 TypeScript** glassmorphic web dashboard.

---

## 🌟 Key Features

1. **Event-Driven Core Engine**: Synchronous event bus emitting `MarketDataEvent`, `SignalEvent`, `OrderEvent`, `FillEvent`, and `PortfolioEvent`.
2. **Zero Look-Ahead Bias**: Orders triggered on bar $t$ fill strictly on bar $t+1$'s Open price.
3. **Realistic Market Friction**: Models per-trade commission fees ($) and basis-point slippage (bps).
4. **No-Code Visual Strategy Builder**: Interactive canvas using React Flow (`@xyflow/react`) to visually configure moving average crossover rules and backtest parameters.
5. **Quantitative Analytics Dashboard**:
   - Interactive Recharts Equity Curve (mark-to-market portfolio value).
   - Key Metrics Cards: Total Return (%), Annualized Return (%), Sharpe Ratio, Max Drawdown (%), Win Rate (%), Profit Factor, Total Trade Count.
   - Filterable Trade Log Table with status badges and CSV export.

---

## 📁 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── core/           # Event definitions & EventBus
│   │   ├── strategies/     # Strategy interface & MovingAverageCrossover
│   │   ├── data/           # CSV/Parquet ingestion, replay iterator & sample data
│   │   ├── backtest/       # Backtest engine, OMS portfolio tracker & metrics
│   │   ├── api/            # FastAPI schemas & REST endpoints
│   │   └── main.py         # Server entry point with CORS middleware
│   ├── tests/              # Pytest unit & integration test suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── layout.tsx      # Root glassmorphism layout with sticky Navbar
│   │   ├── page.tsx        # Overview & 1-click preset launcher
│   │   ├── builder/        # Visual strategy builder (dynamic import ssr: false)
│   │   └── backtests/[id]/ # Backtest analytics dashboard
│   ├── components/         # Navbar, VisualBuilder, PerformanceDashboard, MetricCard
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🚀 Quick Start (Local Setup)

### 1. Run Backend Service (Python FastAPI)

```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
python -m pytest tests/              # Run unit & API test suite
uvicorn app.main:app --reload --port 8000
```

FastAPI OpenAPI interactive docs will be live at `http://localhost:8000/docs`.

### 2. Run Frontend Dashboard (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 🐳 Docker Deployment

To launch both backend and frontend in containers:

```bash
docker-compose up --build
```
