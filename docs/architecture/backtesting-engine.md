# Backtesting Engine Architecture

## Core Execution Semantics & Zero Look-Ahead Bias

The backtesting engine is designed as an event-driven chronological simulator.

### Timeline Mechanics
1. **Bar $t$ Close**: At bar $t$, indicators are calculated using price data up to bar $t$ close (`Open_t`, `High_t`, `Low_t`, `Close_t`, `Volume_t`).
2. **Strategy Evaluation**: Entry and exit rules are evaluated against bar $t$ indicator values.
3. **Signal Generation**: If rules pass, a `Signal` is emitted with signal time $t$.
4. **Order Generation**: The `Signal` is converted into an `Order` (BUY/SELL) with order time $t$.
5. **Execution ($t+1$ Open)**: The order is simulated for fill strictly on bar $t+1$'s `Open_{t+1}` price (plus slippage & transaction costs).

### Indian Cost Model Accounting
For each executed trade, transaction friction is calculated:
- **Brokerage**: Flat ₹20 per trade or 0.03% (whichever is lower).
- **STT (Securities Transaction Tax)**: 0.025% on sell side (intraday) / 0.1% on buy+sell (delivery).
- **Exchange Turnover Charge**: 0.00345% (NSE).
- **GST**: 18% on (Brokerage + Exchange Charges).
- **SEBI Charges**: ₹10 per crore (0.0001%).
- **Stamp Duty**: 0.003% on buy side.
- **Slippage**: Fixed basis-points or fixed rupee offset.
