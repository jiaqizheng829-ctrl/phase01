from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.sensors import Sensor
from app.infrastructure.models import DeviceRow


class DeviceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_sensor(self, sensor: Sensor) -> Sensor:
        row = DeviceRow(
            device_type=sensor.device_type,
            role="sensor",
            display_name=sensor.display_name,
            default_config=sensor.default_config,
        )
        self.session.add(row)
        self.session.commit()
        self.session.refresh(row)
        return self._to_sensor(row)

    def list_sensors(self) -> list[Sensor]:
        statement = (
            select(DeviceRow)
            .where(DeviceRow.role == "sensor")
            .order_by(DeviceRow.created_at)
        )
        rows = self.session.scalars(statement).all()
        return [self._to_sensor(row) for row in rows]

    @staticmethod
    def _to_sensor(row: DeviceRow) -> Sensor:
        return Sensor(
            id=row.id,
            device_type=row.device_type,
            display_name=row.display_name,
            default_config=row.default_config,
        )
