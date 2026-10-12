import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, insert, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.infrastructure.models import (
    AutomationRuleRow,
    DeviceRow,
    LocationRow,
    ReadingRow,
    ZoneRow,
)


@pytest.fixture
def api():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is required for API tests")

    if make_url(url).database != "greenhouse_phase3_test":
        pytest.fail("API tests must use greenhouse_phase3_test")

    from app.infrastructure.db import get_session
    from app.main import app

    engine = create_engine(url)

    try:
        with engine.connect() as connection:
            transaction = connection.begin()

            def test_session():
                with Session(
                    bind=connection,
                    join_transaction_mode="create_savepoint",
                ) as session:
                    yield session

            previous = app.dependency_overrides.copy()
            app.dependency_overrides[get_session] = test_session

            try:
                with TestClient(app) as client:
                    yield client, connection
            finally:
                app.dependency_overrides.clear()
                app.dependency_overrides.update(previous)
                transaction.rollback()
    finally:
        engine.dispose()


def create_location(connection):
    location_id = uuid4()
    connection.execute(
        insert(LocationRow).values(
            id=location_id,
            name=f"Automation test {location_id}",
        )
    )
    return location_id


def create_zone(connection, location_id, low=0.2, high=0.8):
    zone_id = uuid4()
    connection.execute(
        insert(ZoneRow).values(
            id=zone_id,
            location_id=location_id,
            name=f"Zone {zone_id}",
            moisture_threshold_low=low,
            moisture_threshold_high=high,
        )
    )
    return zone_id


def create_sensor(
    connection,
    location_id=None,
    zone_id=None,
    device_type="moisture_sensor",
):
    device_id = uuid4()
    connection.execute(
        insert(DeviceRow).values(
            id=device_id,
            device_type=device_type,
            role="sensor",
            display_name="Automation test sensor",
            location_id=location_id,
            zone_id=zone_id,
            tracking_enabled=False,
        )
    )
    return device_id


def add_reading(
    connection,
    device_id,
    value,
    seconds=0,
    source="simulation",
    unit="vwc",
):
    connection.execute(
        insert(ReadingRow).values(
            id=uuid4(),
            device_id=device_id,
            value=value,
            unit=unit,
            source=source,
            recorded_at=(
                datetime(2026, 1, 1, tzinfo=timezone.utc)
                + timedelta(seconds=seconds)
            ),
        )
    )


def automation_url(location_id):
    return f"/api/locations/{location_id}/automation"


def save_strategy(client, location_id, key):
    response = client.put(
        automation_url(location_id),
        json={"strategy_key": key},
    )
    assert response.status_code == 200
    return response.json()


def evaluate(client, location_id):
    response = client.post(
        f"{automation_url(location_id)}/evaluate"
    )
    assert response.status_code == 200
    return response.json()


def test_strategy_is_persisted_and_updated_in_one_row(api):
    client, connection = api
    location_id = create_location(connection)
    other_id = create_location(connection)

    save_strategy(client, location_id, "conservative")
    save_strategy(client, location_id, "aggressive")

    response = client.get(automation_url(location_id))
    assert response.status_code == 200
    assert response.json()["strategy_key"] == "aggressive"

    saved_key = connection.scalar(
        select(AutomationRuleRow.strategy_key).where(
            AutomationRuleRow.location_id == location_id
        )
    )
    assert saved_key == "aggressive"

    count = connection.scalar(
        select(func.count())
        .select_from(AutomationRuleRow)
        .where(AutomationRuleRow.location_id == location_id)
    )
    assert count == 1

    other = client.get(automation_url(other_id))
    assert other.status_code == 200
    assert other.json()["strategy_key"] is None


