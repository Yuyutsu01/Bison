# Product Specification: Backtest Orchestration & Job Execution Engine

## 1. Overview
The Backtest Orchestration Engine coordinates the execution of historical simulations across all domain engines in Bison: Strategy DSL, Signal Engine, Order & Execution Simulator, Cost & Charges Engine, and Portfolio & Risk Engine. It provides deterministic run identity hashing, asynchronous queue-based execution, atomic persistence, real-time progress tracking, graceful cancellation, and comprehensive error classification.

---

## 2. Key User Capabilities

1. **Deterministic Run Submissions**
   - Traders submit backtest configurations (strategy, universe, date range, initial capital, execution model, slippage, brokerage config).
   - System computes a SHA-256 deterministic run identity hash for deduplication and auditability.
   - If an active identical backtest is running, the platform returns the existing active run ID rather than duplicating compute load.

2. **Asynchronous Execution & Progress Polling**
   - Fast, low-latency status polling endpoint (`/api/v1/backtests/{id}/status`) providing exact bar processing progress (`processed_bars / total_bars`) and estimated time remaining.
   - Decoupled API submission from worker execution to handle high-frequency bar data without HTTP timeouts.

3. **Graceful Cancellation**
   - Traders can cancel running or queued backtests at any point.
   - The engine checks cancellation tokens every batch of bars, cleanly rolling back or marking terminal states without partial corruption.

4. **Structured Error Diagnostics**
   - Failures categorize transparently into retryable transient errors (database locks, timeouts) vs. non-retryable domain errors (insufficient historical data, validation errors).
   - Detailed stack trace and error code presented in UI.

---

## 3. Product Architecture Workflow
```
[User / UI]
     │
     ▼ (POST /api/v1/backtests)
[FastAPI Route Layer] ──► [RunIdentityCalculator] ──► [Deduplication Check]
     │
     ▼
[PostgreSQL (CREATED / QUEUED)]
     │
     ▼ (BackgroundTasks / Celery Worker)
[BacktestStateMachine: RUNNING]
     │
     ▼
[BacktestOrchestrator]
     ├─► 1. Market Data Fetching & Verification
     ├─► 2. Indicator Warmup & Signal Evaluation
     ├─► 3. Next-Bar-Open Execution Simulation
     ├─► 4. Indian Statutory Cost Calculation
     ├─► 5. Portfolio Accounting & Risk Mutation
     └─► 6. Progress & Cancellation Callback
     │
     ▼ (Atomic DB Commit)
[PostgreSQL (COMPLETED)]
     ├─► Orders & Executions
     ├─► Transaction Costs & Net Cash Flows
     ├─► Positions, Portfolio Snapshots & Risk Events
     └─► Summary Metrics & Operational Telemetry
```
