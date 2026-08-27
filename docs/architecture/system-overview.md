# System Architecture Overview

## Architecture Goals

1. **Separation of Concerns**: Decouple strategy definitions, market data streaming, simulation execution, and UI visualization.
2. **Deterministic Backtesting Engine**: Completely isolated from database models, web framework dependencies, and frontend state.
3. **Asynchronous Execution**: Long-running simulations run in worker threads/processes decoupled from the REST API request-response loop.

## Monorepo Layout

- `apps/web`: Frontend application (Next.js 14, React Flow, Tailwind CSS, Recharts).
- `apps/api`: Backend application (FastAPI, SQLAlchemy 2.0, Alembic, Celery/Arq worker, Backtesting Engine).
- `data/fixtures`: Deterministic sample datasets for Indian indices (NIFTY, BANKNIFTY).
- `infra/docker`: Infrastructure configurations.
