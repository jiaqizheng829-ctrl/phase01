from copy import deepcopy

from app.application.locations.dto import (
    LocationConfigCreateRequest,
    LocationConfigRead,
    LocationRead,
    ZoneRead,
)
from app.domain.locations.config_builder import LocationConfigBuilder
from app.domain.locations.entity import LocationConfig


def to_domain_config(
    request: LocationConfigCreateRequest,
) -> LocationConfig:
    builder = LocationConfigBuilder()
    builder.set_location_name(request.location_name)

    for zone in request.zones:
        builder.add_zone(
            name=zone.name,
            moisture_threshold_low=zone.moisture_threshold_low,
            moisture_threshold_high=zone.moisture_threshold_high,
            schedule=zone.schedule,
        )

    return builder.build()


def to_config_read(config: LocationConfig) -> LocationConfigRead:
    location = config.location

    if location.id is None:
        raise ValueError("Cannot return a location without a saved ID.")

    zones = []

    for zone in location.zones:
        if zone.id is None:
            raise ValueError("Cannot return a zone without a saved ID.")

        zones.append(
            ZoneRead(
                id=zone.id,
                location_id=location.id,
                name=zone.name,
                moisture_threshold_low=zone.moisture_threshold_low,
                moisture_threshold_high=zone.moisture_threshold_high,
                schedule=deepcopy(zone.schedule),
            )
        )

    return LocationConfigRead(
        location=LocationRead(
            id=location.id,
            name=location.name,
        ),
        zones=zones,
    )