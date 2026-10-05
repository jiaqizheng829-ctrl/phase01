from abc import ABC, abstractmethod

from app.domain.devices.entity import Device
from app.domain.sensors.reading import Reading


class SensorPort(ABC):
    @abstractmethod
    def read(self, device: Device) -> Reading:
        """Read a sensor and return a normalized reading."""
        raise NotImplementedError