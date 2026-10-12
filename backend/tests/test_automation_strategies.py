from uuid import uuid4

import pytest

from app.domain.automation.context import LocationAutomationContext
from app.domain.automation.strategy import (
    UnknownStrategyError,
    get_strategy,
)


def make_context(
    moisture: float | None,
    *,
    has_sensor: bool = True,
    low: float = 0.2,
    high: float = 0.8,
) -> LocationAutomationContext:
    return LocationAutomationContext(
        location_id=uuid4(),
        zone_id=uuid4(),
        moisture_threshold_low=low,
        moisture_threshold_high=high,
        latest_moisture=moisture,
        has_moisture_sensor=has_sensor,
    )


def test_same_context_produces_different_recommendations():
    context = make_context(0.4)

    conservative = get_strategy("conservative").decide(context)
    aggressive = get_strategy("aggressive").decide(context)

    assert conservative.action == "wait"
    assert aggressive.action == "irrigate"
    assert conservative.reason
    assert aggressive.reason


@pytest.mark.parametrize(
    "key,moisture,expected",
    [
        ("conservative", 0.19, "irrigate"),
        ("conservative", 0.2, "wait"),
        ("conservative", 0.8, "wait"),
        ("aggressive", 0.49, "irrigate"),
        ("aggressive", 0.5, "wait"),
        ("aggressive", 0.8, "wait"),
    ],
)
def test_threshold_boundaries(key, moisture, expected):
    result = get_strategy(key).decide(make_context(moisture))

    assert result.action == expected


@pytest.mark.parametrize("key", ["conservative", "aggressive"])
def test_zone_without_sensor_waits(key):
    context = make_context(None, has_sensor=False)

    result = get_strategy(key).decide(context)

    assert result.action == "wait"
    assert "no moisture sensor" in result.reason.lower()


@pytest.mark.parametrize("key", ["conservative", "aggressive"])
def test_sensor_without_saved_reading_waits(key):
    context = make_context(None)

    result = get_strategy(key).decide(context)

    assert result.action == "wait"
    assert "no saved moisture reading" in result.reason.lower()


@pytest.mark.parametrize(
    "key,moisture",
    [
        ("conservative", 0.3),
        ("aggressive", 0.55),
    ],
)
def test_strategy_uses_zone_thresholds(key, moisture):
    strategy = get_strategy(key)

    original = strategy.decide(
        make_context(moisture, low=0.2, high=0.8)
    )
    changed = strategy.decide(
        make_context(moisture, low=0.4, high=0.8)
    )

    assert original.action == "wait"
    assert changed.action == "irrigate"


def test_unknown_strategy_is_rejected():
    with pytest.raises(UnknownStrategyError):
        get_strategy("unknown")


@pytest.mark.parametrize(
    "low,high",
    [
        (-0.1, 0.8),
        (0.2, 1.1),
        (0.5, 0.5),
        (0.8, 0.2),
    ],
)
def test_invalid_thresholds_are_rejected(low, high):
    with pytest.raises(ValueError):
        make_context(0.4, low=low, high=high)


@pytest.mark.parametrize(
    "moisture",
    [-0.1, 1.1, float("nan"), float("inf")],
)
def test_invalid_moisture_is_rejected(moisture):
    with pytest.raises(ValueError):
        make_context(moisture)


def test_reading_without_sensor_is_rejected():
    with pytest.raises(ValueError):
        make_context(0.4, has_sensor=False)