def test_evaluation_uses_saved_key_for_same_reading(api):
    client, connection = api
    location_id = create_location(connection)
    zone_id = create_zone(connection, location_id)
    sensor_id = create_sensor(connection, location_id, zone_id)
    add_reading(connection, sensor_id, 0.4)

    save_strategy(client, location_id, "conservative")
    conservative = evaluate(client, location_id)

    save_strategy(client, location_id, "aggressive")
    aggressive = evaluate(client, location_id)

    assert conservative["strategy_key"] == "conservative"
    assert aggressive["strategy_key"] == "aggressive"
    assert conservative["action"] == "wait"
    assert aggressive["action"] == "irrigate"

    for result in (conservative, aggressive):
        assert len(result["zones"]) == 1
        assert result["zones"][0]["latest_moisture"] == pytest.approx(0.4)

    # Evaluation must not generate another sensor reading.
    count = connection.scalar(
        select(func.count())
        .select_from(ReadingRow)
        .where(ReadingRow.device_id == sensor_id)
    )
    assert count == 1


def test_unknown_key_returns_400_without_changing_saved_key(api):
    client, connection = api
    location_id = create_location(connection)
    save_strategy(client, location_id, "conservative")

    response = client.put(
        automation_url(location_id),
        json={"strategy_key": "unknown"},
    )
    assert response.status_code == 400

    saved = client.get(automation_url(location_id))
    assert saved.json()["strategy_key"] == "conservative"


def test_missing_location_returns_404(api):
    client, _ = api
    url = automation_url(uuid4())

    assert client.get(url).status_code == 404
    assert client.put(
        url,
        json={"strategy_key": "conservative"},
    ).status_code == 404
    assert client.post(f"{url}/evaluate").status_code == 404


def test_unconfigured_location_and_location_without_zones(api):
    client, connection = api
    location_id = create_location(connection)
    url = automation_url(location_id)

    settings = client.get(url)
    assert settings.status_code == 200
    assert settings.json()["strategy_key"] is None
    assert client.post(f"{url}/evaluate").status_code == 400

    save_strategy(client, location_id, "conservative")
    result = evaluate(client, location_id)

    assert result["action"] == "wait"
    assert result["zones"] == []
    assert "no zones" in result["reason"].lower()


def test_latest_reading_is_selected_only_from_each_zone(api):
    client, connection = api
    location_id = create_location(connection)

    first_zone = create_zone(connection, location_id)
    second_zone = create_zone(connection, location_id)
    empty_zone = create_zone(connection, location_id)
    unread_zone = create_zone(connection, location_id)

    first_sensor = create_sensor(connection, location_id, first_zone)
    newer_sensor = create_sensor(connection, location_id, first_zone)
    second_sensor = create_sensor(connection, location_id, second_zone)
    create_sensor(connection, location_id, unread_zone)

    # The newest reading across both sensors in the first zone wins.
    add_reading(connection, first_sensor, 0.1, seconds=0)
    add_reading(
        connection, newer_sensor, 0.4, seconds=10, source="mqtt"
    )
    add_reading(connection, second_sensor, 0.9, seconds=20)

    # A newer light reading in the same zone must not be used.
    light = create_sensor(
        connection, location_id, first_zone, "light_sensor"
    )
    add_reading(connection, light, 1000, seconds=30, unit="lux")

    # Neither unassigned sensors nor another location may affect results.
    unassigned = create_sensor(connection, location_id)
    add_reading(connection, unassigned, 0.01, seconds=40)

    other_location = create_location(connection)
    other_zone = create_zone(connection, other_location)
    other_sensor = create_sensor(connection, other_location, other_zone)
    add_reading(connection, other_sensor, 0.02, seconds=50)

    save_strategy(client, location_id, "aggressive")
    result = evaluate(client, location_id)
    zones = {zone["zone_id"]: zone for zone in result["zones"]}

    assert len(zones) == 4

    first = zones[str(first_zone)]
    assert first["latest_moisture"] == pytest.approx(0.4)
    assert first["action"] == "irrigate"

    second = zones[str(second_zone)]
    assert second["latest_moisture"] == pytest.approx(0.9)
    assert second["action"] == "wait"

    empty = zones[str(empty_zone)]
    assert empty["latest_moisture"] is None
    assert empty["action"] == "wait"
    assert "no moisture sensor" in empty["reason"].lower()

    unread = zones[str(unread_zone)]
    assert unread["latest_moisture"] is None
    assert unread["action"] == "wait"
    assert "no saved moisture reading" in unread["reason"].lower()