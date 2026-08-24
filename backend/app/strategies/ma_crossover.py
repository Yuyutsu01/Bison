"""
Moving Average Crossover Strategy Implementation.

Calculates Fast and Slow Simple Moving Averages (SMA) over incoming close prices.
Emits a BUY SignalEvent when Fast SMA crosses above Slow SMA.
Emits an EXIT/SELL SignalEvent when Fast SMA crosses below Slow SMA.
"""

from collections import deque
from typing import List, Optional

from app.core.events import MarketDataEvent, SignalEvent, SignalDirection
from app.core.event_bus import EventBus
from app.strategies.base import BaseStrategy, StrategyRegistry


@StrategyRegistry.register("moving_average_crossover")
class MovingAverageCrossover(BaseStrategy):
    """
    Moving Average Crossover Strategy.
    Config parameters:
        - fast_period (int): Lookback period for fast moving average (e.g. 10 or 20)
        - slow_period (int): Lookback period for slow moving average (e.g. 50 or 200)
    """

    def __init__(self, strategy_id: str, symbol: str, event_bus: EventBus, config: dict):
        super().__init__(strategy_id, symbol, event_bus, config)
        self.fast_period: int = int(config.get("fast_period", 20))
        self.slow_period: int = int(config.get("slow_period", 50))
        
        if self.fast_period >= self.slow_period:
            raise ValueError(f"fast_period ({self.fast_period}) must be strictly less than slow_period ({self.slow_period})")

        # Rolling window history of close prices
        self.prices: deque[float] = deque(maxlen=self.slow_period)
        
        # State tracking for crossover detection
        self.prev_fast_sma: Optional[float] = None
        self.prev_slow_sma: Optional[float] = None
        self.in_position: bool = False

    def on_market_data(self, event: MarketDataEvent) -> List[SignalEvent]:
        # Filter for matching symbol
        if event.symbol != self.symbol:
            return []

        self.prices.append(event.close)
        signals: List[SignalEvent] = []

        # We need at least slow_period bars to calculate both SMAs
        if len(self.prices) < self.slow_period:
            return signals

        # Calculate current Fast and Slow Simple Moving Averages
        price_list = list(self.prices)
        fast_sma = sum(price_list[-self.fast_period:]) / self.fast_period
        slow_sma = sum(price_list[-self.slow_period:]) / self.slow_period

        # Check for crossover signals if previous values exist
        if self.prev_fast_sma is not None and self.prev_slow_sma is not None:
            # Bullish Crossover: Fast SMA crosses above Slow SMA
            # Condition: prev_fast <= prev_slow AND curr_fast > curr_slow
            if self.prev_fast_sma <= self.prev_slow_sma and fast_sma > slow_sma:
                if not self.in_position:
                    signal = SignalEvent(
                        event_type=None,
                        timestamp=event.timestamp,
                        strategy_id=self.strategy_id,
                        symbol=self.symbol,
                        direction=SignalDirection.BUY,
                        strength=1.0
                    )
                    signals.append(signal)
                    self.in_position = True

            # Bearish Crossover: Fast SMA crosses below Slow SMA
            # Condition: prev_fast >= prev_slow AND curr_fast < curr_slow
            elif self.prev_fast_sma >= self.prev_slow_sma and fast_sma < slow_sma:
                if self.in_position:
                    signal = SignalEvent(
                        event_type=None,
                        timestamp=event.timestamp,
                        strategy_id=self.strategy_id,
                        symbol=self.symbol,
                        direction=SignalDirection.EXIT,
                        strength=1.0
                    )
                    signals.append(signal)
                    self.in_position = False

        # Store current SMA values for the next bar comparison
        self.prev_fast_sma = fast_sma
        self.prev_slow_sma = slow_sma

        return signals
