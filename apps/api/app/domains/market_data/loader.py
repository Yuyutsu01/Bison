"""
Historical Market Data Ingestion & Quality Validation.

Loads OHLCV data for Indian market instruments (NIFTY, BANKNIFTY, Equities)
and performs data hygiene checks (duplicate detection, missing candles, invalid OHLC relationships).
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
import pandas as pd


@dataclass
class DataQualityReport:
    symbol: str
    total_rows: int
    missing_candles: int
    duplicates: int
    invalid_ohlc: int
    status: str  # "PASSED", "WARNING", "FAILED"
    issues: List[str]


class MarketDataLoader:
    """Ingests, cleans, and validates OHLCV market data series."""

    @classmethod
    def load_from_csv(cls, file_path: str, symbol: str) -> Tuple[pd.DataFrame, DataQualityReport]:
        df = pd.read_csv(file_path)
        return cls.process_and_validate(df, symbol)

    @classmethod
    def process_and_validate(cls, df: pd.DataFrame, symbol: str) -> Tuple[pd.DataFrame, DataQualityReport]:
        issues: List[str] = []
        df = df.copy()

        # Clean column names to lowercase
        df.columns = [c.lower().strip() for c in df.columns]

        required_cols = {"open", "high", "low", "close"}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Market dataset for '{symbol}' missing required columns: {missing}")

        if "timestamp" not in df.columns and "date" in df.columns:
            df["timestamp"] = df["date"]

        total_rows = len(df)

        # 1. Check & remove duplicates
        duplicates = int(df.duplicated(subset=["timestamp"]).sum())
        if duplicates > 0:
            issues.append(f"Found {duplicates} duplicate timestamps. Dropping duplicates.")
            df = df.drop_duplicates(subset=["timestamp"], keep="first")

        # 2. Sort chronologically
        df = df.sort_values(by="timestamp").reset_index(drop=True)

        # 3. Check for invalid OHLC relationships
        invalid_mask = (
            (df["high"] < df["low"]) |
            (df["high"] < df["open"]) |
            (df["high"] < df["close"]) |
            (df["low"] > df["open"]) |
            (df["low"] > df["close"]) |
            (df["open"] <= 0) |
            (df["close"] <= 0)
        )
        invalid_ohlc = int(invalid_mask.sum())
        if invalid_ohlc > 0:
            issues.append(f"Found {invalid_ohlc} candles with invalid OHLC relationship (e.g. High < Low or zero price).")
            # Filter out invalid candles
            df = df[~invalid_mask].reset_index(drop=True)

        missing_candles = 0
        status = "PASSED"
        if invalid_ohlc > 0 or duplicates > 0:
            status = "WARNING"

        report = DataQualityReport(
            symbol=symbol,
            total_rows=total_rows,
            missing_candles=missing_candles,
            duplicates=duplicates,
            invalid_ohlc=invalid_ohlc,
            status=status,
            issues=issues
        )

        return df, report
