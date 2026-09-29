from copy import deepcopy

from .entity import Location, LocationConfig, Zone
from .errors import ConfigurationError
from .validation import validate_name, validate_zone


class LocationConfigBuilder:
    def __init__(self):
        self._location_name: str = ""
        self._zones: list[Zone] = []

    def set_location_name(self, name: str) -> "LocationConfigBuilder":
        self._location_name = name
        return self

    def add_zone(
        self,
        name: str,
        moisture_threshold_low: float,
        moisture_threshold_high: float,
        schedule: dict | None = None,
    ) -> "LocationConfigBuilder":
        self._zones.append(
            Zone(
                name=name,
                moisture_threshold_low=moisture_threshold_low,
                moisture_threshold_high=moisture_threshold_high,
                schedule=deepcopy(
                    schedule if schedule is not None else {}
                ),
            )
        )
        return self

    def build(self) -> LocationConfig:
        location_name = validate_name(
            self._location_name, "Location name"
        )

        if not self._zones:
            raise ConfigurationError(
                "A location must have at least one zone."
            )

        names: set[str] = set()
        validated_zones: list[Zone] = []

        for zone in self._zones:
            zone_name = validate_zone(
                zone.name,
                zone.moisture_threshold_low,
                zone.moisture_threshold_high,
                zone.schedule,
            )

            if zone_name in names:
                raise ConfigurationError(
                    f"Duplicate zone name: {zone_name}"
                )

            names.add(zone_name)

            validated_zones.append(
                Zone(
                    name=zone_name,
                    moisture_threshold_low=float(
                        zone.moisture_threshold_low
                    ),
                    moisture_threshold_high=float(
                        zone.moisture_threshold_high
                    ),
                    schedule=deepcopy(zone.schedule),
                )
            )

        return LocationConfig(
            location=Location(
                name=location_name,
                zones=tuple(validated_zones),
            )
        )