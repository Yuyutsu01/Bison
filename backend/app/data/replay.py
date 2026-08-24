"""
Market Data Replay Iterator.

Streams MarketDataEvent instances in chronological order for backtesting.
Supports single or multi-symbol replay loops.
"""

from datetime import datetime
from typing import Generator, List, Optional
import pandas as pd

from app.core.events import MarketDataEvent, EventType


class DataReplayIterator:
    """Replays historical market data bar-by-bar yielding MarketDataEvents."""

    def __init__(self, df: pd.DataFrame, symbol: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        self.symbol = symbol
        self.df = df.copy()
        
        # Filter by optional date range
        if start_date:
            self.df = self.df[self.df["timestamp"] >= pd.to_datetime(start_date)]
        if end_date:
            self.df = self.df[self.df["timestamp"] <= pd.to_datetime(end_date)]
            
        self.df = self.df.sort_values("timestamp").reset_index(drop=True)

    def __len__(self) -> int:
        return len(self.df)

    def __iter__(self) -> Generator[MarketDataEvent, None, None]:
        for row in self.df.itertuples():
            yield MarketDataEvent(
                event_type=EventType.MARKET_DATA,
                timestamp=row.timestamp.to_pydatetime() if hasattr(row.timestamp, "to_pydatetime") else row.timestamp,
                symbol=self.symbol,
                open=float(row.open),
                high=float(row.high),
                low=float(row.low),
                close=float(row.close),
                volume=float(row.volume)
            )
