"""
Unit tests for Deterministic Run Identity Calculation.

Tests hash stability across identical configurations and sensitivity to parameter alterations.
"""

from app.domains.backtesting.configuration import BacktestConfiguration, RunIdentityCalculator, ENGINE_VERSION


def test_run_identity_deterministic_match():
    """Identical configurations must produce bit-exact identical run identities."""
    config1 = BacktestConfiguration(
        strategy_version_id="strat_ver_1",
        dataset_id="NIFTY_5M_2025",
        instrument_id="NIFTY50",
        initial_capital=100000.0,
        engine_version=ENGINE_VERSION
    )

    config2 = BacktestConfiguration(
        strategy_version_id="strat_ver_1",
        dataset_id="NIFTY_5M_2025",
        instrument_id="NIFTY50",
        initial_capital=100000.0,
        engine_version=ENGINE_VERSION
    )

    id1 = RunIdentityCalculator.calculate_run_identity(config1, strategy_dsl_version=1)
    id2 = RunIdentityCalculator.calculate_run_identity(config2, strategy_dsl_version=1)

    assert id1 == id2
    assert len(id1) == 64  # SHA-256 hex digest length


def test_run_identity_divergence_on_param_change():
    """Different capital or dataset must produce different run identities."""
    config_base = BacktestConfiguration(
        strategy_version_id="strat_ver_1",
        dataset_id="NIFTY_5M_2025",
        initial_capital=100000.0
    )

    config_different_cap = BacktestConfiguration(
        strategy_version_id="strat_ver_1",
        dataset_id="NIFTY_5M_2025",
        initial_capital=200000.0
    )

    id_base = RunIdentityCalculator.calculate_run_identity(config_base)
    id_diff = RunIdentityCalculator.calculate_run_identity(config_different_cap)

    assert id_base != id_diff
