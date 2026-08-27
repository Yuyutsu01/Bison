import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from app.main import app
from app.db.base import Base

# Ensure SQLite tables exist for testing in a fresh clean state
engine = create_engine("sqlite:///./bison.db")
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_check():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_list_instruments():
    response = client.get("/api/v1/instruments")
    assert response.status_code == 200
    instruments = response.json()
    assert len(instruments) > 0
    symbols = [inst["symbol"] for inst in instruments]
    assert "NIFTY" in symbols
    assert "BANKNIFTY" in symbols


def test_auth_and_strategy_workflow():
    # 1. Register User
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": "trader@bison.com",
        "password": "SecurePassword123!",
        "full_name": "Quant Trader"
    })
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Validate Strategy DSL
    val_resp = client.post("/api/v1/strategies/validate", json={
        "name": "NIFTY EMA Strategy",
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
    assert val_resp.status_code == 200
    assert val_resp.json()["is_valid"] is True

    # 3. Create Strategy
    strat_resp = client.post("/api/v1/strategies", headers=headers, json={
        "name": "NIFTY EMA Strategy",
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
    assert strat_resp.status_code == 201
    strategy_id = strat_resp.json()["id"]

    # 4. Trigger Backtest Run
    bt_resp = client.post("/api/v1/backtests", headers=headers, json={
        "strategy_id": strategy_id,
        "initial_capital": 100000.0
    })
    assert bt_resp.status_code == 202
    backtest_id = bt_resp.json()["id"]

    # 5. Fetch Backtest Details
    get_bt_resp = client.get(f"/api/v1/backtests/{backtest_id}", headers=headers)
    assert get_bt_resp.status_code == 200
    assert get_bt_resp.json()["id"] == backtest_id
