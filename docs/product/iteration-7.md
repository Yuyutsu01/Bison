# Bison — Iteration 7 Product Documentation

## Feature Overview: Indian Transaction Cost & Cost Engine

Iteration 7 equips Bison with a production-ready **Transaction Cost Engine** tailored specifically for Indian financial markets (NSE/BSE).

### Key Features

1. **Realistic Indian Market Costs**: Calculates Brokerage, STT, Exchange Turnover Fees, SEBI Fees, Stamp Duty, and 18% GST.
2. **Effective-Date Profile Versioning**: Supports versioned fee schedules with `effective_from` and `effective_to` date bounds to handle historical regulatory tax revisions cleanly.
3. **Legal Tax Base Compliance**: Correctly computes 18% GST only on Brokerage + Exchange Fees + SEBI Fees, explicitly excluding STT and Stamp Duty.
4. **Exact Decimal Accounting**: Uses Python `Decimal` with `ROUND_HALF_UP` to prevent floating-point drift in portfolio cash balance and net P&L calculations.
5. **Full Database Audit Trail**: Every execution records an itemized cost row in the `transaction_costs` PostgreSQL table.
6. **REST API & Dashboard Visibility**: Exposes cost profiles and backtest transaction cost breakdowns via REST API and visualizes total transaction friction in the Web UI dashboard.
