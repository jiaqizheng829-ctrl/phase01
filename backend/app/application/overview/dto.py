from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class LocationSummaryDto(BaseModel):
    id: UUID
    name: str


class DeviceCountsDto(BaseModel):
    sensor: int = 0
    actuator: int = 0


class OverviewDeviceDto(BaseModel):
    id: UUID
    device_type: str
    role: Literal["sensor", "actuator"]
    display_name: str


class LatestReadingDto(BaseModel):
    device_id: UUID
    value: float
    unit: str
    recorded_at: datetime
    tracking_enabled: bool
    sampling_interval_seconds: int


class OverviewZoneDto(BaseModel):
    id: UUID
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    devices: list[OverviewDeviceDto] = Field(default_factory=list)
    latest_readings: list[LatestReadingDto] = Field(default_factory=list)


class RecommendationDto(BaseModel):
    action: Literal["irrigate", "wait"]
    reason: str


class LocationOverviewDto(BaseModel):
    location: LocationSummaryDto
    device_counts: DeviceCountsDto
    zones: list[OverviewZoneDto]
    strategy_key: str | None = None
    last_recommendation: RecommendationDto | None = None