"""
Unit tests for Synchronous Event Bus.
"""

from datetime import datetime
import pytest
from app.core.events import EventType, MarketDataEvent
from app.core.event_bus import EventBus


def test_event_bus_subscribe_and_dispatch():
    bus = EventBus()
    received_events = []

    def handle_market_data(event):
        received_events.append(event)

    bus.subscribe(EventType.MARKET_DATA, handle_market_data)

    event1 = MarketDataEvent(
        event_type=EventType.MARKET_DATA,
        timestamp=datetime(2025, 1, 1, 9, 30),
        symbol="AAPL",
        open=150.0, high=155.0, low=149.0, close=154.0, volume=100000.0
    )

    bus.put(event1)
    bus.process_all()

    assert len(received_events) == 1
    assert received_events[0].symbol == "AAPL"
    assert received_events[0].close == 154.0
