"""
Unit tests for BacktestConfiguration validation.
"""

import pytest
from pydantic import ValidationError
from app.domains.backtesting.configuration import BacktestConfiguration


def test_valid_configuration():
    """Valid parameters instantiate BacktestConfiguration successfully."""
    config = BacktestConfiguration(
        strategy_version_id="ver_1",
        initial_capital=50000.0,
        slippage_value=0.5
    )
    assert config.strategy_version_id == "ver_1"
    assert config.initial_capital == 50000.0
    assert config.slippage_value == 0.5


def test_invalid_capital_rejected():
    """Initial capital <= 0 must fail validation."""
    with pytest.raises(ValidationError):
        BacktestConfiguration(
            strategy_version_id="ver_1",
            initial_capital=0.0
        )

    with pytest.raises(ValidationError):
        BacktestConfiguration(
            strategy_version_id="ver_1",
            initial_capital=-500.0
        )


def test_immutability_frozen():
    """Configuration attributes are immutable (frozen)."""
    config = BacktestConfiguration(strategy_version_id="ver_1")
    with pytest.raises(ValidationError):
        config.initial_capital = 200000.0
