from collections import defaultdict
from collections.abc import Callable
from typing import Any

from {{ package_name }}.domain.ports.events import EventDispatcher


class InProcessEventDispatcher(EventDispatcher):
    # Default dispatcher — calls subscribed handlers synchronously, in-process.
    # Swap for a real message bus (SNS, Kafka, ...) by implementing EventDispatcher
    # and wiring it in container.py; use cases that call dispatch() don't change.
    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable[[Any], None]]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: Callable[[Any], None]) -> None:
        self._handlers[event_type].append(handler)

    def dispatch(self, event: object) -> None:
        for handler in self._handlers[type(event)]:
            handler(event)
