"""
Integration tests for Worker execution, Orchestrator simulation, and atomic persistence.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, selectinload

from app.main import app
from app.db.session import AsyncSessionLocal
from app.db.models import BacktestRunModel, StrategyVersionModel, TradeModel, OrderModel, ExecutionModel, TransactionCostModel
from app.domains.jobs.worker import execute_backtest_job

client = TestClient(app)
sync_engine = create_engine("sqlite:///./bison.db")


@pytest.fixture
def auth_user():
    """Registers and authenticates a test user."""
    import uuid
    unique_email = f"worker_tester_{uuid.uuid4().hex[:8]}@bison.com"
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": unique_email,
        "password": "Password123!",
        "full_name": "Worker Execution Tester"
    })
    data = reg_resp.json()
    token = data["access_token"]
    user_id = data["user_id"]
    return {"headers": {"Authorization": f"Bearer {token}"}, "user_id": user_id}


@pytest.fixture
def strategy_id(auth_user):
    """Creates a valid strategy."""
    strat_resp = client.post("/api/v1/strategies", headers=auth_user["headers"], json={
        "name": "NIFTY RSI + EMA Strategy",
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


@pytest.mark.asyncio
async def test_worker_simulation_and_persistence(auth_user, strategy_id):
    """Seeds a QUEUED backtest and directly invokes execute_backtest_job, verifying atomic DB persistence."""
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
        backtest_id = queued_run.id

    # Execute worker task directly
    await execute_backtest_job(backtest_id)

    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(BacktestRunModel)
            .options(
                selectinload(BacktestRunModel.trades),
                selectinload(BacktestRunModel.orders),
                selectinload(BacktestRunModel.executions),
                selectinload(BacktestRunModel.transaction_costs),
                selectinload(BacktestRunModel.portfolio)
            )
            .where(BacktestRunModel.id == backtest_id)
        )
        run = res.scalars().first()

        assert run is not None
        assert run.status == "COMPLETED"
        assert run.progress == 100.0
        assert run.total_bars > 0
        assert run.processed_bars == run.total_bars
        assert run.completed_at is not None
        assert run.final_capital is not None
        assert run.execution_metrics_json is not None
        assert "bars_per_second" in run.execution_metrics_json
