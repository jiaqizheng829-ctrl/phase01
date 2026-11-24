from app.domain.events.bus import EventBus
from app.infrastructure.event_bus import event_bus


def get_event_bus() -> EventBus:
    return event_bus