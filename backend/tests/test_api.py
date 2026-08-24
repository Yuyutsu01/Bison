"""
API Route Integration Tests for FastAPI backend.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"


def test_get_available_symbols():
    response = client.get("/api/data/symbols")
    assert response.status_code == 200
    data = response.json()
    assert "symbols" in data
    assert len(data["symbols"]) > 0


def test_run_backtest_api():
    payload = {
        "strategy_config": {
            "name": "Test MA Crossover",
            "strategy_type": "moving_average_crossover",
            "symbol": "AAPL",
            "parameters": {"fast_period": 10, "slow_period": 30}
        },
        "initial_capital": 100000.0,
        "commission": 1.0,
        "slippage_bps": 5.0
    }

    response = client.post("/api/backtests", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "backtest_id" in data
    assert data["status"] == "COMPLETED"
    assert "metrics" in data
    assert "equity_curve" in data
    assert "trades" in data
