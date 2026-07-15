"""
Event bus for Aphelion - central event dispatcher.

Provides type-safe event subscription and dispatching using Qt signals.
This enables loose coupling between components without direct references.
"""
from typing import Dict, Type, Callable, Any, Optional
from PySide6.QtCore import QObject, Signal
from .logging import get_logger

logger = get_logger(__name__)


class EventBus(QObject):
    """
    Central event dispatcher for application-wide events.

    Uses Qt signals for thread-safe event delivery.
    Singleton pattern ensures single bus instance.
    """

    _instance: Optional["EventBus"] = None
    _initialized: bool = False

    # Define signals for each event type
    # We use a generic signal that carries event type and data
    event_dispatched = Signal(object)  # Generic signal for any event

    def __new__(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        super().__init__()
        self._subscribers: Dict[Type[Any], list[Callable[[Any], None]]] = {}
        self._initialized = True

    def subscribe(self, event_type: Type[Any], handler: Callable[[Any], None]) -> None:
        """
        Subscribe to an event type.

        Args:
            event_type: The event class to subscribe to (e.g., LayerChangedEvent)
            handler: Callback function that takes the event as parameter
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            logger.debug(f"Subscribed {handler.__name__} to {event_type.__name__}")

    def unsubscribe(self, event_type: Type[Any], handler: Callable[[Any], None]) -> None:
        """
        Unsubscribe from an event type.

        Args:
            event_type: The event class to unsubscribe from
            handler: The callback function to remove
        """
        if event_type in self._subscribers:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
                logger.debug(f"Unsubscribed {handler.__name__} from {event_type.__name__}")

    def publish(self, event: Any) -> None:
        """
        Publish an event to all subscribers.

        Args:
            event: Event instance (should be a dataclass from events.py)
        """
        event_type = type(event)

        if event_type not in self._subscribers:
            return

        logger.debug(f"Publishing {event_type.__name__}: {event}")

        # Call all handlers for this event type
        for handler in self._subscribers[event_type]:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler {handler.__name__}: {e}", exc_info=True)

    def clear_all(self) -> None:
        """Clear all subscriptions. Used for testing."""
        self._subscribers.clear()


# Global singleton instance
def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    return EventBus()
