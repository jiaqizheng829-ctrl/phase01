from app.domain.devices.entity import Device
from app.domain.sensors.ports import SensorPort
from app.domain.sensors.reading import ReadingError
from app.infrastructure.adapters.sensors.simulation import (
    SimulationSensorAdapter,
)
from app.infrastructure.adapters.sensors.vendor_stub import (
    VendorStubSensorAdapter,
)


def select_sensor_adapter(device: Device) -> SensorPort:
    if device.role != "sensor":
        raise ReadingError("Only sensors can produce readings.")

    protocol = device.default_config.get("protocol")
    driver = device.default_config.get("driver")

    if protocol == "mqtt":
        raise ReadingError(
            "MQTT sensors require an incoming payload. "
            "Read now is not available for this device."
        )

    if protocol != "simulation":
        raise ReadingError(
            f"Unsupported sensor protocol: {protocol}"
        )

    if driver == "vendor_stub":
        return VendorStubSensorAdapter()

    if driver is not None:
        raise ReadingError(
            f"Unsupported sensor driver: {driver}"
        )

    return SimulationSensorAdapter()