from datetime import datetime, timezone
from math import isfinite

from app.domain.devices.entity import Device
from app.domain.sensors.reading import Reading, ReadingError


class MqttSensorAdapter:
    def translate(self, device: Device, payload: dict) -> Reading:
        if device.id is None:
            raise ReadingError("The device must be saved before reading.")

        if device.role != "sensor":
            raise ReadingError("Only sensors can produce readings.")

        if not isinstance(payload, dict):
            raise ReadingError("MQTT payload must be an object.")

        value = payload.get("value")
        unit = payload.get("unit")

        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
        ):
            raise ReadingError("MQTT value must be a finite number.")

        if device.device_type == "moisture_sensor":
            if unit != "vwc":
                raise ReadingError("Moisture readings must use vwc.")
            if not 0 <= value <= 1:
                raise ReadingError("Moisture must be between 0 and 1.")
        elif device.device_type == "light_sensor":
            if unit != "lux":
                raise ReadingError("Light readings must use lux.")
            if value < 0:
                raise ReadingError("Light readings cannot be negative.")
        else:
            raise ReadingError(
                f"Unsupported sensor type: {device.device_type}"
            )

        return Reading(
            device_id=device.id,
            value=float(value),
            unit=unit,
            source="mqtt",
            recorded_at=datetime.now(timezone.utc),
        )