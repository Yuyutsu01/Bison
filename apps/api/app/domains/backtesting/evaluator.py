"""
Rule Evaluator Engine.

Evaluates Strategy DSL conditions against price and indicator time-series data at a specific bar index.
Handles price fields, indicator values, numerical constants, and cross-over operations.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np
from app.domains.strategies.schemas import (
    RuleGroup, Condition, Operand, OperandType, Operator, LogicalOperator
)


class RuleEvaluator:
    """Evaluates entry and exit conditions for a given bar index in a time-series DataFrame."""

    @classmethod
    def evaluate_rule_group(
        cls,
        rule_group: RuleGroup,
        df: pd.DataFrame,
        indicators: Dict[str, pd.Series],
        bar_idx: int
    ) -> bool:
        if not rule_group.conditions:
            return False

        results = [
            cls.evaluate_condition(cond, df, indicators, bar_idx)
            for cond in rule_group.conditions
        ]

        if rule_group.operator == LogicalOperator.AND:
            return all(results)
        elif rule_group.operator == LogicalOperator.OR:
            return any(results)
        elif rule_group.operator == LogicalOperator.NOT:
            return not any(results)
        return False

    @classmethod
    def evaluate_condition(
        cls,
        cond: Condition,
        df: pd.DataFrame,
        indicators: Dict[str, pd.Series],
        bar_idx: int
    ) -> bool:
        left_curr = cls._resolve_operand(cond.left, df, indicators, bar_idx)
        right_curr = cls._resolve_operand(cond.right, df, indicators, bar_idx)

        # Check for NaN / invalid indicator warm-up values
        if left_curr is None or right_curr is None or np.isnan(left_curr) or np.isnan(right_curr):
            return False

        op = cond.operator

        if op == Operator.GREATER_THAN:
            return left_curr > right_curr
        elif op == Operator.LESS_THAN:
            return left_curr < right_curr
        elif op == Operator.GREATER_THAN_EQUAL:
            return left_curr >= right_curr
        elif op == Operator.LESS_THAN_EQUAL:
            return left_curr <= right_curr
        elif op == Operator.EQUAL:
            return abs(left_curr - right_curr) < 1e-6
        elif op == Operator.NOT_EQUAL:
            return abs(left_curr - right_curr) >= 1e-6
        elif op in (Operator.CROSS_ABOVE, Operator.CROSS_BELOW):
            if bar_idx < 1:
                return False
            left_prev = cls._resolve_operand(cond.left, df, indicators, bar_idx - 1)
            right_prev = cls._resolve_operand(cond.right, df, indicators, bar_idx - 1)

            if left_prev is None or right_prev is None or np.isnan(left_prev) or np.isnan(right_prev):
                return False

            if op == Operator.CROSS_ABOVE:
                return (left_prev <= right_prev) and (left_curr > right_curr)
            elif op == Operator.CROSS_BELOW:
                return (left_prev >= right_prev) and (left_curr < right_curr)

        return False

    @classmethod
    def _resolve_operand(
        cls,
        operand: Operand,
        df: pd.DataFrame,
        indicators: Dict[str, pd.Series],
        bar_idx: int
    ) -> float:
        if operand.type == OperandType.CONSTANT:
            return float(operand.value)
        elif operand.type == OperandType.PRICE:
            col = operand.field.value.lower()
            if col in df.columns:
                return float(df[col].iloc[bar_idx])
            raise KeyError(f"Price field '{col}' not found in DataFrame.")
        elif operand.type == OperandType.INDICATOR:
            # Build unique key for pre-calculated indicator series
            key = cls._get_indicator_key(operand)
            if key in indicators:
                return float(indicators[key].iloc[bar_idx])
            raise KeyError(f"Pre-calculated indicator '{key}' not found.")
        return 0.0

    @classmethod
    def _get_indicator_key(cls, operand: Operand) -> str:
        name = operand.name.upper()
        params = getattr(operand, "parameters", {})
        param_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{name}_{param_str}" if param_str else name
