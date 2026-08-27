"""
Strategy Validator Module.

Performs domain-level validation of StrategyDSL objects to ensure correctness before execution.
Returns detailed, user-friendly error diagnostic reports.
"""

from typing import List, Dict, Any
from app.domains.strategies.schemas import (
    StrategyDSL, OperandType, IndicatorOperand, Condition
)

SUPPORTED_INDICATORS = {
    "SMA": ["period"],
    "EMA": ["period"],
    "RSI": ["period"],
    "MACD": ["fast_period", "slow_period", "signal_period"],
    "BB": ["period", "std_dev"],
    "ATR": ["period"]
}


class StrategyValidationError(Exception):
    """Raised when strategy validation fails with structured errors."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class StrategyValidator:
    """Validates strategy schema rules, indicator parameters, and risk management settings."""

    @classmethod
    def validate(cls, dsl: StrategyDSL) -> List[str]:
        errors: List[str] = []

        # 1. Validate Entry Conditions
        if not dsl.entry.conditions:
            errors.append("Strategy must have at least one entry condition.")
        else:
            for idx, cond in enumerate(dsl.entry.conditions, 1):
                cls._validate_condition(cond, f"Entry Condition #{idx}", errors)

        # 2. Validate Exit Conditions
        for idx, cond in enumerate(dsl.exit.conditions, 1):
            cls._validate_condition(cond, f"Exit Condition #{idx}", errors)

        # 3. Validate Risk Settings
        if dsl.risk.stop_loss_percent is not None and dsl.risk.stop_loss_percent <= 0:
            errors.append("Stop loss percentage must be strictly greater than 0.")

        if dsl.risk.target_percent is not None and dsl.risk.target_percent <= 0:
            errors.append("Target percentage must be strictly greater than 0.")

        if dsl.risk.trailing_stop_percent is not None and dsl.risk.trailing_stop_percent <= 0:
            errors.append("Trailing stop percentage must be strictly greater than 0.")

        # 4. Validate Position Sizing
        if dsl.position_sizing.value <= 0:
            errors.append("Position sizing value must be strictly greater than 0.")

        return errors

    @classmethod
    def _validate_condition(cls, cond: Condition, prefix: str, errors: List[str]) -> None:
        cls._validate_operand(cond.left, f"{prefix} (Left Operand)", errors)
        cls._validate_operand(cond.right, f"{prefix} (Right Operand)", errors)

    @classmethod
    def _validate_operand(cls, operand: Any, label: str, errors: List[str]) -> None:
        if operand.type == OperandType.INDICATOR:
            indicator_name = getattr(operand, "name", "").upper()
            if indicator_name not in SUPPORTED_INDICATORS:
                errors.append(f"{label}: Indicator '{indicator_name}' is not supported. Supported indicators: {list(SUPPORTED_INDICATORS.keys())}.")
                return

            params = getattr(operand, "parameters", {})
            required_params = SUPPORTED_INDICATORS[indicator_name]

            for param in required_params:
                if param not in params:
                    errors.append(f"{label}: Indicator '{indicator_name}' is missing parameter '{param}'.")
                else:
                    val = params[param]
                    if param in ["period", "fast_period", "slow_period", "signal_period"]:
                        if not isinstance(val, int) or val <= 0:
                            errors.append(f"{label}: Indicator '{indicator_name}' parameter '{param}' must be a positive integer > 0.")
                    elif param == "std_dev":
                        if not isinstance(val, (int, float)) or val <= 0:
                            errors.append(f"{label}: Indicator '{indicator_name}' parameter 'std_dev' must be a positive number > 0.")
