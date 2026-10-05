from app.domain.sensors import LightSensorCreator, MoistureSensorCreator


def test_moisture_creator_uses_moisture_defaults() -> None:
    sensor = MoistureSensorCreator().create_sensor()

    assert sensor.device_type == "moisture_sensor"
    assert sensor.default_config["protocol"] == "simulation"
    assert sensor.default_config["unit"] == "vwc"
    assert sensor.default_config["minimum"] == 0
    assert sensor.default_config["maximum"] == 1
    assert sensor.default_config["warning_below"] == 0.3
    assert sensor.sampling_interval_seconds == 300
    assert sensor.tracking_enabled is True


def test_light_creator_has_different_defaults() -> None:
    moisture = MoistureSensorCreator().create_sensor()
    light = LightSensorCreator().create_sensor()

    assert light.device_type == "light_sensor"
    assert light.default_config["protocol"] == "simulation"
    assert light.default_config["unit"] == "lux"
    assert light.default_config != moisture.default_config
    assert light.sampling_interval_seconds == 300
    assert light.tracking_enabled is True