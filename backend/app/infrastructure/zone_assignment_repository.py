from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.devices.entity import Device
from app.infrastructure.device_repository import DeviceRepository
from app.infrastructure.models import DeviceRow, ZoneRow


class AssignmentNotFoundError(LookupError):
    """The requested device or zone does not exist."""


class ZoneAssignmentRepository:
    def __init__(self, session: Session):
        self.session = session

    def assign(
        self,
        device_id: UUID,
        zone_id: UUID | None,
    ) -> Device:
        try:
            zone = None

            if zone_id is not None:
                zone = self.session.scalar(
                    select(ZoneRow)
                    .where(ZoneRow.id == zone_id)
                    .with_for_update()
                )

                if zone is None:
                    raise AssignmentNotFoundError("Zone was not found.")

            device = self.session.scalar(
                select(DeviceRow)
                .where(DeviceRow.id == device_id)
                .with_for_update()
            )

            if device is None:
                raise AssignmentNotFoundError("Device was not found.")

            device.zone_id = zone.id if zone is not None else None
            device.location_id = (
                zone.location_id if zone is not None else None
            )

            self.session.flush()
            result = DeviceRepository._to_device(device)
            self.session.commit()
            return result

        except Exception:
            self.session.rollback()
            raise

    def list_devices(
        self,
        location_id: UUID,
        zone_id: UUID,
    ) -> list[Device]:
        zone = self.session.scalar(
            select(ZoneRow).where(
                ZoneRow.id == zone_id,
                ZoneRow.location_id == location_id,
            )
        )

        if zone is None:
            raise AssignmentNotFoundError(
                "Zone was not found in this location."
            )

        rows = self.session.scalars(
            select(DeviceRow)
            .where(DeviceRow.zone_id == zone_id)
            .order_by(DeviceRow.created_at, DeviceRow.id)
        ).all()

        return [DeviceRepository._to_device(row) for row in rows]