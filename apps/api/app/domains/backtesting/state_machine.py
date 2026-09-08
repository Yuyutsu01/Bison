"""
Backtest Lifecycle State Machine and Structured Domain Errors.

Defines explicit job lifecycle states, valid state transition rules,
structured domain error models, and retry policy classifications.
"""

from enum import Enum
from typing import Set, Dict


class BacktestStatus(str, Enum):
    """Explicit lifecycle states for a backtest job."""
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    CANCELLING = "CANCELLING"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BacktestStateMachine:
    """
    Enforces valid lifecycle transitions and prevents illegal state mutations.
    """

    # Legal transitions mapping: Current Status -> Set of Allowed Next Statuses
    _TRANSITIONS: Dict[BacktestStatus, Set[BacktestStatus]] = {
        BacktestStatus.CREATED: {BacktestStatus.QUEUED, BacktestStatus.FAILED, BacktestStatus.CANCELLED},
        BacktestStatus.QUEUED: {BacktestStatus.RUNNING, BacktestStatus.CANCELLED, BacktestStatus.FAILED},
        BacktestStatus.RUNNING: {BacktestStatus.COMPLETED, BacktestStatus.FAILED, BacktestStatus.CANCELLING, BacktestStatus.CANCELLED},
        BacktestStatus.CANCELLING: {BacktestStatus.CANCELLED, BacktestStatus.FAILED},
        BacktestStatus.CANCELLED: set(),    # Terminal state
        BacktestStatus.COMPLETED: set(),    # Terminal state
        BacktestStatus.FAILED: {BacktestStatus.QUEUED}  # Retry can re-queue
    }

    @classmethod
    def can_transition(cls, current: str, target: str) -> bool:
        """Returns True if transition from current to target is legally permitted."""
        try:
            curr_enum = BacktestStatus(current)
            target_enum = BacktestStatus(target)
            return target_enum in cls._TRANSITIONS.get(curr_enum, set())
        except ValueError:
            return False

    @classmethod
    def validate_transition(cls, current: str, target: str) -> None:
        """
        Validates transition and raises InvalidStateTransitionError if illegal.
        """
        if not cls.can_transition(current, target):
            raise InvalidStateTransitionError(
                f"Illegal state transition from '{current}' to '{target}'."
            )


# ==============================================================================
# Structured Domain Exceptions
# ==============================================================================

class BacktestDomainError(Exception):
    """Base domain exception for all backtest orchestration errors."""
    error_code: str = "BACKTEST_DOMAIN_ERROR"
    is_retryable: bool = False

    def __init__(self, message: str, error_code: str = None, is_retryable: bool = None):
        super().__init__(message)
        if error_code is not None:
            self.error_code = error_code
        if is_retryable is not None:
            self.is_retryable = is_retryable


class InvalidStateTransitionError(BacktestDomainError):
    error_code = "INVALID_STATE_TRANSITION"
    is_retryable = False


class BacktestConfigurationError(BacktestDomainError):
    error_code = "BACKTEST_CONFIGURATION_INVALID"
    is_retryable = False


class StrategyNotFoundError(BacktestDomainError):
    error_code = "STRATEGY_NOT_FOUND"
    is_retryable = False


class StrategyInvalidError(BacktestDomainError):
    error_code = "STRATEGY_INVALID"
    is_retryable = False


class DatasetNotFoundError(BacktestDomainError):
    error_code = "DATASET_NOT_FOUND"
    is_retryable = False


class DatasetInvalidError(BacktestDomainError):
    error_code = "DATASET_INVALID"
    is_retryable = False


class InstrumentMismatchError(BacktestDomainError):
    error_code = "INSTRUMENT_MISMATCH"
    is_retryable = False


class UnsupportedTimeframeError(BacktestDomainError):
    error_code = "UNSUPPORTED_TIMEFRAME"
    is_retryable = False


class CostProfileNotFoundError(BacktestDomainError):
    error_code = "COST_PROFILE_NOT_FOUND"
    is_retryable = False


class EngineExecutionError(BacktestDomainError):
    error_code = "ENGINE_EXECUTION_ERROR"
    is_retryable = False


class ResultPersistenceError(BacktestDomainError):
    error_code = "RESULT_PERSISTENCE_ERROR"
    is_retryable = True  # Transient DB connection errors may be retried


class JobCancelledError(BacktestDomainError):
    error_code = "JOB_CANCELLED"
    is_retryable = False


class WorkerTimeoutError(BacktestDomainError):
    error_code = "WORKER_TIMEOUT"
    is_retryable = False


def is_retryable_error(exc: Exception) -> bool:
    """Determines whether a failure is retryable by the worker retry policy."""
    if isinstance(exc, BacktestDomainError):
        return exc.is_retryable
    # Default: non-domain uncaught exceptions (e.g. operational DB disconnects) are transient
    return True
