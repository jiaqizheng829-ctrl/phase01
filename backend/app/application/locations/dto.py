from uuid import UUID

from pydantic import BaseModel, Field


class ZoneCreateRequest(BaseModel):
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    schedule: dict = Field(default_factory=dict)


class LocationConfigCreateRequest(BaseModel):
    location_name: str
    zones: list[ZoneCreateRequest]


class LocationRead(BaseModel):
    id: UUID
    name: str


class ZoneRead(BaseModel):
    id: UUID
    location_id: UUID
    name: str
    moisture_threshold_low: float
    moisture_threshold_high: float
    schedule: dict


class LocationConfigRead(BaseModel):
    location: LocationRead
    zones: list[ZoneRead]


class ZoneUpdateRequest(BaseModel):
    name: str | None = None
    moisture_threshold_low: float | None = None
    moisture_threshold_high: float | None = None
    schedule: dict | None = None
