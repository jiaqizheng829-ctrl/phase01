from typing import Protocol
from uuid import UUID

from app.application.automation.dto import EvaluationDto
from app.application.overview.dto import (
    DeviceCountsDto,
    LatestReadingDto,
    LocationOverviewDto,
    LocationSummaryDto,
    OverviewDeviceDto,
    OverviewZoneDto,
    RecommendationDto,
)


class OverviewLocationNotFoundError(LookupError):
    pass


class OverviewStore(Protocol):
    def get_location_with_zones(
        self,
        location_id: UUID,
    ) -> tuple[LocationSummaryDto, list[OverviewZoneDto]] | None:
        ...

    def list_assigned_devices(
        self,
        location_id: UUID,
    ) -> list[tuple[UUID, OverviewDeviceDto]]:
        ...

    def latest_readings_for_devices(
        self,
        device_ids: list[UUID],
    ) -> list[LatestReadingDto]:
        ...


class StrategyKeyStore(Protocol):
    def get_strategy_key(self, location_id: UUID) -> str | None:
        ...


class AutomationEvaluator(Protocol):
    def evaluate(self, location_id: UUID) -> EvaluationDto:
        ...


class LocationOverviewFacade:
    def __init__(
        self,
        overview: OverviewStore,
        rules: StrategyKeyStore,
        automation: AutomationEvaluator,
    ) -> None:
        self.overview = overview
        self.rules = rules
        self.automation = automation

    def get_overview(self, location_id: UUID) -> LocationOverviewDto:
        location_data = self.overview.get_location_with_zones(
            location_id
        )

        if location_data is None:
            raise OverviewLocationNotFoundError("Location not found.")

        location, zones = location_data
        zones_by_id = {zone.id: zone for zone in zones}

        assigned_devices = self.overview.list_assigned_devices(
            location_id
        )

        counts = DeviceCountsDto()
        device_zone_ids: dict[UUID, UUID] = {}

        for zone_id, device in assigned_devices:
            zones_by_id[zone_id].devices.append(device)
            device_zone_ids[device.id] = zone_id

            if device.role == "sensor":
                counts.sensor += 1
            elif device.role == "actuator":
                counts.actuator += 1

        readings = self.overview.latest_readings_for_devices(
            list(device_zone_ids)
        )

        for reading in readings:
            zone_id = device_zone_ids[reading.device_id]
            zones_by_id[zone_id].latest_readings.append(reading)

        strategy_key = self.rules.get_strategy_key(location_id)
        recommendation = None

        if strategy_key is not None:
            evaluation = self.automation.evaluate(location_id)

            # Use the key actually used by the evaluation service.
            strategy_key = evaluation.strategy_key
            recommendation = RecommendationDto(
                action=evaluation.action,
                reason=evaluation.reason,
            )

        return LocationOverviewDto(
            location=location,
            device_counts=counts,
            zones=zones,
            strategy_key=strategy_key,
            last_recommendation=recommendation,
        )