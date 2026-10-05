from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.application.readings.service import ReadingIngest
from app.domain.devices.entity import Device
from app.domain.sensors.ports import SensorPort
from app.domain.sensors.reading import Reading


@dataclass(frozen=True)
class SamplingDevice:
    device: Device
    sampling_interval_seconds: int
    tracking_enabled: bool


class SamplingDeviceSource(Protocol):
    def list_sampling_devices(self) -> list[SamplingDevice]:
        ...


class LatestReadingSource(Protocol):
    def latest_for_device(self, device_id: UUID) -> Reading | None:
        ...


class SimulationSampler:
    def __init__(
        self,
        devices: SamplingDeviceSource,
        readings: LatestReadingSource,
        ingest: ReadingIngest,
        select_adapter: Callable[[Device], SensorPort],
    ):
        self.devices = devices
        self.readings = readings
        self.ingest = ingest
        self.select_adapter = select_adapter

    def run_once(self, now: datetime) -> int:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("Sampler time must include a timezone.")

        recorded_count = 0

        for settings in self.devices.list_sampling_devices():
            device = settings.device

            if device.id is None or device.role != "sensor":
                continue

            if not settings.tracking_enabled:
                continue

            if device.default_config.get("protocol") != "simulation":
                continue

            latest = self.readings.latest_for_device(device.id)

            if latest is not None:
                elapsed = (now - latest.recorded_at).total_seconds()

                if elapsed < settings.sampling_interval_seconds:
                    continue

            adapter = self.select_adapter(device)
            reading = adapter.read(device)

            # Use the tick time so tests can control time without sleeping.
            reading = replace(reading, recorded_at=now)

            self.ingest.record(device.id, reading)
            recorded_count += 1

        return recorded_count