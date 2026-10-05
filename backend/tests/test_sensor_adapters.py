from uuid import uuid4

import pytest

from app.domain.devices.entity import Device
from app.domain.sensors.reading import ReadingError
from app.infrastructure.adapters.sensors.simulation import (
    SimulationSensorAdapter,
)
from app.infrastructure.adapters.sensors.vendor_stub import (
    VendorStubClient,
    VendorStubSensorAdapter,
)
from app.infrastructure.adapters.sensors.mqtt import MqttSensorAdapter
from app.infrastructure.adapters.sensors.selector import (
    select_sensor_adapter,
)
from app.infrastructure.adapters.actuators.simulation import (
    SimulationActuatorAdapter,
)


def make_sensor(device_type="moisture_sensor", config=None):
    return Device(
        id=uuid4(),
        device_type=device_type,
        role="sensor",
        device_family="simulation",
        display_name="Test sensor",
        default_config=(
            config if config is not None
            else {"protocol": "simulation"}
        ),
    )


@pytest.mark.parametrize(
    "device_type,unit,minimum,maximum",
    [
        ("moisture_sensor", "vwc", 0.2, 0.6),
        ("light_sensor", "lux", 200, 2000),
    ],
)
def test_simulation_reading_in_range(device_type, unit, minimum, maximum):
    device = make_sensor(device_type)
    adapter = SimulationSensorAdapter()

    for _ in range(50):
        reading = adapter.read(device)

        assert reading.device_id == device.id
        assert minimum <= reading.value <= maximum
        assert reading.unit == unit
        assert reading.source == "simulation"
        assert reading.recorded_at.utcoffset() is not None


def test_vendor_adapter_translates_custom_raw_payload():
    class CustomVendorClient(VendorStubClient):
        def fetch(self, sensor_type):
            return {
                "status_code": 0,
                "measurement": 57.0,
                "measurement_unit": "percent",
            }

    device = make_sensor()
    adapter = VendorStubSensorAdapter(CustomVendorClient())

    reading = adapter.read(device)

    assert reading.device_id == device.id
    assert reading.value == pytest.approx(0.57)
    assert reading.unit == "vwc"
    assert reading.source == "vendor"


def test_vendor_adapter_rejects_driver_error():
    class FailedVendorClient(VendorStubClient):
        def fetch(self, sensor_type):
            return {"status_code": 9}

    adapter = VendorStubSensorAdapter(FailedVendorClient())

    with pytest.raises(ReadingError):
        adapter.read(make_sensor())


@pytest.mark.parametrize(
    "device_type,payload",
    [
        ("moisture_sensor", {"value": 0.41, "unit": "vwc"}),
        ("light_sensor", {"value": 980, "unit": "lux"}),
    ],
)
def test_mqtt_translates_without_network(monkeypatch, device_type, payload):
    def forbid_network(*args, **kwargs):
        raise AssertionError("MQTT translation must not open a socket.")

    monkeypatch.setattr("socket.socket", forbid_network)
    monkeypatch.setattr("socket.create_connection", forbid_network)

    device = make_sensor(device_type, {"protocol": "mqtt"})
    reading = MqttSensorAdapter().translate(device, payload)

    assert reading.device_id == device.id
    assert reading.value == payload["value"]
    assert reading.unit == payload["unit"]
    assert reading.source == "mqtt"
    assert reading.recorded_at.utcoffset() is not None


@pytest.mark.parametrize(
    "payload",
    [
        {"value": True, "unit": "vwc"},
        {"value": "0.41", "unit": "vwc"},
        {"value": float("nan"), "unit": "vwc"},
        {"value": float("inf"), "unit": "vwc"},
        {"value": 1.5, "unit": "vwc"},
        {"value": 0.41, "unit": "percent"},
        {},
    ],
)
def test_mqtt_rejects_invalid_payload(payload):
    with pytest.raises(ReadingError):
        MqttSensorAdapter().translate(make_sensor(), payload)


def test_selector_chooses_simulation_and_vendor():
    simulation = make_sensor()
    vendor = make_sensor(
        config={"protocol": "simulation", "driver": "vendor_stub"},
    )

    assert isinstance(
        select_sensor_adapter(simulation),
        SimulationSensorAdapter,
    )
    assert isinstance(
        select_sensor_adapter(vendor),
        VendorStubSensorAdapter,
    )


def test_selector_does_not_generate_mqtt_readings():
    device = make_sensor(config={"protocol": "mqtt"})

    with pytest.raises(ReadingError, match="incoming payload"):
        select_sensor_adapter(device)


def test_simulation_actuator_keeps_independent_payload():
    adapter = SimulationActuatorAdapter()
    device_id = uuid4()
    payload = {"duration_seconds": 10}

    adapter.apply(device_id, "turn_on", payload)
    payload["duration_seconds"] = 99

    assert adapter.commands == [
        {
            "device_id": device_id,
            "command": "turn_on",
            "payload": {"duration_seconds": 10},
        }
    ]