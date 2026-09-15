from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class Sensor:
    id: UUID | None
    device_type: str
    display_name: str
    default_config: dict[str, Any]


class SensorCreator(ABC):
    key: str

    @abstractmethod
    def create_sensor(self, display_name: str | None = None) -> Sensor:
        pass


class MoistureSensorCreator(SensorCreator):
    key = "moisture"

    def create_sensor(self, display_name: str | None = None) -> Sensor:
        return Sensor(
            id=None,
            device_type="moisture_sensor",
            display_name=display_name or "Moisture sensor",
            default_config={
                "unit": "%",
                "minimum": 0,
                "maximum": 100,
                "warning_below": 30,
            },
        )


class LightSensorCreator(SensorCreator):
    key = "light"

    def create_sensor(self, display_name: str | None = None) -> Sensor:
        return Sensor(
            id=None,
            device_type="light_sensor",
            display_name=display_name or "Light sensor",
            default_config={
                "unit": "lux",
                "minimum": 0,
                "maximum": 100000,
                "warning_below": 5000,
            },
        )


SENSOR_CREATORS: dict[str, SensorCreator] = {
    "moisture": MoistureSensorCreator(),
    "light": LightSensorCreator(),
}


def get_sensor_creator(sensor_type: str) -> SensorCreator:
    try:
        return SENSOR_CREATORS[sensor_type]
    except KeyError as error:
        raise ValueError(f"Unknown sensor type: {sensor_type}") from error
