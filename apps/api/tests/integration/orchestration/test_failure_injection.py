"""
Integration tests for Failure Injection and Corrupt Dataset Handling.
"""

import pytest
import pandas as pd
from app.domains.strategies.schemas import StrategyDSL
from app.domains.backtesting.configuration import BacktestConfiguration
from app.domains.backtesting.orchestrator import BacktestOrchestrator
from app.domains.backtesting.state_machine import DatasetInvalidError


@pytest.fixture
def sample_strategy():
    return StrategyDSL(
        name="Failure Test Strategy",
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


def test_empty_dataset_fails(sample_strategy):
    """Empty DataFrame fails dataset validation with DatasetInvalidError."""
    empty_df = pd.DataFrame()
    config = BacktestConfiguration(strategy_version_id="ver_1")

    with pytest.raises(DatasetInvalidError):
        BacktestOrchestrator.run_simulation(df=empty_df, strategy=sample_strategy, config=config)


def test_missing_ohlcv_columns_fails(sample_strategy):
    """DataFrame missing required OHLCV columns raises DatasetInvalidError."""
    bad_df = pd.DataFrame({
        "open": [100.0, 101.0, 102.0],
        "close": [101.0, 102.0, 103.0]
        # missing high, low
    })
    config = BacktestConfiguration(strategy_version_id="ver_1")

    with pytest.raises(DatasetInvalidError):
        BacktestOrchestrator.run_simulation(df=bad_df, strategy=sample_strategy, config=config)


def test_unsorted_timestamps_fails(sample_strategy):
    """Non-chronologically sorted bars fail validation."""
    unsorted_df = pd.DataFrame({
        "timestamp": ["2025-01-01 10:00", "2025-01-01 09:00", "2025-01-01 11:00"],
        "open": [100.0, 101.0, 102.0],
        "high": [105.0, 106.0, 107.0],
        "low": [99.0, 100.0, 101.0],
        "close": [104.0, 105.0, 106.0]
    })
    config = BacktestConfiguration(strategy_version_id="ver_1")

    with pytest.raises(DatasetInvalidError):
        BacktestOrchestrator.run_simulation(df=unsorted_df, strategy=sample_strategy, config=config)
