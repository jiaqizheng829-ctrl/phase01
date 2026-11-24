from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from app.application.readings.dto import ReadingDto, to_reading_dto
from app.domain.devices.entity import Device
from app.domain.events.bus import EventBus
from app.domain.events.events import ReadingCreated
from app.domain.sensors.ports import SensorPort
from app.domain.sensors.reading import Reading, ReadingError


class DeviceNotFoundError(LookupError):
    pass


class DeviceReader(Protocol):
    def get(self, device_id: UUID) -> Device | None:
        ...


class ReadingStore(Protocol):
    def insert(self, reading: Reading) -> Reading:
        ...

    def list_for_device(
        self,
        device_id: UUID,
        limit: int = 20,
    ) -> list[Reading]:
        ...


class ReadingIngest:
    def __init__(
        self,
        devices: DeviceReader,
        readings: ReadingStore,
        select_adapter: Callable[[Device], SensorPort],
        *,
        bus: EventBus | None = None,
        is_tracking_enabled: Callable[[UUID], bool] | None = None,
    ):
        if bus is not None and is_tracking_enabled is None:
            raise ValueError(
                "is_tracking_enabled is required when a bus is supplied."
            )

        self.devices = devices
        self.readings = readings
        self.select_adapter = select_adapter
        self.bus = bus
        self.is_tracking_enabled = is_tracking_enabled

    def take_reading(self, device_id: UUID) -> ReadingDto:
        device = self._get_sensor(device_id)
        adapter = self.select_adapter(device)
        reading = adapter.read(device)
        return self.record(device_id, reading)

    def record(
        self,
        device_id: UUID,
        reading: Reading,
    ) -> ReadingDto:
        device = self._get_sensor(device_id)

        if reading.device_id != device_id:
            raise ReadingError("Reading belongs to another device.")

        if device.device_type == "moisture_sensor":
            if reading.unit != "vwc" or not 0 <= reading.value <= 1:
                raise ReadingError(
                    "Moisture must be between 0 and 1, using vwc."
                )
        elif device.device_type == "light_sensor":
            if reading.unit != "lux" or reading.value < 0:
                raise ReadingError(
                    "Light must be non-negative, using lux."
                )
        else:
            raise ReadingError(
                f"Unsupported sensor type: {device.device_type}"
            )

        should_publish = (
            self.bus is not None
            and self.is_tracking_enabled is not None
            and self.is_tracking_enabled(device_id)
        )

        zone_id = device.zone_id
        location_id = device.location_id if zone_id is not None else None

        # ReadingRepository.insert commits before returning.
        # Tracking off still permits storing a supplied reading.
        saved = self.readings.insert(reading)
        result = to_reading_dto(saved)

        if should_publish and self.bus is not None:
            self.bus.publish(
                ReadingCreated(
                    device_id=saved.device_id,
                    location_id=location_id,
                    zone_id=zone_id,
                    value=float(saved.value),
                    unit=saved.unit,
                    source=saved.source,
                    recorded_at=saved.recorded_at,
                )
            )

        return result

    def list_readings(
        self,
        device_id: UUID,
        limit: int = 20,
    ) -> list[ReadingDto]:
        self._get_sensor(device_id)

        if not 1 <= limit <= 100:
            raise ReadingError("Limit must be between 1 and 100.")

        return [
            to_reading_dto(reading)
            for reading in self.readings.list_for_device(
                device_id,
                limit=limit,
            )
        ]

    def _get_sensor(self, device_id: UUID) -> Device:
        device = self.devices.get(device_id)

        if device is None:
            raise DeviceNotFoundError("Device not found.")

        if device.role != "sensor":
            raise ReadingError("Only sensors can produce readings.")

        return device