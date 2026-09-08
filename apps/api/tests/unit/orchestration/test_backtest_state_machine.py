"""
Unit tests for Backtest Lifecycle State Machine.

Tests legal state transitions, terminal states, and rejection of invalid state transitions.
"""

import pytest
from app.domains.backtesting.state_machine import (
    BacktestStatus,
    BacktestStateMachine,
    InvalidStateTransitionError
)


def test_legal_state_transitions():
    """Verify standard happy path lifecycle: CREATED -> QUEUED -> RUNNING -> COMPLETED."""
    assert BacktestStateMachine.can_transition(BacktestStatus.CREATED.value, BacktestStatus.QUEUED.value)
    assert BacktestStateMachine.can_transition(BacktestStatus.QUEUED.value, BacktestStatus.RUNNING.value)
    assert BacktestStateMachine.can_transition(BacktestStatus.RUNNING.value, BacktestStatus.COMPLETED.value)


def test_cancellation_transitions():
    """Verify cancellation from QUEUED and RUNNING states."""
    # From QUEUED directly to CANCELLED
    assert BacktestStateMachine.can_transition(BacktestStatus.QUEUED.value, BacktestStatus.CANCELLED.value)
    # From RUNNING to CANCELLING or CANCELLED
    assert BacktestStateMachine.can_transition(BacktestStatus.RUNNING.value, BacktestStatus.CANCELLING.value)
    assert BacktestStateMachine.can_transition(BacktestStatus.CANCELLING.value, BacktestStatus.CANCELLED.value)


def test_failure_and_retry_transitions():
    """Verify RUNNING -> FAILED, and FAILED -> QUEUED for retries."""
    assert BacktestStateMachine.can_transition(BacktestStatus.RUNNING.value, BacktestStatus.FAILED.value)
    assert BacktestStateMachine.can_transition(BacktestStatus.FAILED.value, BacktestStatus.QUEUED.value)


def test_illegal_state_transitions():
    """Verify invalid state transitions raise InvalidStateTransitionError."""
    # Cannot jump from CREATED directly to COMPLETED
    assert not BacktestStateMachine.can_transition(BacktestStatus.CREATED.value, BacktestStatus.COMPLETED.value)
    with pytest.raises(InvalidStateTransitionError):
        BacktestStateMachine.validate_transition(BacktestStatus.CREATED.value, BacktestStatus.COMPLETED.value)

    # Terminal COMPLETED cannot transition to RUNNING
    assert not BacktestStateMachine.can_transition(BacktestStatus.COMPLETED.value, BacktestStatus.RUNNING.value)
    with pytest.raises(InvalidStateTransitionError):
        BacktestStateMachine.validate_transition(BacktestStatus.COMPLETED.value, BacktestStatus.RUNNING.value)

    # CANCELLED cannot transition to COMPLETED
    assert not BacktestStateMachine.can_transition(BacktestStatus.CANCELLED.value, BacktestStatus.COMPLETED.value)
    with pytest.raises(InvalidStateTransitionError):
        BacktestStateMachine.validate_transition(BacktestStatus.CANCELLED.value, BacktestStatus.COMPLETED.value)
