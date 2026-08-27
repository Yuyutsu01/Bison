import pytest
import pandas as pd
from app.domains.strategies.schemas import (
    StrategyDSL, InstrumentSpec, RuleGroup, Condition, PriceOperand,
    ConstantOperand, Operator, LogicalOperator, RiskManagement, PositionSizing
)
from app.domains.backtesting.engine import BacktestEngine, CostModelConfig
from app.domains.backtesting.costs import SlippageType


def test_zero_lookahead_bias_execution():
    """
    Verifies that a signal generated on bar t (e.g. bar 1 close) MUST execute strictly on bar t+1 (bar 2 Open).
    Bar 1 Open = 100, Close = 105.
    Bar 2 Open = 110, Close = 115.
    If entry condition is Close > 102 (triggered at bar 1 close), entry price MUST be bar 2 Open (110 + slippage).
    """
    df = pd.DataFrame({
        "timestamp": ["2026-08-01 09:15:00", "2026-08-01 09:20:00", "2026-08-01 09:25:00"],
        "open": [100.0, 110.0, 120.0],
        "high": [106.0, 116.0, 125.0],
        "low": [99.0, 109.0, 119.0],
        "close": [105.0, 115.0, 124.0],
        "volume": [1000, 1000, 1000]
    })

    strategy = StrategyDSL(
        name="Zero Lookahead Test Strategy",
        instrument=InstrumentSpec(symbol="NIFTY"),
        entry=RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(
                    left=PriceOperand(field="close"),
                    operator=Operator.GREATER_THAN,
                    right=ConstantOperand(value=102.0)
                )
            ]
        ),
        position_sizing=PositionSizing(value=1.0)
    )

    cost_config = CostModelConfig(slippage_type=SlippageType.ZERO, brokerage_per_order=0.0, brokerage_percent_cap=0.0)
    engine = BacktestEngine(strategy=strategy, initial_capital=10000.0, cost_config=cost_config)

    res = engine.run(df)

    assert len(res.trades) == 1
    trade = res.trades[0]

    # Signal triggered at Bar 0 close (105.0 > 102.0)
    # Execution MUST happen on Bar 1 Open (110.0)
    assert trade.entry_time == "2026-08-01 09:20:00"
    assert trade.entry_price == 110.0
