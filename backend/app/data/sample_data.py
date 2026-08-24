"""
Sample Historical Market Data Generator.

Generates reproducible synthetic historical OHLCV data for AAPL, MSFT, and SPY
if no custom dataset has been uploaded.
"""

from datetime import datetime, timedelta
import os
import pandas as pd
import numpy as np


def generate_sample_data(symbol: str = "AAPL", num_days: int = 1250, start_price: float = 150.0) -> pd.DataFrame:
    """
    Generates realistic daily OHLCV bars using a Geometric Brownian Motion model.
    """
    seed = abs(hash(symbol)) % 100000
    np.random.seed(seed)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=int(num_days * 1.4))  # account for weekends
    dates = pd.date_range(start=start_date, end=end_date, freq='B')[:num_days]
    
    # Drift and volatility
    mu = 0.0004
    sigma = 0.015
    
    returns = np.random.normal(mu, sigma, len(dates))
    price_paths = start_price * np.exp(np.cumsum(returns))
    
    opens = price_paths * (1 + np.random.normal(0, 0.003, len(dates)))
    highs = np.maximum(opens, price_paths) * (1 + np.abs(np.random.normal(0.002, 0.005, len(dates))))
    lows = np.minimum(opens, price_paths) * (1 - np.abs(np.random.normal(0.002, 0.005, len(dates))))
    volumes = np.random.randint(5000000, 50000000, size=len(dates))
    
    df = pd.DataFrame({
        "timestamp": dates.strftime("%Y-%m-%d %H:%M:%S"),
        "open": np.round(opens, 2),
        "high": np.round(highs, 2),
        "low": np.round(lows, 2),
        "close": np.round(price_paths, 2),
        "volume": volumes
    })
    return df


def ensure_sample_data_dir(data_dir: str = "data") -> None:
    """Ensures sample datasets exist locally for instant testing."""
    os.makedirs(data_dir, exist_ok=True)
    symbols = [("AAPL", 150.0), ("MSFT", 300.0), ("SPY", 400.0)]
    for symbol, price in symbols:
        file_path = os.path.join(data_dir, f"{symbol}.csv")
        if not os.path.exists(file_path):
            df = generate_sample_data(symbol, num_days=1000, start_price=price)
            df.to_csv(file_path, index=False)
