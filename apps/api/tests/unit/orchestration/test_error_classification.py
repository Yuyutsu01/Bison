"""
Unit tests for structured domain errors and retry classification.
"""

from app.domains.backtesting.state_machine import (
    BacktestConfigurationError,
    DatasetInvalidError,
    ResultPersistenceError,
    is_retryable_error
)


def test_retryable_vs_non_retryable_errors():
    """Verify deterministic errors are not retryable while transient persistence errors are."""
    cfg_err = BacktestConfigurationError("Invalid strategy parameters")
    assert not is_retryable_error(cfg_err)

    dataset_err = DatasetInvalidError("Corrupted CSV structure")
    assert not is_retryable_error(dataset_err)

    persist_err = ResultPersistenceError("Temporary database deadlock")
    assert is_retryable_error(persist_err)


def test_generic_exception_retry_classification():
    """Uncaught runtime operational errors default to retryable."""
    generic_err = ConnectionResetError("Remote host closed connection")
    assert is_retryable_error(generic_err)
