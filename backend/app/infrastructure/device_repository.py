from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.devices.entity import Device
from app.domain.sensors import Sensor
from app.infrastructure.models import DeviceRow


class DeviceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, device_id: UUID) -> Device | None:
        row = self.session.get(DeviceRow, device_id)
        return self._to_device(row) if row is not None else None

    def add_sensor(self, sensor: Sensor) -> Sensor:
        row = DeviceRow(
            device_type=sensor.device_type,
            role="sensor",
            device_family="simulation",
            display_name=sensor.display_name,
            default_config=dict(sensor.default_config),
            sampling_interval_seconds=sensor.sampling_interval_seconds,
            tracking_enabled=sensor.tracking_enabled,
        )

        try:
            self.session.add(row)
            self.session.flush()
            saved = self._to_sensor(row)
            self.session.commit()
            return saved
        except Exception:
            self.session.rollback()
            raise

    def list_sensors(self) -> list[Sensor]:
        statement = (
            select(DeviceRow)
            .where(DeviceRow.role == "sensor")
            .order_by(DeviceRow.created_at, DeviceRow.id)
        )

        rows = self.session.scalars(statement).all()
        return [self._to_sensor(row) for row in rows]

    def save_device(self, device: Device) -> Device:
        return self.save_many([device])[0]

    def save_many(self, devices: list[Device]) -> list[Device]:
        rows = [
            DeviceRow(
                device_type=device.device_type,
                role=device.role,
                device_family=device.device_family,
                display_name=device.display_name,
                default_config=dict(device.default_config),
            )
            for device in devices
        ]

        try:
            self.session.add_all(rows)
            self.session.flush()
            saved = [self._to_device(row) for row in rows]
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        return saved

    def list_devices(
        self,
        family: str | None = None,
        role: str | None = None,
    ) -> list[Device]:
        statement = select(DeviceRow)

        if family is not None:
            statement = statement.where(
                DeviceRow.device_family == family
            )

        if role is not None:
            statement = statement.where(DeviceRow.role == role)

        statement = statement.order_by(
            DeviceRow.created_at,
            DeviceRow.id,
        )
        rows = self.session.scalars(statement).all()

        return [self._to_device(row) for row in rows]

    @staticmethod
    def _to_sensor(row: DeviceRow) -> Sensor:
        return Sensor(
            id=row.id,
            device_type=row.device_type,
            display_name=row.display_name,
            default_config=dict(row.default_config),
            sampling_interval_seconds=row.sampling_interval_seconds,
            tracking_enabled=row.tracking_enabled,
        )

    @staticmethod
    def _to_device(row: DeviceRow) -> Device:
        return Device(
            id=row.id,
            device_type=row.device_type,
            role=row.role,
            device_family=row.device_family,
            display_name=row.display_name,
            default_config=dict(row.default_config),
            zone_id=row.zone_id,
            location_id=row.location_id,
        )