"""
Integration tests for Backtest Cancellation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.main import app
from app.db.models import BacktestRunModel, StrategyVersionModel

client = TestClient(app)
sync_engine = create_engine("sqlite:///./bison.db")


@pytest.fixture
def auth_user():
    """Registers and authenticates a test user."""
    import uuid
    unique_email = f"cancel_user_{uuid.uuid4().hex[:8]}@bison.com"
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "Password123!",
        "full_name": "Cancel Tester"
    })
    data = reg_resp.json()
    token = data["access_token"]
    user_id = data["user_id"]
    return {"headers": {"Authorization": f"Bearer {token}"}, "user_id": user_id}


@pytest.fixture
def strategy_id(auth_user):
    """Creates a valid strategy."""
    strat_resp = client.post("/api/v1/strategies", headers=auth_user["headers"], json={
        "name": "NIFTY Cancel Strategy",
        "instrument": {"symbol": "NIFTY", "exchange": "NSE", "timeframe": "5m"},
        "entry": {
            "operator": "AND",
            "conditions": [
                {
                    "left": {"type": "indicator", "name": "EMA", "parameters": {"period": 20}},
                    "operator": "CROSS_ABOVE",
                    "right": {"type": "indicator", "name": "EMA", "parameters": {"period": 50}}
                }
            ]
        },
        "risk": {"stop_loss_percent": 1.0, "target_percent": 2.0},
        "position_sizing": {"type": "FIXED_QUANTITY", "value": 50}
    })
    return strat_resp.json()["id"]


def test_cancel_queued_backtest(auth_user, strategy_id):
    """Cancelling a QUEUED backtest transitions it to CANCELLED immediately."""
    with Session(sync_engine) as db:
        ver = db.query(StrategyVersionModel).filter_by(strategy_id=strategy_id).first()
        queued_run = BacktestRunModel(
            user_id=auth_user["user_id"],
            strategy_version_id=ver.id,
            initial_capital=100000.0,
            status="QUEUED"
        )
        db.add(queued_run)
        db.commit()
        queued_id = queued_run.id

    # Request cancellation
    cancel_resp = client.post(f"/api/v1/backtests/{queued_id}/cancel", headers=auth_user["headers"])
    assert cancel_resp.status_code == 200
    cancel_data = cancel_resp.json()
    assert cancel_data["status"] == "CANCELLED"
    assert cancel_data["error_code"] == "JOB_CANCELLED"


def test_cancel_terminal_backtest_rejected(auth_user, strategy_id):
    """Attempting to cancel an already completed backtest returns HTTP 400."""
    with Session(sync_engine) as db:
        ver = db.query(StrategyVersionModel).filter_by(strategy_id=strategy_id).first()
        completed_run = BacktestRunModel(
            user_id=auth_user["user_id"],
            strategy_version_id=ver.id,
            initial_capital=100000.0,
            status="COMPLETED"
        )
        db.add(completed_run)
        db.commit()
        completed_id = completed_run.id

    # Cancel a terminal run
    retry_cancel = client.post(f"/api/v1/backtests/{completed_id}/cancel", headers=auth_user["headers"])
    assert retry_cancel.status_code == 400
