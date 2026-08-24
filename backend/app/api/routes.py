"""
FastAPI REST API Routes.

Endpoints:
- POST /api/data/upload : Upload historical CSV/Parquet market data
- GET  /api/data/symbols : List available market symbols
- POST /api/strategies   : Validate & store strategy configuration JSON
- GET  /api/strategies   : List saved strategy configurations
- POST /api/backtests    : Execute backtest and return detailed analytics
- GET  /api/backtests/{id} : Fetch results of a previous backtest run
"""

import os
import uuid
from pathlib import Path
from typing import Dict, Any, List

from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd

from app.api.schemas import StrategyConfigRequest, BacktestRequest, BacktestResponse
from app.data.ingestion import DataIngestion
from app.data.sample_data import ensure_sample_data_dir
from app.backtest.engine import BacktestEngine

router = APIRouter()

# Data directory path
DATA_DIR = Path("data")
# In-memory storage for saved strategies & backtest results
STRATEGIES_DB: Dict[str, dict] = {}
BACKTESTS_DB: Dict[str, dict] = {}


@router.post("/data/upload")
async def upload_data(file: UploadFile = File(...), symbol: str = "CUSTOM"):
    """
    Upload a CSV or Parquet file containing historical OHLCV data.
    """
    DATA_DIR.mkdir(exist_ok=True)
    temp_file_path = DATA_DIR / f"{symbol.upper()}_{file.filename}"

    with open(temp_file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        df = DataIngestion.load_and_normalize(temp_file_path, symbol=symbol.upper())
        save_path = DATA_DIR / f"{symbol.upper()}.csv"
        df.to_csv(save_path, index=False)
        
        return {
            "status": "SUCCESS",
            "message": f"Successfully ingested dataset for {symbol.upper()}",
            "symbol": symbol.upper(),
            "num_bars": len(df),
            "date_range": {
                "start": str(df["timestamp"].min()),
                "end": str(df["timestamp"].max())
            }
        }
    except Exception as e:
        if temp_file_path.exists():
            os.remove(temp_file_path)
        raise HTTPException(status_code=400, detail=f"Failed to process upload: {str(e)}")


@router.get("/data/symbols")
def get_available_symbols():
    """
    Return list of available historical symbols and bar metadata.
    """
    ensure_sample_data_dir(str(DATA_DIR))
    symbols_info = []

    for file_path in DATA_DIR.glob("*.csv"):
        symbol = file_path.stem.upper()
        try:
            df = pd.read_csv(file_path)
            symbols_info.append({
                "symbol": symbol,
                "num_bars": len(df),
                "start_date": str(df["timestamp"].min()) if "timestamp" in df.columns else "N/A",
                "end_date": str(df["timestamp"].max()) if "timestamp" in df.columns else "N/A"
            })
        except Exception:
            continue

    return {"symbols": symbols_info}


@router.post("/strategies")
def create_strategy_config(config: StrategyConfigRequest):
    """
    Validate and save a strategy configuration.
    """
    strategy_id = str(uuid.uuid4())
    stored_data = {
        "id": strategy_id,
        "name": config.name,
        "strategy_type": config.strategy_type,
        "symbol": config.symbol,
        "parameters": config.parameters
    }
    STRATEGIES_DB[strategy_id] = stored_data
    return stored_data


@router.get("/strategies")
def list_strategies():
    """List all saved strategy configurations."""
    return {"strategies": list(STRATEGIES_DB.values())}


@router.post("/backtests", response_model=BacktestResponse)
def run_backtest(req: BacktestRequest):
    """
    Execute a synchronous backtest run and calculate analytics.
    """
    ensure_sample_data_dir(str(DATA_DIR))
    symbol = req.strategy_config.symbol.upper()
    file_path = DATA_DIR / f"{symbol}.csv"

    if not file_path.exists():
        # Fallback to AAPL if specified symbol isn't found
        symbol = "AAPL"
        file_path = DATA_DIR / "AAPL.csv"

    try:
        df = pd.read_csv(file_path)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read market data for {symbol}: {str(e)}")

    # Initialize Backtest Engine
    engine = BacktestEngine(
        symbol=symbol,
        df_data=df,
        strategy_name=req.strategy_config.strategy_type,
        strategy_config=req.strategy_config.parameters,
        initial_capital=req.initial_capital,
        commission=req.commission,
        slippage_bps=req.slippage_bps
    )

    result = engine.run()
    backtest_id = str(uuid.uuid4())

    response_payload = {
        "backtest_id": backtest_id,
        "status": result["status"],
        "symbol": symbol,
        "metrics": result["metrics"],
        "equity_curve": result["equity_curve"],
        "trades": result["trades"]
    }

    # Store result for subsequent retrieval
    BACKTESTS_DB[backtest_id] = response_payload
    return response_payload


@router.get("/backtests/{backtest_id}", response_model=BacktestResponse)
def get_backtest_result(backtest_id: str):
    """
    Retrieve stored backtest run details by backtest_id.
    """
    if backtest_id not in BACKTESTS_DB:
        raise HTTPException(status_code=404, detail=f"Backtest run with ID '{backtest_id}' not found.")
    return BACKTESTS_DB[backtest_id]
