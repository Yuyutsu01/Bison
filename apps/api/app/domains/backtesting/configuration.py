"""
Backtest Configuration and Deterministic Run Identity.

Provides immutable, serializable configuration objects and canonical SHA-256
hash calculation for reproducible backtest identification.
"""

import json
import hashlib
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict

ENGINE_VERSION = "bison-backtest-engine-v0.8.0"


class BacktestConfiguration(BaseModel):
    """
    Immutable, serializable configuration for a backtest execution.
    
    Contains all parameterization required to deterministically reproduce a simulation.
    """
    model_config = ConfigDict(frozen=True)

    strategy_version_id: str
    dataset_id: str = "DEFAULT_NIFTY_5M"
    instrument_id: str = "NIFTY50"
    timeframe: str = "5m"
    start_datetime: Optional[str] = None
    end_datetime: Optional[str] = None
    initial_capital: float = Field(default=100000.0, gt=0)
    execution_policy: str = "NEXT_BAR_OPEN"
    slippage_type: str = "ZERO"  # ZERO, FIXED_POINTS, PERCENTAGE
    slippage_value: float = Field(default=0.0, ge=0)
    cost_profile_version_id: Optional[str] = None
    position_sizing: Dict[str, Any] = Field(default_factory=lambda: {"type": "FIXED_QUANTITY", "value": 1.0})
    risk_management: Dict[str, Any] = Field(default_factory=lambda: {"end_of_day_exit": True})
    warmup_bars: int = Field(default=0, ge=0)
    engine_version: str = Field(default=ENGINE_VERSION)


class RunIdentityCalculator:
    """
    Calculates deterministic SHA-256 run identity from canonical configuration serialization.
    """

    @staticmethod
    def calculate_run_identity(
        config: BacktestConfiguration,
        strategy_dsl_version: int = 1,
        dataset_content_hash: str = "DATASET_DEFAULT_V1",
        cost_profile_version: int = 1
    ) -> str:
        """
        Computes SHA-256 hash across canonicalized configuration, strategy version,
        dataset version, cost profile version, and engine version.
        
        Important Logic:
        - Keys are sorted and encoded to eliminate dict-ordering nondeterminism.
        - Identical inputs strictly produce the exact same hex digest.
        """
        canonical_dict = {
            "strategy_version_id": config.strategy_version_id,
            "strategy_dsl_version": strategy_dsl_version,
            "dataset_id": config.dataset_id,
            "dataset_content_hash": dataset_content_hash,
            "instrument_id": config.instrument_id,
            "timeframe": config.timeframe,
            "start_datetime": config.start_datetime,
            "end_datetime": config.end_datetime,
            "initial_capital": config.initial_capital,
            "execution_policy": config.execution_policy,
            "slippage_type": config.slippage_type,
            "slippage_value": config.slippage_value,
            "cost_profile_version_id": config.cost_profile_version_id,
            "cost_profile_version": cost_profile_version,
            "position_sizing": config.position_sizing,
            "risk_management": config.risk_management,
            "warmup_bars": config.warmup_bars,
            "engine_version": config.engine_version
        }

        canonical_json = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
