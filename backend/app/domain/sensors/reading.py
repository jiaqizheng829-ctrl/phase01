from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from uuid import UUID


class ReadingError(ValueError):
    """A sensor reading could not be produced or validated."""


@dataclass(frozen=True)
class Reading:
    device_id: UUID
    value: float
    unit: str
    source: str
    recorded_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.device_id, UUID):
            raise ReadingError("device_id must be a UUID.")

        if (
            isinstance(self.value, bool)
            or not isinstance(self.value, (int, float))
            or not isfinite(self.value)
        ):
            raise ReadingError("Reading value must be a finite number.")

        if not isinstance(self.unit, str) or not self.unit.strip():
            raise ReadingError("Reading unit is required.")

        if self.source not in ("simulation", "vendor", "mqtt"):
            raise ReadingError("Unknown reading source.")

        if (
            not isinstance(self.recorded_at, datetime)
            or self.recorded_at.tzinfo is None
            or self.recorded_at.utcoffset() is None
        ):
            raise ReadingError("recorded_at must include a timezone.")