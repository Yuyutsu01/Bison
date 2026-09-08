"""
Integration tests for End-to-End Determinism and Reproducibility.

Executes identical backtest configurations multiple times and verifies exact matching results.
"""

import pytest
import os
import pandas as pd
from app.domains.strategies.schemas import StrategyDSL
from app.domains.market_data.loader import MarketDataLoader
from app.domains.backtesting.configuration import BacktestConfiguration, ENGINE_VERSION
from app.domains.backtesting.orchestrator import BacktestOrchestrator


def test_orchestrator_deterministic_reproducibility():
    """Two backtests run with identical inputs must produce bit-exact identical quantitative outputs."""
    # 1. Load market data
    fixture_path = os.path.join("data", "fixtures", "nifty_5m.csv")
    if not os.path.exists(fixture_path):
        fixture_path = "../../data/fixtures/nifty_5m.csv"

    df, _ = MarketDataLoader.load_from_csv(fixture_path, "NIFTY")

    # 2. Build Strategy DSL
    strategy = StrategyDSL(
        name="Deterministic Test Strategy",
        instrument={"symbol": "NIFTY", "exchange": "NSE", "timeframe": "5m"},
        entry={
            "operator": "AND",
            "conditions": [
                {
                    "left": {"type": "indicator", "name": "EMA", "parameters": {"period": 20}},
                    "operator": "CROSS_ABOVE",
                    "right": {"type": "indicator", "name": "EMA", "parameters": {"period": 50}}
                }
            ]
        },
        risk={"stop_loss_percent": 1.0, "target_percent": 2.0},
        position_sizing={"type": "FIXED_QUANTITY", "value": 50}
    )

    # 3. Build Configuration
    config = BacktestConfiguration(
        strategy_version_id="ver_1",
        dataset_id="NIFTY_5M",
        instrument_id="NIFTY",
        initial_capital=100000.0,
        engine_version=ENGINE_VERSION
    )

    # 4. Run Backtest Run A
    run_a = BacktestOrchestrator.run_simulation(df=df, strategy=strategy, config=config)["result"]

    # 5. Run Backtest Run B
    run_b = BacktestOrchestrator.run_simulation(df=df, strategy=strategy, config=config)["result"]

    # 6. Verify Exact Equivalence
    assert run_a.final_capital == run_b.final_capital
    assert run_a.total_net_pnl == run_b.total_net_pnl
    assert run_a.total_trades == run_b.total_trades
    assert run_a.win_rate == run_b.win_rate
    assert run_a.sharpe_ratio == run_b.sharpe_ratio
    assert run_a.max_drawdown_percent == run_b.max_drawdown_percent
    assert len(run_a.trades) == len(run_b.trades)

    for ta, tb in zip(run_a.trades, run_b.trades):
        assert ta.trade_id == tb.trade_id
        assert ta.entry_price == tb.entry_price
        assert ta.exit_price == tb.exit_price
        assert ta.net_pnl == tb.net_pnl
        assert ta.total_costs == tb.total_costs
