from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.devices.entity import Device
from app.domain.sensors import Sensor
from app.infrastructure.models import DeviceRow


class DeviceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    # Keep the Phase 2 sensor API working.
    def add_sensor(self, sensor: Sensor) -> Sensor:
        device = Device(
            id=None,
            device_type=sensor.device_type,
            role="sensor",
            device_family="simulation",
            display_name=sensor.display_name,
            default_config=dict(sensor.default_config),
        )
        saved = self.save_device(device)
        return Sensor(
            id=saved.id,
            device_type=saved.device_type,
            display_name=saved.display_name,
            default_config=dict(saved.default_config),
        )

    def list_sensors(self) -> list[Sensor]:
        devices = self.list_devices(role="sensor")
        return [
            Sensor(
                id=device.id,
                device_type=device.device_type,
                display_name=device.display_name,
                default_config=dict(device.default_config),
            )
            for device in devices
        ]

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
            statement = statement.where(
                DeviceRow.role == role
            )

        statement = statement.order_by(
            DeviceRow.created_at,
            DeviceRow.id,
        )
        rows = self.session.scalars(statement).all()

        return [self._to_device(row) for row in rows]

    @staticmethod
    def _to_device(row: DeviceRow) -> Device:
        return Device(
            id=row.id,
            device_type=row.device_type,
            role=row.role,
            device_family=row.device_family,
            display_name=row.display_name,
            default_config=dict(row.default_config),
        )