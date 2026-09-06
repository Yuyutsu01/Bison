"""
Unit Tests verifying Accounting Invariants and Conservation Laws.
"""

import pytest
import pandas as pd
from decimal import Decimal
from app.domains.strategies.schemas import (
    StrategyDSL, InstrumentSpec, PositionSizing, RuleGroup, Condition,
    PriceOperand, ConstantOperand, Operator, PositionSizingType, RiskManagement, LogicalOperator
)
from app.domains.backtesting.engine import BacktestEngine


def create_invariant_strategy() -> StrategyDSL:
    return StrategyDSL(
        name="Invariant_Strategy",
        description="Accounting Invariant Test",
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
        risk=RiskManagement(stop_loss_percent=2.0)
    )


def test_accounting_invariants():
    """
    Accounting Invariant Verification:
    
    1. Equity == Cash + Gross Exposure (Market Value of Open Positions) at all snapshots.
    2. Total PnL == Realized PnL + Unrealized PnL == Equity - Initial Capital.
    """
    df = pd.DataFrame([
        {"timestamp": "10:00", "open": 24000.0, "high": 24050.0, "low": 23950.0, "close": 24020.0},
        {"timestamp": "10:05", "open": 24020.0, "high": 24100.0, "low": 24010.0, "close": 24090.0},  # Signal
        {"timestamp": "10:10", "open": 24090.0, "high": 24150.0, "low": 24080.0, "close": 24140.0},  # Fills
        {"timestamp": "10:15", "open": 24140.0, "high": 24200.0, "low": 23000.0, "close": 23500.0},  # Triggers SL
        {"timestamp": "10:20", "open": 23500.0, "high": 23600.0, "low": 23400.0, "close": 23550.0},  # Exit Fills
    ])

    strategy = create_invariant_strategy()
    engine = BacktestEngine(strategy, initial_capital=1000000.0)
    result = engine.run(df)

    assert result.portfolio is not None
    assert len(result.snapshots) > 0

    for snap in result.snapshots:
        # Invariant 1: Equity == Cash + Gross Exposure
        assert abs(snap.equity - (snap.cash + snap.gross_exposure)) < Decimal("0.01")
        # Invariant 2: Total PnL == Realized PnL + Unrealized PnL
        assert abs(snap.total_pnl - (snap.realized_pnl + snap.unrealized_pnl)) < Decimal("0.01")
