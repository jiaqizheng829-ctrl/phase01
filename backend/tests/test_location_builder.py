import pytest

from app.domain.locations.config_builder import LocationConfigBuilder
from app.domain.locations.errors import ConfigurationError


def test_build_valid_configuration():
    config = (
        LocationConfigBuilder()
        .set_location_name("Main greenhouse")
        .add_zone("Zone A", 0.2, 0.8)
        .build()
    )

    assert config.location.name == "Main greenhouse"
    assert config.location.id is None
    assert len(config.location.zones) == 1

    zone = config.location.zones[0]
    assert zone.name == "Zone A"
    assert zone.moisture_threshold_low == 0.2
    assert zone.moisture_threshold_high == 0.8
    assert zone.id is None


def test_missing_location_name():
    builder = LocationConfigBuilder().add_zone("Zone A", 0.2, 0.8)

    with pytest.raises(ConfigurationError):
        builder.build()


def test_no_zones():
    builder = LocationConfigBuilder().set_location_name("Main greenhouse")

    with pytest.raises(ConfigurationError):
        builder.build()


@pytest.mark.parametrize(
    "low, high",
    [
        (0.8, 0.2),
        (0.5, 0.5),
        (-0.1, 0.8),
        (0.2, 1.1),
        (float("nan"), 0.8),
    ],
)
def test_invalid_thresholds(low, high):
    builder = (
        LocationConfigBuilder()
        .set_location_name("Main greenhouse")
        .add_zone("Zone A", low, high)
    )

    with pytest.raises(ConfigurationError):
        builder.build()


def test_duplicate_zone_names():
    builder = (
        LocationConfigBuilder()
        .set_location_name("Main greenhouse")
        .add_zone("Zone A", 0.2, 0.8)
        .add_zone("Zone A", 0.3, 0.7)
    )

    with pytest.raises(ConfigurationError):
        builder.build()


def test_blank_zone_name():
    builder = (
        LocationConfigBuilder()
        .set_location_name("Main greenhouse")
        .add_zone("   ", 0.2, 0.8)
    )

    with pytest.raises(ConfigurationError):
        builder.build()


def test_built_configuration_is_independent():
    schedule = {"watering": {"hour": 8}}
    builder = (
        LocationConfigBuilder()
        .set_location_name("Main greenhouse")
        .add_zone("Zone A", 0.2, 0.8, schedule)
    )

    first = builder.build()
    schedule["watering"]["hour"] = 20

    builder.set_location_name("Another location")
    builder.add_zone("Zone B", 0.3, 0.7)
    second = builder.build()
    second.location.zones[0].schedule["watering"]["hour"] = 12

    assert first.location.name == "Main greenhouse"
    assert len(first.location.zones) == 1
    assert first.location.zones[0].schedule == {"watering": {"hour": 8}}