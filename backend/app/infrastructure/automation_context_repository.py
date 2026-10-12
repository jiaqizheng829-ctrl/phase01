from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.automation.context import LocationAutomationContext
from app.infrastructure.models import DeviceRow, ReadingRow, ZoneRow


class AutomationContextRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_location(
        self,
        location_id: UUID,
    ) -> list[LocationAutomationContext]:
        zones = self.session.scalars(
            select(ZoneRow)
            .where(ZoneRow.location_id == location_id)
            .order_by(ZoneRow.name, ZoneRow.id)
        ).all()

        contexts: list[LocationAutomationContext] = []

        for zone in zones:
            sensor_filters = (
                DeviceRow.zone_id == zone.id,
                DeviceRow.role == "sensor",
                DeviceRow.device_type == "moisture_sensor",
            )

            sensor_id = self.session.scalar(
                select(DeviceRow.id)
                .where(*sensor_filters)
                .limit(1)
            )

            latest_value = self.session.scalar(
                select(ReadingRow.value)
                .join(
                    DeviceRow,
                    DeviceRow.id == ReadingRow.device_id,
                )
                .where(*sensor_filters)
                .order_by(
                    ReadingRow.recorded_at.desc(),
                    ReadingRow.id.desc(),
                )
                .limit(1)
            )

            contexts.append(
                LocationAutomationContext(
                    location_id=location_id,
                    zone_id=zone.id,
                    moisture_threshold_low=float(
                        zone.moisture_threshold_low
                    ),
                    moisture_threshold_high=float(
                        zone.moisture_threshold_high
                    ),
                    latest_moisture=(
                        float(latest_value)
                        if latest_value is not None
                        else None
                    ),
                    has_moisture_sensor=sensor_id is not None,
                )
            )

        return contexts