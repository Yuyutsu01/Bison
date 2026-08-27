import pytest
import pandas as pd
from app.domains.strategies.schemas import (
    StrategyDSL, InstrumentSpec, RuleGroup, Condition, PriceOperand,
    IndicatorOperand, ConstantOperand, Operator, LogicalOperator
)
from app.domains.signals.engine import SignalEngine
from app.domains.signals.models import SignalType


@pytest.fixture
def crossover_sample_data():
    """Synthetic dataset designed for an EMA crossover signal."""
    timestamps = [f"2026-08-01 09:{i:02d}:00" for i in range(10, 60, 5)]
    # Downtrend then sharp uptrend
    closes = [100.0, 98.0, 96.0, 94.0, 92.0, 95.0, 105.0, 115.0, 125.0, 135.0]
    return pd.DataFrame({
        "timestamp": timestamps,
        "open": closes,
        "high": [c + 1.0 for c in closes],
        "low": [c - 1.0 for c in closes],
        "close": closes,
        "volume": [1000] * len(closes)
    })


def test_signal_engine_crossover_and_multiple_conditions(crossover_sample_data):
    """Tests EMA Crossover + RSI condition generating deterministic BUY signals."""
    strategy = StrategyDSL(
        name="Crossover + RSI Signal Test",
        instrument=InstrumentSpec(symbol="NIFTY"),
        entry=RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(
                    left=IndicatorOperand(name="EMA", parameters={"period": 2}),
                    operator=Operator.CROSS_ABOVE,
                    right=IndicatorOperand(name="EMA", parameters={"period": 4})
                ),
                Condition(
                    left=PriceOperand(field="close"),
                    operator=Operator.GREATER_THAN,
                    right=ConstantOperand(value=100.0)
                )
            ]
        )
    )

    engine = SignalEngine(strategy)
    signals = engine.generate_signals(crossover_sample_data)

    # Should generate BUY signal on the crossover bar where close > 100
    assert len(signals) > 0
    buy_signals = [s for s in signals if s.signal_type == SignalType.BUY]
    assert len(buy_signals) >= 1
    assert buy_signals[0].trigger_price > 100.0


def test_signal_engine_not_operator(crossover_sample_data):
    """Tests NOT logical operator in strategy signals."""
    strategy = StrategyDSL(
        name="NOT Operator Signal Test",
        instrument=InstrumentSpec(symbol="NIFTY"),
        entry=RuleGroup(
            operator=LogicalOperator.NOT,
            conditions=[
                Condition(
                    left=PriceOperand(field="close"),
                    operator=Operator.LESS_THAN,
                    right=ConstantOperand(value=120.0)
                )
            ]
        )
    )

    engine = SignalEngine(strategy)
    signals = engine.generate_signals(crossover_sample_data)

    # NOT (Close < 120) means Close >= 120
    assert len(signals) > 0
    for s in signals:
        assert s.trigger_price >= 120.0


def test_signal_engine_warmup_protection(crossover_sample_data):
    """Verifies that warm-up NaN values do NOT trigger false early signals."""
    strategy = StrategyDSL(
        name="Warm-up Protection Test",
        instrument=InstrumentSpec(symbol="NIFTY"),
        entry=RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(
                    left=IndicatorOperand(name="SMA", parameters={"period": 20}),
                    operator=Operator.GREATER_THAN,
                    right=ConstantOperand(value=1.0)
                )
            ]
        )
    )

    engine = SignalEngine(strategy)
    signals = engine.generate_signals(crossover_sample_data)

    # Sample dataset has only 10 rows, so 20-period SMA is NaN for all bars
    assert len(signals) == 0
