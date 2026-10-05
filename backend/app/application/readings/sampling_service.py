from typing import Protocol
from uuid import UUID

from app.application.readings.dto import (
    SamplingDto,
    SamplingUpdateRequest,
)
from app.application.readings.service import DeviceNotFoundError
from app.domain.sensors.reading import ReadingError


class SamplingStore(Protocol):
    def update(
        self,
        device_id: UUID,
        interval: int,
        tracking_enabled: bool,
    ) -> tuple[UUID, int, bool] | None:
        ...


class SamplingService:
    def __init__(self, repository: SamplingStore):
        self.repository = repository

    def update(
        self,
        device_id: UUID,
        request: SamplingUpdateRequest,
    ) -> SamplingDto:
        interval = request.sampling_interval_seconds

        if not 5 <= interval <= 2147483647:
            raise ReadingError(
                "Sampling interval must be between 5 and "
                "2147483647 seconds."
            )

        result = self.repository.update(
            device_id,
            interval,
            request.tracking_enabled,
        )

        if result is None:
            raise DeviceNotFoundError("Device not found.")

        saved_id, saved_interval, saved_tracking = result

        return SamplingDto(
            device_id=saved_id,
            sampling_interval_seconds=saved_interval,
            tracking_enabled=saved_tracking,
        )