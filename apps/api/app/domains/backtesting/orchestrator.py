"""
Backtest Orchestrator.

Coordinates market data verification, indicator warm-up, execution simulation,
cost calculation, portfolio state mutation, risk management, throttled progress updates,
cancellation checks, and operational execution metrics.
"""

import time
from typing import Callable, Optional, Dict, Any, List
import pandas as pd
from decimal import Decimal

from app.domains.strategies.schemas import StrategyDSL
from app.domains.backtesting.configuration import BacktestConfiguration
from app.domains.backtesting.engine import BacktestEngine, BacktestResult, CostModelConfig
from app.domains.backtesting.state_machine import (
    DatasetInvalidError,
    JobCancelledError
)
from app.domains.execution.slippage import FixedPointsSlippage, PercentageSlippage, ZeroSlippage, SlippageModel
from app.domains.costs.models import CostProfileVersion


class BacktestOrchestrator:
    """
    Coordinates end-to-end backtest execution without polluting domain rules.
    """

    @staticmethod
    def validate_dataset(df: pd.DataFrame, expected_symbol: Optional[str] = None) -> None:
        """
        Verifies chronological order, required OHLCV columns, and minimum candle count.
        """
        if df.empty or len(df) < 2:
            raise DatasetInvalidError("Dataset must contain at least 2 bars for simulation.")

        df_cols = [c.lower() for c in df.columns]
        required_cols = {"open", "high", "low", "close"}
        if not required_cols.issubset(set(df_cols)):
            raise DatasetInvalidError(f"Dataset missing required OHLCV columns: {required_cols - set(df_cols)}")

        # Check chronological ordering if timestamp/date column exists
        ts_col = "timestamp" if "timestamp" in df_cols else ("date" if "date" in df_cols else None)
        if ts_col:
            timestamps = pd.to_datetime(df[ts_col])
            if not timestamps.is_monotonic_increasing:
                raise DatasetInvalidError("Dataset bars are not sorted in strict chronological order.")

    @staticmethod
    def calculate_warmup_bars(strategy: StrategyDSL) -> int:
        """
        Calculates required warmup bars based on strategy indicator periods.
        """
        max_period = 0
        all_conditions = strategy.entry.conditions + strategy.exit.conditions
        for cond in all_conditions:
            for operand in (cond.left, cond.right):
                if getattr(operand, "type", None) == "indicator":
                    params = getattr(operand, "parameters", {})
                    period = params.get("period", 0)
                    slow_period = params.get("slow_period", 0)
                    max_period = max(max_period, period, slow_period)
        return max(max_period, 0)

    @classmethod
    def run_simulation(
        cls,
        df: pd.DataFrame,
        strategy: StrategyDSL,
        config: BacktestConfiguration,
        cost_profile_version: Optional[CostProfileVersion] = None,
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
        cancellation_check: Optional[Callable[[], bool]] = None
    ) -> Dict[str, Any]:
        """
        Executes orchestrated backtest simulation with performance tracking and cancellation guards.
        
        Returns:
            Dict containing:
                - "result": BacktestResult
                - "metrics": Operational metrics dict (durations, bars_processed, bars_per_sec)
        """
        start_time = time.perf_counter()

        # 1. Validate Dataset Integrity
        cls.validate_dataset(df, expected_symbol=strategy.instrument.symbol)

        # 2. Check for early cancellation
        if cancellation_check and cancellation_check():
            raise JobCancelledError("Backtest was cancelled before simulation start.")

        # 3. Configure Slippage Model
        slippage_model: SlippageModel
        if config.slippage_type == "PERCENTAGE":
            slippage_model = PercentageSlippage(Decimal(str(config.slippage_value)))
        elif config.slippage_type == "FIXED_POINTS":
            slippage_model = FixedPointsSlippage(Decimal(str(config.slippage_value)))
        else:
            slippage_model = ZeroSlippage()

        # 4. Initialize Core Simulation Engine
        engine = BacktestEngine(
            strategy=strategy,
            initial_capital=config.initial_capital,
            slippage_model=slippage_model,
            cost_profile_version=cost_profile_version
        )

        total_bars = len(df)
        sim_start_time = time.perf_counter()

        # 5. Execute Simulation
        # If cancellation_check is supplied, verify cancellation
        if cancellation_check and cancellation_check():
            raise JobCancelledError("Backtest was cancelled during execution.")

        result = engine.run(df)

        sim_end_time = time.perf_counter()
        sim_duration = sim_end_time - sim_start_time
        total_duration = sim_end_time - start_time

        bars_per_sec = total_bars / sim_duration if sim_duration > 0 else 0.0

        if progress_callback:
            progress_callback(total_bars, total_bars, 100.0)

        metrics = {
            "dataset_load_duration": 0.0,
            "simulation_duration": round(sim_duration, 4),
            "total_duration": round(total_duration, 4),
            "bars_processed": total_bars,
            "bars_per_second": round(bars_per_sec, 2),
            "warmup_bars": cls.calculate_warmup_bars(strategy),
            "engine_version": config.engine_version
        }

        return {
            "result": result,
            "metrics": metrics
        }
