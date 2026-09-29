from uuid import UUID

from app.application.devices.dto import DeviceDto
from app.application.devices.mappers import to_device_dto
from app.infrastructure.zone_assignment_repository import (
    ZoneAssignmentRepository,
)


class ZoneAssignmentService:
    def __init__(self, repository: ZoneAssignmentRepository):
        self.repository = repository

    def assign(
        self,
        device_id: UUID,
        zone_id: UUID | None,
    ) -> DeviceDto:
        device = self.repository.assign(device_id, zone_id)
        return to_device_dto(device)

    def list_devices(
        self,
        location_id: UUID,
        zone_id: UUID,
    ) -> list[DeviceDto]:
        devices = self.repository.list_devices(location_id, zone_id)
        return [to_device_dto(device) for device in devices]