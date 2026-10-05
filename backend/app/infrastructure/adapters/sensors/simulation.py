from datetime import datetime, timezone
from random import uniform

from app.domain.devices.entity import Device
from app.domain.sensors.ports import SensorPort
from app.domain.sensors.reading import Reading, ReadingError


class SimulationSensorAdapter(SensorPort):
    def read(self, device: Device) -> Reading:
        if device.id is None:
            raise ReadingError("The device must be saved before reading.")

        if device.role != "sensor":
            raise ReadingError("Only sensors can produce readings.")

        if device.device_type == "moisture_sensor":
            value = round(uniform(0.2, 0.6), 4)
            unit = "vwc"
        elif device.device_type == "light_sensor":
            value = round(uniform(200, 2000), 2)
            unit = "lux"
        else:
            raise ReadingError(
                f"Unsupported sensor type: {device.device_type}"
            )

        return Reading(
            device_id=device.id,
            value=value,
            unit=unit,
            source="simulation",
            recorded_at=datetime.now(timezone.utc),
        )