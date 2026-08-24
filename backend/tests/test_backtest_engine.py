"""
Integration unit tests for BacktestEngine & Performance Analytics.
"""

from datetime import datetime
import pandas as pd
import numpy as np
import pytest

from app.backtest.engine import BacktestEngine
from app.data.sample_data import generate_sample_data


def test_backtest_engine_run():
    df = generate_sample_data("AAPL", num_days=300, start_price=100.0)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    engine = BacktestEngine(
        symbol="AAPL",
        df_data=df,
        strategy_name="moving_average_crossover",
        strategy_config={"fast_period": 10, "slow_period": 30},
        initial_capital=100000.0,
        commission=1.0,
        slippage_bps=5.0
    )

    results = engine.run()

    assert results["status"] == "COMPLETED"
    assert "metrics" in results
    assert "equity_curve" in results
    assert "trades" in results
    
    metrics = results["metrics"]
    assert "total_return_pct" in metrics
    assert "sharpe_ratio" in metrics
    assert "max_drawdown_pct" in metrics
    assert "win_rate_pct" in metrics
    assert len(results["equity_curve"]) > 0
