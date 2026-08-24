"""
Pydantic API Schemas for Validation and OpenAPI Documentation.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class StrategyConfigRequest(BaseModel):
    name: str = Field(default="Moving Average Crossover", description="Display name for strategy")
    strategy_type: str = Field(default="moving_average_crossover", description="Strategy identifier in registry")
    symbol: str = Field(default="AAPL", description="Trading asset symbol")
    parameters: Dict[str, Any] = Field(
        default_factory=lambda: {"fast_period": 20, "slow_period": 50},
        description="Dynamic strategy parameters"
    )


class BacktestRequest(BaseModel):
    strategy_config: StrategyConfigRequest
    initial_capital: float = Field(default=100000.0, ge=100.0)
    commission: float = Field(default=1.0, ge=0.0, description="Fixed fee per trade ($)")
    slippage_bps: float = Field(default=5.0, ge=0.0, description="Slippage in basis points (1 bps = 0.01%)")


class BacktestResponse(BaseModel):
    backtest_id: str
    status: str
    symbol: str
    metrics: Dict[str, Any]
    equity_curve: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]
