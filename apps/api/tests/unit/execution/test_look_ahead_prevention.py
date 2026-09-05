"""
Unit Tests Proving Zero Look-Ahead Bias Prevention in Order & Execution Simulator.
"""

import pytest
import pandas as pd
from decimal import Decimal
from app.domains.strategies.schemas import (
    StrategyDSL, InstrumentSpec, PositionSizing, RuleGroup, Condition,
    PriceOperand, ConstantOperand, Operator, PositionSizingType, RiskManagement, LogicalOperator
)
from app.domains.backtesting.engine import BacktestEngine


def create_test_strategy() -> StrategyDSL:
    return StrategyDSL(
        name="Close_Breakout",
        description="Test Strategy",
        version=1,
        instrument=InstrumentSpec(symbol="NIFTY"),
        timeframe="5m",
        position_sizing=PositionSizing(type=PositionSizingType.FIXED_QUANTITY, value=50.0),
        entry=RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(
                    left=PriceOperand(field="close"),
                    operator=Operator.GREATER_THAN,
                    right=ConstantOperand(value=24050.0)
                )
            ]
        ),
        exit=RuleGroup(operator=LogicalOperator.AND, conditions=[]),
        risk=RiskManagement()
    )


def test_order_generated_at_t_does_not_use_future_data():
    """
    Look-ahead Leakage Prevention Test:
    
    Given two market datasets A and B:
    - Dataset A and Dataset B have identical prices up to bar t.
    - Dataset B has drastically different future prices starting at bar t+1.
    
    Verified Invariants:
    1. The signal created at bar t Close is identical in both datasets.
    2. The order generated at bar t is identical in both datasets.
    3. The execution price at bar t+1 Open matches the specific dataset's bar t+1 Open.
    """
    df_base = pd.DataFrame([
        {"timestamp": "10:00", "open": 24000.0, "high": 24050.0, "low": 23950.0, "close": 24020.0},
        {"timestamp": "10:05", "open": 24020.0, "high": 24100.0, "low": 24010.0, "close": 24090.0},  # Close > 24050 -> Signal at 10:05 Close
        {"timestamp": "10:10", "open": 24090.0, "high": 24150.0, "low": 24080.0, "close": 24140.0},  # Fills at 10:10 Open
        {"timestamp": "10:15", "open": 24140.0, "high": 24200.0, "low": 24130.0, "close": 24190.0},
        {"timestamp": "10:20", "open": 24190.0, "high": 24250.0, "low": 24180.0, "close": 24240.0},
    ])

    df_dataset_a = df_base.copy()

    # Dataset B is modified starting at bar 2 (10:10)
    df_dataset_b = df_base.copy()
    df_dataset_b.loc[2, "open"] = 24500.0  # Completely different future open at 10:10
    df_dataset_b.loc[2, "close"] = 24550.0

    strategy = create_test_strategy()
    engine_a = BacktestEngine(strategy)
    engine_b = BacktestEngine(strategy)

    result_a = engine_a.run(df_dataset_a)
    result_b = engine_b.run(df_dataset_b)

    # Orders created at bar 1 (10:05) must be identical
    assert len(result_a.orders) > 0
    assert len(result_b.orders) > 0
    order_a = result_a.orders[0]
    order_b = result_b.orders[0]

    assert order_a.symbol == order_b.symbol
    assert order_a.created_at == "10:05"
    assert order_a.eligible_at == "10:10"
    assert order_b.created_at == "10:05"
    assert order_b.eligible_at == "10:10"

    # Executions fill on bar 2 (10:10) and reflect their respective future bar Open
    exec_a = result_a.executions[0]
    exec_b = result_b.executions[0]

    assert exec_a.timestamp == exec_b.timestamp == "10:10"
    assert exec_a.reference_price == Decimal("24090.0")
    assert exec_b.reference_price == Decimal("24500.0")
