import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, insert
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.infrastructure.models import (
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


def test_unknown_location_returns_404(api):
    client, _ = api

    response = client.get(
        f"/api/locations/{uuid4()}/overview"
    )

    assert response.status_code == 404


def test_overview_returns_strategy_and_readings(api):
    client, connection = api

    location_id = uuid4()
    zone_id = uuid4()
    empty_zone_id = uuid4()
    sensor_id = uuid4()
    pump_id = uuid4()
    unassigned_id = uuid4()

    connection.execute(
        insert(LocationRow).values(
            id=location_id,
            name="Overview test location",
        )
    )

    for current_id, name in (
        (zone_id, "Zone with devices"),
        (empty_zone_id, "Empty zone"),
    ):
        connection.execute(
            insert(ZoneRow).values(
                id=current_id,
                location_id=location_id,
                name=name,
                moisture_threshold_low=0.2,
                moisture_threshold_high=0.8,
            )
        )

    for device_id, device_type, role, assigned_zone in (
        (sensor_id, "moisture_sensor", "sensor", zone_id),
        (pump_id, "water_pump", "actuator", zone_id),
        (unassigned_id, "moisture_sensor", "sensor", None),
    ):
        connection.execute(
            insert(DeviceRow).values(
                id=device_id,
                device_type=device_type,
                role=role,
                display_name=f"Test {device_type}",
                location_id=location_id,
                zone_id=assigned_zone,
                tracking_enabled=False,
                sampling_interval_seconds=45,
            )
        )

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def add_reading(device_id, value, seconds, source):
        connection.execute(
            insert(ReadingRow).values(
                id=uuid4(),
                device_id=device_id,
                value=value,
                unit="vwc",
                source=source,
                recorded_at=start + timedelta(seconds=seconds),
            )
        )

    add_reading(sensor_id, 0.1, 0, "simulation")
    add_reading(sensor_id, 0.4, 10, "mqtt")
    add_reading(unassigned_id, 0.01, 20, "simulation")

    overview_url = f"/api/locations/{location_id}/overview"
    automation_url = f"/api/locations/{location_id}/automation"

    def get_overview():
        response = client.get(overview_url)
        assert response.status_code == 200
        return response.json()

    result = get_overview()

    assert result["location"] == {
        "id": str(location_id),
        "name": "Overview test location",
    }
    assert result["device_counts"] == {
        "sensor": 1,
        "actuator": 1,
    }
    assert result["strategy_key"] is None
    assert result["last_recommendation"] is None

    zones = {zone["id"]: zone for zone in result["zones"]}
    assert set(zones) == {str(zone_id), str(empty_zone_id)}

    empty = zones[str(empty_zone_id)]
    assert empty["devices"] == []
    assert empty["latest_readings"] == []

    populated = zones[str(zone_id)]
    assert populated["moisture_threshold_low"] == pytest.approx(0.2)
    assert populated["moisture_threshold_high"] == pytest.approx(0.8)

    device_ids = {device["id"] for device in populated["devices"]}
    assert device_ids == {str(sensor_id), str(pump_id)}

    for zone in result["zones"]:
        assert all(
            device["id"] != str(unassigned_id)
            for device in zone["devices"]
        )
        assert all(
            reading["device_id"] != str(unassigned_id)
            for reading in zone["latest_readings"]
        )

    # The pump remains listed even though it has no reading.
    assert len(populated["latest_readings"]) == 1
    reading = populated["latest_readings"][0]
    assert reading["device_id"] == str(sensor_id)
    assert reading["value"] == pytest.approx(0.4)
    assert reading["unit"] == "vwc"
    assert reading["tracking_enabled"] is False
    assert reading["sampling_interval_seconds"] == 45
    assert datetime.fromisoformat(
        reading["recorded_at"].replace("Z", "+00:00")
    ) == start + timedelta(seconds=10)

    # Overview must reuse the existing evaluation service.
    for key, expected_action in (
        ("conservative", "wait"),
        ("aggressive", "irrigate"),
    ):
        saved = client.put(
            automation_url,
            json={"strategy_key": key},
        )
        assert saved.status_code == 200

        evaluation = client.post(f"{automation_url}/evaluate")
        assert evaluation.status_code == 200
        evaluated = evaluation.json()

        result = get_overview()
        assert result["strategy_key"] == key
        assert result["last_recommendation"] == {
            "action": evaluated["action"],
            "reason": evaluated["reason"],
        }
        assert result["last_recommendation"]["action"] == expected_action

    # A new reading must appear on the next GET without another save.
    add_reading(sensor_id, 0.9, 30, "simulation")

    updated = get_overview()
    updated_zone = next(
        zone for zone in updated["zones"]
        if zone["id"] == str(zone_id)
    )

    assert len(updated_zone["latest_readings"]) == 1
    assert updated_zone["latest_readings"][0]["value"] == pytest.approx(0.9)
    assert updated["strategy_key"] == "aggressive"
    assert updated["last_recommendation"]["action"] == "wait"