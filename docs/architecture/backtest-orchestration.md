# Bison Architecture — Backtest Orchestration & Job Execution Engine

## 1. Executive Summary

The **Backtest Orchestration Engine** coordinates the full spectrum of quantitative trading domains into an asynchronous, observable, and deterministic execution workflow. It decouples high-throughput API endpoints from CPU-intensive simulation tasks while providing atomic result persistence and strict idempotency protection.

```text
                    ┌──────────────────┐
                    │    Next.js UI    │
                    └────────┬─────────┘
                             │ (Submit / Poll Status / Cancel)
                             ▼
                    ┌──────────────────┐
                    │ FastAPI Gateway  │
                    └────────┬─────────┘
                             │ (Validate & Enqueue)
                             ▼
                    ┌──────────────────┐
                    │   Job Queue      │
                    │ Redis + Worker   │
                    └────────┬─────────┘
                             │
                             ▼
                 ┌────────────────────────┐
                 │ Backtest Orchestrator  │
                 └────────────┬───────────┘
                              │
             ┌────────────────┼────────────────┐
             ▼                ▼                ▼
       Market Data       Strategy Engine    Cost Engine
             │                │                │
             └────────┬───────┴────────────────┘
                      ▼
               Orchestrated Event Loop:
               Bar t -> Fill t-1 Orders -> Costs -> Portfolio -> MTM -> Risk -> Signals -> Orders t
                      ↓
               Atomic Result Persistence -> Mark COMPLETED
```

---

## 2. Immutable Configuration & Run Identity

A backtest execution is completely defined by its immutable `BacktestConfiguration`:
- `strategy_version_id`
- `dataset_id`
- `instrument_id`
- `timeframe`
- `start_datetime`, `end_datetime`
- `initial_capital`
- `execution_policy`
- `slippage_type`, `slippage_value`
- `cost_profile_version_id`
- `position_sizing`, `risk_management`
- `engine_version` (`bison-backtest-engine-v0.8.0`)

### Deterministic Run Identity Hashing
The `RunIdentityCalculator` serializes the canonical configuration, strategy DSL version, dataset version hash, cost profile version, and engine version into a normalized JSON string and computes its SHA-256 digest:
$$\text{Run Identity} = \text{SHA256}(\text{CanonicalJSON}(\text{Config} + \text{StrategyVer} + \text{DatasetHash} + \text{CostProfileVer} + \text{EngineVer}))$$

---

## 3. Backtest Lifecycle State Machine

Explicit lifecycle states:
```text
CREATED  ──>  QUEUED  ──>  RUNNING  ──>  COMPLETED
   │             │            │
   └──> CANCELLED/FAILED      ├──> CANCELLING ──> CANCELLED
                              └──> FAILED ──(Retry)──> QUEUED
```

- **Transitions Enforced**: `BacktestStateMachine.validate_transition(current, target)` prevents invalid mutations (e.g., terminal `COMPLETED` cannot transition to `RUNNING`).

---

## 4. Simulation Coordination & Warmup

The `BacktestOrchestrator` implements the zero look-ahead bias event loop:
1. **Dataset Integrity Check**: Verifies sorting, absence of duplicate bars, and required OHLCV columns.
2. **Warmup Calculation**: Inspects strategy condition indicators and determines maximum lookback period needed.
3. **Execution Fills**: Fills pending orders from bar $t-1$ strictly at bar $t$ Open.
4. **Cost Application**: Calculates itemized charges via `TransactionCostEngine`.
5. **Portfolio & Risk Mutation**: Updates positions, marks to market, and evaluates risk triggers.
6. **Strategy Evaluation**: Evaluates entry/exit rule trees and queues new orders for bar $t+1$.
7. **Atomic Persistence**: Persists all Trades, Orders, Executions, Transaction Costs, Snapshots, and Risk Events in a single transaction.
