"""
Unit tests for Moving Average Crossover Strategy logic.
"""

from datetime import datetime, timedelta
import pytest
from app.core.events import EventType, MarketDataEvent, SignalDirection
from app.core.event_bus import EventBus
from app.strategies.ma_crossover import MovingAverageCrossover


def test_ma_crossover_signals():
    bus = EventBus()
    strategy = MovingAverageCrossover(
        strategy_id="test_ma",
        symbol="AAPL",
        event_bus=bus,
        config={"fast_period": 2, "slow_period": 4}
    )

    base_time = datetime(2025, 1, 1)
    # Price sequence designed to create a bullish crossover
    prices = [100.0, 100.0, 100.0, 100.0, 110.0, 120.0, 130.0]
    
    generated_signals = []

    for i, p in enumerate(prices):
        t = base_time + timedelta(days=i)
        bar = MarketDataEvent(
            event_type=EventType.MARKET_DATA,
            timestamp=t,
            symbol="AAPL",
            open=p, high=p + 1.0, low=p - 1.0, close=p, volume=1000.0
        )
        sigs = strategy.on_market_data(bar)
        generated_signals.extend(sigs)

    # Should trigger at least one BUY signal when fast SMA crosses slow SMA
    buy_signals = [s for s in generated_signals if s.direction == SignalDirection.BUY]
    assert len(buy_signals) >= 1
    assert buy_signals[0].symbol == "AAPL"
