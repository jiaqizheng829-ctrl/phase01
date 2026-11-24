from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app.application.alerts.subscribers import (
    AlertPersistenceSubscriber,
    MoistureThresholdSubscriber,
)
from app.domain.events.bus import EventBus
from app.domain.events.events import (
    ActuatorStateChanged,
    CommandFailed,
    ReadingCreated,
    ThresholdCrossed,
)
from app.infrastructure.alert_repository import AlertRepository
from app.infrastructure.db import SessionLocal
from app.infrastructure.models import ZoneRow


def build_event_bus(
    session_factory: Callable[[], Session] = SessionLocal,
) -> EventBus:
    bus = EventBus()

    def load_threshold(zone_id: UUID) -> float | None:
        with session_factory() as session:
            zone = session.get(ZoneRow, zone_id)
            if zone is None:
                return None
            return float(zone.moisture_threshold_low)

    def save_alert(**fields: object) -> None:
        with session_factory() as session:
            try:
                AlertRepository(session).add(**fields)
                session.commit()
            except Exception:
                session.rollback()
                raise

    moisture = MoistureThresholdSubscriber(bus, load_threshold)
    persistence = AlertPersistenceSubscriber(save_alert)

    bus.subscribe(ReadingCreated, moisture.on_reading)
    bus.subscribe(ThresholdCrossed, persistence.on_threshold)
    bus.subscribe(CommandFailed, persistence.on_command)
    bus.subscribe(ActuatorStateChanged, persistence.on_state)

    return bus


# Shared by the application's publishers.
event_bus = build_event_bus()