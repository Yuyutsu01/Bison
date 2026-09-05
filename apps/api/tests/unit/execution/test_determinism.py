"""
Unit Tests for End-to-End Simulation Determinism.
"""

import pytest
import pandas as pd
from decimal import Decimal
from app.domains.strategies.schemas import (
    StrategyDSL, InstrumentSpec, PositionSizing, RuleGroup, Condition,
    IndicatorOperand, Operator, PositionSizingType, RiskManagement, LogicalOperator
)
from app.domains.backtesting.engine import BacktestEngine


def create_determinism_strategy() -> StrategyDSL:
    return StrategyDSL(
        name="SMA_Cross_Det",
        description="Determinism Strategy",
        version=1,
        instrument=InstrumentSpec(symbol="NIFTY"),
        timeframe="5m",
        position_sizing=PositionSizing(type=PositionSizingType.FIXED_QUANTITY, value=50.0),
        entry=RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(
                    left=IndicatorOperand(name="SMA", parameters={"period": 2}),
                    operator=Operator.GREATER_THAN,
                    right=IndicatorOperand(name="SMA", parameters={"period": 5})
                )
            ]
        ),
        exit=RuleGroup(operator=LogicalOperator.AND, conditions=[]),
        risk=RiskManagement()
    )


def test_double_run_determinism():
    """
    Determinism Test:
    
    Given identical strategy, market data, and execution policy,
    two independent backtest runs must produce identical trades, orders,
    executions, equity points, and summary metrics.
    """
    df = pd.DataFrame([
        {"timestamp": "10:00", "open": 24000.0, "high": 24050.0, "low": 23950.0, "close": 24020.0},
        {"timestamp": "10:05", "open": 24020.0, "high": 24100.0, "low": 24010.0, "close": 24090.0},
        {"timestamp": "10:10", "open": 24090.0, "high": 24150.0, "low": 24080.0, "close": 24140.0},
        {"timestamp": "10:15", "open": 24140.0, "high": 24200.0, "low": 24130.0, "close": 24190.0},
        {"timestamp": "10:20", "open": 24190.0, "high": 24250.0, "low": 24180.0, "close": 24240.0},
    ])

    strategy = create_determinism_strategy()

    engine1 = BacktestEngine(strategy)
    engine2 = BacktestEngine(strategy)

    res1 = engine1.run(df)
    res2 = engine2.run(df)

    assert res1.total_trades == res2.total_trades
    assert res1.final_capital == res2.final_capital
    assert res1.total_net_pnl == res2.total_net_pnl
    assert len(res1.orders) == len(res2.orders)
    assert len(res1.executions) == len(res2.executions)

    for o1, o2 in zip(res1.orders, res2.orders):
        assert o1.symbol == o2.symbol
        assert o1.side == o2.side
        assert o1.quantity == o2.quantity
        assert o1.created_at == o2.created_at
        assert o1.idempotency_key == o2.idempotency_key

    for e1, e2 in zip(res1.executions, res2.executions):
        assert e1.symbol == e2.symbol
        assert e1.timestamp == e2.timestamp
        assert e1.reference_price == e2.reference_price
        assert e1.execution_price == e2.execution_price
        assert e1.slippage == e2.slippage
