"""
Data Ingestion & Normalization Module.

Parses CSV and Parquet market data files, standardizing schemas into:
timestamp (datetime), open (float), high (float), low (float), close (float), volume (float).
"""

from datetime import datetime
from pathlib import Path
from typing import Union, List, Dict
import pandas as pd
import numpy as np


class DataIngestion:
    """Handles parsing, schema normalization, and storage of uploaded datasets."""

    REQUIRED_COLUMNS = {"timestamp", "open", "high", "low", "close", "volume"}

    @classmethod
    def load_and_normalize(cls, file_path_or_buffer: Union[str, Path, pd.DataFrame], symbol: str) -> pd.DataFrame:
        """
        Loads CSV/Parquet file, validates schema, converts timestamps to UTC datetime,
        and returns a sorted normalized pandas DataFrame.
        """
        if isinstance(file_path_or_buffer, pd.DataFrame):
            df = file_path_or_buffer.copy()
        else:
            path = Path(file_path_or_buffer)
            if path.suffix.lower() == ".parquet":
                df = pd.read_parquet(path)
            elif path.suffix.lower() == ".csv":
                df = pd.read_csv(path)
            else:
                raise ValueError(f"Unsupported file extension '{path.suffix}'. Expected .csv or .parquet")

        # Standardize column headers to lowercase
        df.columns = [col.strip().lower() for col in df.columns]

        # Check required columns
        missing = cls.REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Dataset for {symbol} is missing required columns: {missing}")

        # Parse timestamp column
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        # Cast numeric fields
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Drop any invalid rows with NaNs
        df = df.dropna(subset=["timestamp", "open", "high", "low", "close", "volume"])

        return df
