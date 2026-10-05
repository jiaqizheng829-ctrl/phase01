from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from app.application.readings.dto import ReadingDto, to_reading_dto
from app.domain.devices.entity import Device
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
    ):
        self.devices = devices
        self.readings = readings
        self.select_adapter = select_adapter

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

        saved = self.readings.insert(reading)
        return to_reading_dto(saved)

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