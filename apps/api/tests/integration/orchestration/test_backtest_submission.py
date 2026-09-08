"""
Integration tests for Backtest Submission, Validation, Idempotency, and Duplicate Protection.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.main import app
from app.db.models import BacktestRunModel, StrategyVersionModel, StrategyModel

client = TestClient(app)
sync_engine = create_engine("sqlite:///./bison.db")


@pytest.fixture
def auth_user():
    """Registers and authenticates a test user, returning headers and user_id."""
    import uuid
    unique_email = f"user_{uuid.uuid4().hex[:8]}@bison.com"
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "Password123!",
        "full_name": "Backtest Orchestration Tester"
    })
    data = reg_resp.json()
    token = data["access_token"]
    user_id = data["user_id"]
    return {"headers": {"Authorization": f"Bearer {token}"}, "user_id": user_id}


@pytest.fixture
def sample_strategy(auth_user):
    """Creates a sample strategy for backtest submission."""
    strat_resp = client.post("/api/v1/strategies", headers=auth_user["headers"], json={
        "name": "NIFTY EMA Crossover",
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
    return strat_resp.json()


def test_async_backtest_submission(auth_user, sample_strategy):
    """POST /api/v1/backtests returns HTTP 202 with job summary."""
    resp = client.post("/api/v1/backtests", headers=auth_user["headers"], json={
        "strategy_id": sample_strategy["id"],
        "initial_capital": 100000.0,
        "slippage_type": "ZERO",
        "slippage_value": 0.0
    })
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] in ("QUEUED", "RUNNING", "COMPLETED")
    assert "id" in data
    assert data["initial_capital"] == 100000.0
    assert data["engine_version"] == "bison-backtest-engine-v0.8.0"
    assert data["run_identity"] is not None


def test_submission_duplicate_active_protection(auth_user, sample_strategy):
    """If an identical active backtest is QUEUED, POST /backtests returns the existing active run."""
    with Session(sync_engine) as db:
        # Fetch the strategy version
        ver = db.query(StrategyVersionModel).filter_by(strategy_id=sample_strategy["id"]).first()
        assert ver is not None

        # Seed an active QUEUED run with known run_identity
        from app.domains.backtesting.configuration import BacktestConfiguration, RunIdentityCalculator, ENGINE_VERSION
        config = BacktestConfiguration(
            strategy_version_id=ver.id,
            dataset_id="DEFAULT_NIFTY_5M",
            instrument_id="NIFTY",
            timeframe="5m",
            initial_capital=150000.0,
            engine_version=ENGINE_VERSION
        )
        run_identity = RunIdentityCalculator.calculate_run_identity(config, strategy_dsl_version=ver.version)

        active_run = BacktestRunModel(
            user_id=auth_user["user_id"],
            strategy_version_id=ver.id,
            initial_capital=150000.0,
            configuration_json=config.model_dump(),
            run_identity=run_identity,
            engine_version=ENGINE_VERSION,
            status="QUEUED"
        )
        db.add(active_run)
        db.commit()
        seeded_id = active_run.id

    # Now call POST /api/v1/backtests with identical configuration
    resp = client.post("/api/v1/backtests", headers=auth_user["headers"], json={
        "strategy_id": sample_strategy["id"],
        "initial_capital": 150000.0
    })
    assert resp.status_code == 202
    data = resp.json()
    assert data["id"] == seeded_id
    assert data["run_identity"] == run_identity


def test_invalid_strategy_submission_rejected(auth_user):
    """Submitting backtest for non-existent strategy returns 404."""
    resp = client.post("/api/v1/backtests", headers=auth_user["headers"], json={
        "strategy_id": "non_existent_strategy_id_12345",
        "initial_capital": 100000.0
    })
    assert resp.status_code == 404
