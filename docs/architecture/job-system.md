# Bison Architecture — Background Job & Worker System

## 1. Overview

The Bison Worker architecture executes computationally intensive backtests asynchronously. It uses Celery/Redis / Background task queues to decouple web request latency from financial simulations.

---

## 2. Worker Lifecycle

```text
1. Receive Job (backtest_run_id)
2. Transition State: QUEUED -> RUNNING (Record started_at)
3. Load Strategy Version DSL & Dataset
4. Run Simulation Loop via BacktestOrchestrator
5. Periodic Cancellation Check
6. Atomic Result Persistence (Trades, Orders, Executions, Costs, Portfolio, Snapshots, Risk Events)
7. Transition State: RUNNING -> COMPLETED (Record completed_at, metrics)
```

---

## 3. Failure Handling & Retry Policy

Structured errors are categorized into **Retryable** vs **Non-Retryable**:
- **Non-Retryable Errors** (Deterministic):
  - `BACKTEST_CONFIGURATION_INVALID`
  - `STRATEGY_INVALID`
  - `DATASET_INVALID`
  - `COST_PROFILE_NOT_FOUND`
- **Retryable Errors** (Transient Infrastructure):
  - Database connection timeouts / deadlocks
  - Redis connection interruptions

Jobs track `attempt_number` and `max_attempts` (default: 3).

---

## 4. Cancellation Protocol

- **QUEUED State**: When cancellation is requested on a queued job, status transitions immediately to `CANCELLED`.
- **RUNNING State**: When cancellation is requested on a running job, status transitions to `CANCELLING`. The simulation loop checks cancellation periodically and terminates gracefully at a safe bar boundary, transitioning to `CANCELLED`.
