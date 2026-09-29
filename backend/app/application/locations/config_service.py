from uuid import UUID

from app.application.locations.dto import (
    LocationConfigCreateRequest,
    LocationConfigRead,
    LocationRead,
)
from app.application.locations.mappers import (
    to_config_read,
    to_domain_config,
)
from app.infrastructure.location_repository import LocationRepository


class LocationNotFoundError(LookupError):
    """Raised when the requested location does not exist."""


class LocationConfigService:
    def __init__(self, repository: LocationRepository):
        self.repository = repository

    def create(
        self,
        request: LocationConfigCreateRequest,
    ) -> LocationConfigRead:
        config = to_domain_config(request)
        saved_config = self.repository.save(config)
        return to_config_read(saved_config)

    def get(self, location_id: UUID) -> LocationConfigRead:
        config = self.repository.get(location_id)

        if config is None:
            raise LocationNotFoundError(
                f"Location {location_id} was not found."
            )

        return to_config_read(config)

    def list_locations(self) -> list[LocationRead]:
        locations = self.repository.list_locations()

        return [
            LocationRead(id=location.id, name=location.name)
            for location in locations
        ]

    def delete(self, location_id: UUID) -> None:
        deleted = self.repository.delete(location_id)

        if not deleted:
            raise LocationNotFoundError(
                f"Location {location_id} was not found."
            )
