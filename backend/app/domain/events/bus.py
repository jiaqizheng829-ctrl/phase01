import logging
from collections.abc import Callable
from typing import Any, TypeVar


logger = logging.getLogger(__name__)
EventT = TypeVar("EventT")


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable[[Any], None]]] = {}

    def subscribe(
        self,
        event_type: type[EventT],
        handler: Callable[[EventT], None],
    ) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: object) -> None:
        # Snapshot subscriptions so additions during dispatch apply next time.
        handlers = tuple(self._handlers.get(type(event), ()))

        for handler in handlers:
            try:
                handler(event)
            except Exception:
                # One failed subscriber must not prevent later subscribers.
                logger.exception(
                    "Subscriber %r failed while handling %s",
                    handler,
                    type(event).__name__,
                )