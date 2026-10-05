from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.readings.sampler import SamplingDevice
from app.domain.devices.entity import Device
from app.infrastructure.models import DeviceRow


class SamplingDeviceRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_sampling_devices(self) -> list[SamplingDevice]:
        statement = (
            select(DeviceRow)
            .where(
                DeviceRow.role == "sensor",
                DeviceRow.tracking_enabled.is_(True),
                DeviceRow.default_config["protocol"].astext
                == "simulation",
            )
            .order_by(DeviceRow.id)
        )

        rows = self.session.scalars(statement).all()

        return [
            SamplingDevice(
                device=Device(
                    id=row.id,
                    device_type=row.device_type,
                    role=row.role,
                    device_family=row.device_family,
                    display_name=row.display_name,
                    default_config=dict(row.default_config),
                    zone_id=row.zone_id,
                    location_id=row.location_id,
                ),
                sampling_interval_seconds=row.sampling_interval_seconds,
                tracking_enabled=row.tracking_enabled,
            )
            for row in rows
        ]