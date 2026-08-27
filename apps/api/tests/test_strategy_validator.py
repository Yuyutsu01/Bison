import pytest
from app.domains.strategies.schemas import (
    StrategyDSL, InstrumentSpec, RuleGroup, Condition, PriceOperand,
    IndicatorOperand, ConstantOperand, Operator, LogicalOperator, RiskManagement, PositionSizing
)
from app.domains.strategies.validator import StrategyValidator


def test_valid_strategy_validation():
    valid_dsl = StrategyDSL(
        name="EMA Crossover Strategy",
        instrument=InstrumentSpec(symbol="NIFTY"),
        entry=RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(
                    left=IndicatorOperand(name="EMA", parameters={"period": 20}),
                    operator=Operator.CROSS_ABOVE,
                    right=IndicatorOperand(name="EMA", parameters={"period": 50})
                )
            ]
        ),
        risk=RiskManagement(stop_loss_percent=1.0, target_percent=2.0),
        position_sizing=PositionSizing(value=10.0)
    )

    errors = StrategyValidator.validate(valid_dsl)
    assert len(errors) == 0


def test_invalid_strategy_validation_errors():
    invalid_dsl = StrategyDSL(
        name="Broken Strategy",
        instrument=InstrumentSpec(symbol="NIFTY"),
        entry=RuleGroup(
            operator=LogicalOperator.AND,
            conditions=[
                Condition(
                    left=IndicatorOperand(name="INVALID_INDICATOR", parameters={}),
                    operator=Operator.GREATER_THAN,
                    right=ConstantOperand(value=50.0)
                )
            ]
        ),
        risk=RiskManagement(stop_loss_percent=-1.0),
        position_sizing=PositionSizing(value=0.0)
    )

    errors = StrategyValidator.validate(invalid_dsl)
    assert len(errors) > 0
    assert any("not supported" in err for err in errors)
    assert any("Stop loss percentage" in err for err in errors)
    assert any("Position sizing value" in err for err in errors)
