from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StrictBool, StrictInt

from app.domain.sensors.reading import Reading


class ReadingDto(BaseModel):
    device_id: UUID
    value: float
    unit: str
    source: str
    recorded_at: datetime


class SamplingUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sampling_interval_seconds: StrictInt
    tracking_enabled: StrictBool


class SamplingDto(BaseModel):
    device_id: UUID
    sampling_interval_seconds: int
    tracking_enabled: bool


def to_reading_dto(reading: Reading) -> ReadingDto:
    return ReadingDto(
        device_id=reading.device_id,
        value=reading.value,
        unit=reading.unit,
        source=reading.source,
        recorded_at=reading.recorded_at,
    )