"""
Unit Tests for Risk Engine (Stop-Loss, Target, Trailing Stop, Max Holding, EOD, Max Positions).
"""

import pytest
from decimal import Decimal
from app.domains.strategies.schemas import RiskManagement
from app.domains.portfolio.models import Portfolio, Position, PositionSide
from app.domains.risk.models import RiskEventType
from app.domains.risk.engine import RiskEngine


def test_stop_loss_trigger():
    portfolio = Portfolio(id="P1", backtest_run_id="B1", initial_capital=Decimal("100000"), cash=Decimal("100000"), equity=Decimal("100000"))
    pos = Position(
        id="POS_1",
        portfolio_id="P1",
        instrument_id="NIFTY",
        symbol="NIFTY",
        side=PositionSide.LONG,
        quantity=Decimal("50"),
        average_entry_price=Decimal("100.0"),
        current_price=Decimal("100.0")
    )
    risk_config = RiskManagement(stop_loss_percent=1.0)  # SL at 99.0

    bar = {"open": 100.0, "high": 101.0, "low": 98.5, "close": 99.0, "timestamp": "10:05"}
    risk_event = RiskEngine.evaluate_position_risk(portfolio, pos, bar, risk_config)

    assert risk_event is not None
    assert risk_event.event_type == RiskEventType.STOP_LOSS_TRIGGERED
    assert risk_event.trigger_price == Decimal("99.0")


def test_target_trigger():
    portfolio = Portfolio(id="P1", backtest_run_id="B1", initial_capital=Decimal("100000"), cash=Decimal("100000"), equity=Decimal("100000"))
    pos = Position(
        id="POS_2",
        portfolio_id="P1",
        instrument_id="NIFTY",
        symbol="NIFTY",
        side=PositionSide.LONG,
        quantity=Decimal("50"),
        average_entry_price=Decimal("100.0"),
        current_price=Decimal("100.0")
    )
    risk_config = RiskManagement(target_percent=2.0)  # Target at 102.0

    bar = {"open": 100.0, "high": 102.5, "low": 99.5, "close": 102.0, "timestamp": "10:05"}
    risk_event = RiskEngine.evaluate_position_risk(portfolio, pos, bar, risk_config)

    assert risk_event is not None
    assert risk_event.event_type == RiskEventType.TARGET_TRIGGERED
    assert risk_event.trigger_price == Decimal("102.0")


def test_max_simultaneous_positions_rejection():
    portfolio = Portfolio(id="P1", backtest_run_id="B1", initial_capital=Decimal("100000"), cash=Decimal("100000"), equity=Decimal("100000"))
    pos1 = Position(id="POS_A", portfolio_id="P1", instrument_id="NIFTY", symbol="NIFTY", side=PositionSide.LONG, quantity=Decimal("50"), average_entry_price=Decimal("100"), current_price=Decimal("100"))
    portfolio.positions["NIFTY"] = pos1

    decision = RiskEngine.evaluate_entry_risk(portfolio, max_simultaneous_positions=1)
    assert decision.allowed is False
    assert decision.action == "REJECT_ENTRY"
    assert decision.reason == "MAX_POSITIONS_REACHED"
