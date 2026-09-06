"""
Unit Tests for Intrabar Conflict and Gap Execution Policies in RiskEngine.
"""

import pytest
from decimal import Decimal
from app.domains.strategies.schemas import RiskManagement
from app.domains.portfolio.models import Portfolio, Position, PositionSide
from app.domains.risk.models import RiskEventType
from app.domains.risk.engine import RiskEngine


def test_intrabar_conflict_adverse_event_policy():
    """
    Intrabar Conflict Policy Test:
    
    Given:
    - Entry = 100.0, Stop = 95.0 (5%), Target = 105.0 (5%).
    - Bar: Open = 100.0, High = 106.0 (touches target), Low = 94.0 (touches stop).
    
    Invariants:
    - The conservative policy MUST assume the adverse event (Stop-Loss) occurred first.
    - Risk event type MUST be STOP_LOSS_TRIGGERED.
    """
    portfolio = Portfolio(id="P1", backtest_run_id="B1", initial_capital=Decimal("100000"), cash=Decimal("100000"), equity=Decimal("100000"))
    pos = Position(
        id="POS_CONFLICT",
        portfolio_id="P1",
        instrument_id="NIFTY",
        symbol="NIFTY",
        side=PositionSide.LONG,
        quantity=Decimal("50"),
        average_entry_price=Decimal("100.0"),
        current_price=Decimal("100.0")
    )
    risk_config = RiskManagement(stop_loss_percent=5.0, target_percent=5.0)

    bar = {"open": 100.0, "high": 106.0, "low": 94.0, "close": 102.0, "timestamp": "10:05"}
    risk_event = RiskEngine.evaluate_position_risk(portfolio, pos, bar, risk_config)

    assert risk_event is not None
    assert risk_event.event_type == RiskEventType.STOP_LOSS_TRIGGERED
    assert risk_event.metadata.get("intrabar_conflict") is True


def test_gap_through_stop_loss():
    """
    Gap Execution Policy Test:
    
    Given:
    - Entry = 100.0, Stop = 95.0.
    - Bar opens at 90.0 (gaps down below Stop).
    
    Invariants:
    - The system must not claim a fill at impossible ₹95.0.
    - Trigger price MUST equal actual next available executable price (₹90.0).
    """
    portfolio = Portfolio(id="P1", backtest_run_id="B1", initial_capital=Decimal("100000"), cash=Decimal("100000"), equity=Decimal("100000"))
    pos = Position(
        id="POS_GAP",
        portfolio_id="P1",
        instrument_id="NIFTY",
        symbol="NIFTY",
        side=PositionSide.LONG,
        quantity=Decimal("50"),
        average_entry_price=Decimal("100.0"),
        current_price=Decimal("100.0")
    )
    risk_config = RiskManagement(stop_loss_percent=5.0)  # SL at 95.0

    bar = {"open": 90.0, "high": 92.0, "low": 88.0, "close": 91.0, "timestamp": "10:05"}
    risk_event = RiskEngine.evaluate_position_risk(portfolio, pos, bar, risk_config)

    assert risk_event is not None
    assert risk_event.event_type == RiskEventType.STOP_LOSS_TRIGGERED
    assert risk_event.trigger_price == Decimal("90.0")
