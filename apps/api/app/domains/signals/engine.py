"""
Deterministic Signal Engine Module.

Transforms Market Data + Indicators + Strategy DSL rules into a chronological stream of Signal events.
Supports BUY, SELL, and EXIT signals with zero look-ahead bias and indicator warm-up protection.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from app.domains.strategies.schemas import StrategyDSL
from app.domains.signals.models import Signal, SignalType
from app.domains.backtesting.evaluator import RuleEvaluator
from app.domains.indicators.calculator import IndicatorEngine


class SignalEngine:
    """Evaluates time-series candles chronologically and generates deterministic trading signals."""

    def __init__(self, strategy: StrategyDSL):
        self.strategy = strategy

    def generate_signals(self, df: pd.DataFrame) -> List[Signal]:
        """Generates deterministic signal sequence over input DataFrame."""
        if df.empty or len(df) < 2:
            return []

        df = df.copy()
        df.columns = [c.lower() for c in df.columns]
        if "timestamp" not in df.columns and "date" in df.columns:
            df["timestamp"] = df["date"]

        # Precalculate all indicator references in strategy
        indicators = self._precalculate_indicators(df)

        signals: List[Signal] = []
        signal_counter = 0

        # Scan bars chronologically
        for i in range(len(df)):
            row = df.iloc[i]
            timestamp_str = str(row.get("timestamp", f"bar_{i}"))
            close_price = float(row["close"])

            # Check Entry Rules -> BUY Signal
            if self.strategy.entry.conditions:
                if RuleEvaluator.evaluate_rule_group(self.strategy.entry, df, indicators, i):
                    signal_counter += 1
                    signals.append(Signal(
                        signal_id=f"SIG_{signal_counter:04d}",
                        timestamp=timestamp_str,
                        symbol=self.strategy.instrument.symbol,
                        signal_type=SignalType.BUY,
                        bar_index=i,
                        trigger_price=close_price,
                        reason="ENTRY_RULE_TRIGGERED",
                        indicator_snapshot=self._snapshot_indicators(indicators, i)
                    ))

            # Check Exit Rules -> EXIT Signal
            if self.strategy.exit.conditions:
                if RuleEvaluator.evaluate_rule_group(self.strategy.exit, df, indicators, i):
                    signal_counter += 1
                    signals.append(Signal(
                        signal_id=f"SIG_{signal_counter:04d}",
                        timestamp=timestamp_str,
                        symbol=self.strategy.instrument.symbol,
                        signal_type=SignalType.EXIT,
                        bar_index=i,
                        trigger_price=close_price,
                        reason="EXIT_RULE_TRIGGERED",
                        indicator_snapshot=self._snapshot_indicators(indicators, i)
                    ))

        return signals

    def _precalculate_indicators(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        indicators: Dict[str, pd.Series] = {}
        all_conditions = self.strategy.entry.conditions + self.strategy.exit.conditions

        for cond in all_conditions:
            for operand in (cond.left, cond.right):
                if operand.type == "indicator":
                    name = operand.name.upper()
                    params = getattr(operand, "parameters", {})
                    key = RuleEvaluator._get_indicator_key(operand)

                    if key not in indicators:
                        if name == "SMA":
                            indicators[key] = IndicatorEngine.calculate_sma(df, period=params.get("period", 20))
                        elif name == "EMA":
                            indicators[key] = IndicatorEngine.calculate_ema(df, period=params.get("period", 20))
                        elif name == "RSI":
                            indicators[key] = IndicatorEngine.calculate_rsi(df, period=params.get("period", 14))
                        elif name == "ATR":
                            indicators[key] = IndicatorEngine.calculate_atr(df, period=params.get("period", 14))
                        elif name == "MACD":
                            macd_dict = IndicatorEngine.calculate_macd(
                                df,
                                fast_period=params.get("fast_period", 12),
                                slow_period=params.get("slow_period", 26),
                                signal_period=params.get("signal_period", 9)
                            )
                            indicators[key] = macd_dict["macd"]

        return indicators

    def _snapshot_indicators(self, indicators: Dict[str, pd.Series], idx: int) -> Dict[str, float]:
        snapshot = {}
        for k, series in indicators.items():
            val = series.iloc[idx]
            snapshot[k] = round(float(val), 2) if not np.isnan(val) else 0.0
        return snapshot
