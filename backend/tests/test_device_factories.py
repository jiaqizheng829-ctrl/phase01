from collections import Counter

import pytest

from app.domain.devices.family_factory import (
    UnknownDeviceFamily,
    get_device_factory,
)
from app.domain.sensors import (
    LightSensorCreator,
    MoistureSensorCreator,
)


@pytest.mark.parametrize("family", ["simulation", "edge"])
def test_factory_creates_matching_four_device_kit(family):
    devices = get_device_factory(family).create_device_set()

    assert len(devices) == 4
    assert {device.device_family for device in devices} == {family}
    assert Counter(device.role for device in devices) == {
        "sensor": 2,
        "actuator": 2,
    }
    assert {device.device_type for device in devices} == {
        "moisture_sensor",
        "light_sensor",
        "water_pump",
        "grow_light",
    }
    assert all(device.id is None for device in devices)


def test_edge_has_different_configuration_from_simulation():
    simulation = {
        device.device_type: device
        for device in get_device_factory("simulation").create_device_set()
    }
    edge = {
        device.device_type: device
        for device in get_device_factory("edge").create_device_set()
    }

    assert simulation.keys() == edge.keys()

    for device_type in simulation:
        assert (
            simulation[device_type].default_config["protocol"]
            != edge[device_type].default_config["protocol"]
        )
        assert (
            simulation[device_type].display_name
            != edge[device_type].display_name
        )


@pytest.mark.parametrize("family", ["simulation", "edge"])
def test_family_factory_uses_phase2_sensor_creators(monkeypatch, family):
    calls = []

    for creator_class in (MoistureSensorCreator, LightSensorCreator):
        original = creator_class.create_sensor

        def tracked_create(
            self,
            display_name=None,
            original=original,
        ):
            calls.append(type(self))
            return original(self, display_name)

        monkeypatch.setattr(
            creator_class,
            "create_sensor",
            tracked_create,
        )

    get_device_factory(family).create_device_set()

    assert Counter(calls) == {
        MoistureSensorCreator: 1,
        LightSensorCreator: 1,
    }


def test_new_kits_do_not_share_mutable_configuration():
    factory = get_device_factory("simulation")
    first = factory.create_device_set()
    second = factory.create_device_set()

    first[0].default_config["protocol"] = "changed"

    assert second[0].default_config["protocol"] == "simulation"
    assert first[1].default_config["protocol"] == "simulation"


def test_unknown_family_is_rejected():
    with pytest.raises(UnknownDeviceFamily):
        get_device_factory("unknown")