"""
Synchronous Event Bus for Backtesting & Deterministic Processing.

Routes events sequentially to registered subscriber callbacks while preserving strict timestamp ordering.
"""

from collections import deque
from typing import Callable, Dict, List
import logging

from app.core.events import Event, EventType

logger = logging.getLogger(__name__)

# Type alias for event handler callbacks
EventHandler = Callable[[Event], None]


class EventBus:
    """
    Synchronous queue-based event bus ensuring deterministic execution order.
    Strategies, Portfolios, and Execution models subscribe to event types.
    """

    def __init__(self):
        # FIFO Queue storing events in order of dispatch
        self._queue: deque[Event] = deque()
        # Registry mapping EventType to list of handler functions
        self._subscribers: Dict[EventType, List[EventHandler]] = {
            event_type: [] for event_type in EventType
        }

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Register a callback handler for a specific EventType."""
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            logger.debug(f"Subscribed {handler.__name__} to {event_type.value}")

    def put(self, event: Event) -> None:
        """Push an event into the processing queue."""
        self._queue.append(event)

    def process_all(self) -> None:
        """
        Drain the event queue synchronously until empty.
        Handlers can publish new events during processing (e.g. MarketData -> Signal -> Order -> Fill).
        """
        while self._queue:
            event = self._queue.popleft()
            handlers = self._subscribers.get(event.event_type, [])
            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"Error handling event {event} in {handler}: {e}", exc_info=True)
                    raise e

    def clear(self) -> None:
        """Reset event bus queue and subscriptions."""
        self._queue.clear()
        for event_type in self._subscribers:
            self._subscribers[event_type].clear()
