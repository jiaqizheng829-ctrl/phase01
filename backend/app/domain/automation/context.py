from dataclasses import dataclass
from math import isfinite
from uuid import UUID


@dataclass(frozen=True)
class LocationAutomationContext:
    location_id: UUID
    zone_id: UUID
    moisture_threshold_low: float
    moisture_threshold_high: float
    latest_moisture: float | None
    has_moisture_sensor: bool = True

    def __post_init__(self) -> None:
        low = self.moisture_threshold_low
        high = self.moisture_threshold_high

        if not (
            isfinite(low)
            and isfinite(high)
            and 0 <= low < high <= 1
        ):
            raise ValueError(
                "Moisture thresholds must satisfy 0 <= low < high <= 1."
            )

        if self.latest_moisture is not None:
            if not (
                isfinite(self.latest_moisture)
                and 0 <= self.latest_moisture <= 1
            ):
                raise ValueError(
                    "Latest moisture must be between 0 and 1."
                )

        if not self.has_moisture_sensor and self.latest_moisture is not None:
            raise ValueError(
                "A zone without a moisture sensor cannot have a reading."
            )