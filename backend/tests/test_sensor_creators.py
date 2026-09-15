from app.domain.sensors import LightSensorCreator, MoistureSensorCreator


def test_moisture_creator_uses_moisture_defaults() -> None:
    sensor = MoistureSensorCreator().create_sensor()

    assert sensor.device_type == "moisture_sensor"
    assert sensor.default_config["unit"] == "%"
    assert "warning_below" in sensor.default_config


def test_light_creator_has_different_defaults() -> None:
    moisture = MoistureSensorCreator().create_sensor()
    light = LightSensorCreator().create_sensor()

    assert light.device_type == "light_sensor"
    assert light.default_config["unit"] == "lux"
    assert light.default_config != moisture.default_config
