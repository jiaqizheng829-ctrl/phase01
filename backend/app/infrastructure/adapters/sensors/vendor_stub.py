from datetime import datetime, timezone
from math import isfinite

from app.domain.devices.entity import Device
from app.domain.sensors.ports import SensorPort
from app.domain.sensors.reading import Reading, ReadingError


class VendorStubClient:
    """Pretend vendor driver with its own response format."""

    def fetch(self, sensor_type: str) -> dict:
        if sensor_type == "moisture_sensor":
            return {
                "status_code": 0,
                "measurement": 41.0,
                "measurement_unit": "percent",
            }

        if sensor_type == "light_sensor":
            return {
                "status_code": 0,
                "measurement": 1250.0,
                "measurement_unit": "lx",
            }

        raise ReadingError(f"Unsupported sensor type: {sensor_type}")


class VendorStubSensorAdapter(SensorPort):
    def __init__(self, client: VendorStubClient | None = None):
        self.client = client if client is not None else VendorStubClient()

    def read(self, device: Device) -> Reading:
        if device.id is None:
            raise ReadingError("The device must be saved before reading.")

        if device.role != "sensor":
            raise ReadingError("Only sensors can produce readings.")

        raw = self.client.fetch(device.device_type)

        if raw.get("status_code") != 0:
            raise ReadingError("The vendor driver reported an error.")

        value = raw.get("measurement")
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
        ):
            raise ReadingError("The vendor returned an invalid value.")

        raw_unit = raw.get("measurement_unit")

        if device.device_type == "moisture_sensor":
            if raw_unit != "percent" or not 0 <= value <= 100:
                raise ReadingError("Invalid vendor moisture reading.")
            value = value / 100
            unit = "vwc"
        elif device.device_type == "light_sensor":
            if raw_unit != "lx" or value < 0:
                raise ReadingError("Invalid vendor light reading.")
            unit = "lux"
        else:
            raise ReadingError(
                f"Unsupported sensor type: {device.device_type}"
            )

        return Reading(
            device_id=device.id,
            value=float(value),
            unit=unit,
            source="vendor",
            recorded_at=datetime.now(timezone.utc),
        )