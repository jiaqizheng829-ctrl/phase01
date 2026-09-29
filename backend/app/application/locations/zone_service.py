from copy import deepcopy
from uuid import UUID

from app.application.locations.config_service import LocationNotFoundError
from app.application.locations.dto import (
    ZoneCreateRequest,
    ZoneRead,
    ZoneUpdateRequest,
)
from app.domain.locations.entity import Zone
from app.domain.locations.validation import validate_zone
from app.infrastructure.zone_repository import ZoneRepository


class ZoneService:
    def __init__(self, repository: ZoneRepository):
        self.repository = repository

    def add(
        self,
        location_id: UUID,
        request: ZoneCreateRequest,
    ) -> ZoneRead:
        name = validate_zone(
            request.name,
            request.moisture_threshold_low,
            request.moisture_threshold_high,
            request.schedule,
        )

        zone = Zone(
            name=name,
            moisture_threshold_low=request.moisture_threshold_low,
            moisture_threshold_high=request.moisture_threshold_high,
            schedule=deepcopy(request.schedule),
        )

        saved_zone = self.repository.add(location_id, zone)

        if saved_zone is None:
            raise LocationNotFoundError(
                f"Location {location_id} was not found."
            )

        return ZoneRead(
            id=saved_zone.id,
            location_id=location_id,
            name=saved_zone.name,
            moisture_threshold_low=saved_zone.moisture_threshold_low,
            moisture_threshold_high=saved_zone.moisture_threshold_high,
            schedule=deepcopy(saved_zone.schedule),
        )
    def update(
        self,
        location_id: UUID,
        zone_id: UUID,
        request: ZoneUpdateRequest,
    ) -> ZoneRead:
        changes = request.model_dump(exclude_unset=True)
        zone = self.repository.update(location_id, zone_id, changes)

        if zone is None:
            raise LocationNotFoundError(
                "Location or zone was not found in this location."
            )

        return ZoneRead(
            id=zone.id,
            location_id=location_id,
            name=zone.name,
            moisture_threshold_low=zone.moisture_threshold_low,
            moisture_threshold_high=zone.moisture_threshold_high,
            schedule=deepcopy(zone.schedule),
        )
    def delete(self, location_id: UUID, zone_id: UUID) -> None:
        deleted = self.repository.delete(location_id, zone_id)

        if not deleted:
            raise LocationNotFoundError(
                "Location or zone was not found in this location."
            )
