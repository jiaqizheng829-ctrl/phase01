from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.readings.service import (
    DeviceNotFoundError,
    ReadingIngest,
)
from app.domain.events.bus import EventBus
from app.infrastructure.adapters.sensors.selector import (
    select_sensor_adapter,
)
from app.infrastructure.device_repository import DeviceRepository
from app.infrastructure.models import DeviceRow
from app.infrastructure.reading_repository import ReadingRepository


def build_reading_ingest(
    session: Session,
    bus: EventBus,
) -> ReadingIngest:
    def is_tracking_enabled(device_id: UUID) -> bool:
        enabled = session.scalar(
            select(DeviceRow.tracking_enabled).where(
                DeviceRow.id == device_id,
                DeviceRow.role == "sensor",
            )
        )

        if enabled is None:
            raise DeviceNotFoundError("Sensor not found.")

        return bool(enabled)

    return ReadingIngest(
        devices=DeviceRepository(session),
        readings=ReadingRepository(session),
        select_adapter=select_sensor_adapter,
        bus=bus,
        is_tracking_enabled=is_tracking_enabled,
    )