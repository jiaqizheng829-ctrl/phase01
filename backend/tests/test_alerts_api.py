import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select, update
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.domain.events.events import (
    ActuatorStateChanged,
    CommandFailed,
    ReadingCreated,
)
from app.infrastructure.event_bus import build_event_bus
from app.infrastructure.models import AlertRow


@pytest.fixture
def api():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is required")

    if make_url(url).database != "greenhouse_phase3_test":
        pytest.fail("Tests must use greenhouse_phase3_test")

    from app.infrastructure.db import get_session
    from app.interfaces.api.event_dependencies import get_event_bus
    from app.main import app

    engine = create_engine(url)

    try:
        with engine.connect() as connection:
            transaction = connection.begin()
            connection.execute(delete(AlertRow))

            def subscriber_session():
                return Session(
                    bind=connection,
                    join_transaction_mode="create_savepoint",
                )

            def test_session():
                with subscriber_session() as session:
                    yield session

            bus = build_event_bus(subscriber_session)
            previous = app.dependency_overrides.copy()
            app.dependency_overrides[get_session] = test_session
            app.dependency_overrides[get_event_bus] = lambda: bus

            try:
                with TestClient(app) as client:
                    yield client, connection, bus
            finally:
                app.dependency_overrides.clear()
                app.dependency_overrides.update(previous)
                transaction.rollback()
    finally:
        engine.dispose()


def alerts(client, **params):
    response = client.get("/api/alerts", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def publish_failure(bus, message="Max run time exceeded"):
    bus.publish(CommandFailed(
        device_id=None,
        location_id=None,
        zone_id=None,
        command_type="stop_pump",
        message=message,
    ))


def test_empty_feed(api):
    client, _, _ = api
    assert alerts(client) == []


def test_failure_is_persisted_with_null_references(api):
    client, connection, bus = api
    publish_failure(bus)

    rows = alerts(client)
    assert len(rows) == 1
    row = rows[0]

    assert row["event_type"] == "command.failed"
    assert row["severity"] == "warning"
    assert row["message"] == "Max run time exceeded"
    assert row["status"] == "active"
    assert row["device_id"] is None
    assert row["location_id"] is None
    assert row["zone_id"] is None
    assert "acknowledged_at" not in row

    assert connection.scalar(
        select(AlertRow.id).where(AlertRow.id == UUID(row["id"]))
    ) is not None

    # A separate HTTP request still returns the persisted record.
    assert alerts(client) == rows


def test_only_error_state_creates_critical_alert(api):
    client, _, bus = api

    for state in ["idle", "running", "off", "maintenance", "error"]:
        bus.publish(ActuatorStateChanged(
            device_id=None,
            location_id=None,
            zone_id=None,
            state=state,
        ))

    rows = alerts(client)
    assert len(rows) == 1
    assert rows[0]["event_type"] == "state.changed"
    assert rows[0]["severity"] == "critical"
    assert rows[0]["message"] == "Actuator entered error"


def test_low_moisture_alert_and_location_zone_filters(api):
    client, _, bus = api

    response = client.post(
        "/api/locations/config",
        json={
            "location_name": f"Observer test {uuid4()}",
            "zones": [
                {
                    "name": "Bench 1",
                    "moisture_threshold_low": 0.20,
                    "moisture_threshold_high": 0.80,
                    "schedule": {},
                },
                {
                    "name": "Bench 2",
                    "moisture_threshold_low": 0.20,
                    "moisture_threshold_high": 0.80,
                    "schedule": {},
                },
            ],
        },
    )
    assert response.status_code == 201, response.text
    config = response.json()
    location_id = config["location"]["id"]
    zones = {zone["name"]: zone["id"] for zone in config["zones"]}

    response = client.post(
        "/api/devices/provision",
        params={"family": "simulation"},
    )
    assert response.status_code == 201, response.text
    sensor = next(
        row for row in response.json()
        if row["device_type"] == "moisture_sensor"
    )
    response = client.patch(
        f"/api/devices/{sensor['id']}/zone",
        json={"zone_id": zones["Bench 1"]},
    )
    assert response.status_code == 200, response.text

    for value in [0.20, 0.30, 0.10]:
        bus.publish(ReadingCreated(
            device_id=UUID(sensor["id"]),
            location_id=UUID(location_id),
            zone_id=UUID(zones["Bench 1"]),
            value=value,
            unit="vwc",
            source="simulation",
            recorded_at=datetime.now(timezone.utc),
        ))

    rows = alerts(client, zone_id=zones["Bench 1"])
    assert len(rows) == 1
    row = rows[0]
    assert row["event_type"] == "threshold.crossed"
    assert row["severity"] == "warning"
    assert row["message"] == "Moisture below zone low"
    assert row["device_id"] == sensor["id"]
    assert row["location_id"] == location_id
    assert row["zone_id"] == zones["Bench 1"]

    assert alerts(client, location_id=location_id) == rows
    assert alerts(client, zone_id=zones["Bench 2"]) == []
    assert alerts(client, location_id=str(uuid4())) == []


def test_status_filter_defaults_to_active(api):
    client, connection, bus = api
    publish_failure(bus, "First")
    first = alerts(client)[0]

    connection.execute(
        update(AlertRow)
        .where(AlertRow.id == UUID(first["id"]))
        .values(status="resolved")
    )
    publish_failure(bus, "Second")

    assert [row["message"] for row in alerts(client)] == ["Second"]
    assert [
        row["message"] for row in alerts(client, status="resolved")
    ] == ["First"]
    assert len(alerts(client, status="all")) == 2


def test_since_is_inclusive_and_history_is_newest_first(api):
    client, connection, bus = api
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ids = []

    for index in range(3):
        publish_failure(bus, f"Failure {index}")
        identifier = connection.scalar(
            select(AlertRow.id).where(
                AlertRow.message == f"Failure {index}"
            )
        )
        ids.append(str(identifier))
        connection.execute(
            update(AlertRow)
            .where(AlertRow.id == identifier)
            .values(created_at=start + timedelta(seconds=index))
        )

    assert [row["id"] for row in alerts(client)] == ids[::-1]
    assert [
        row["id"] for row in alerts(client, limit=1)
    ] == [ids[2]]
    assert [
        row["id"] for row in alerts(
            client,
            since=(start + timedelta(seconds=1)).isoformat(),
        )
    ] == [ids[2], ids[1]]


@pytest.mark.parametrize("status", ["unknown", "ACTIVE"])
def test_invalid_status_returns_400(api, status):
    client, _, _ = api
    response = client.get("/api/alerts", params={"status": status})
    assert response.status_code == 400


@pytest.mark.parametrize("limit", [0, -1, 201, "invalid"])
def test_invalid_limit_returns_422(api, limit):
    client, _, _ = api
    response = client.get("/api/alerts", params={"limit": limit})
    assert response.status_code == 422


def provision_test_devices(client):
    response = client.post(
        "/api/devices/provision",
        params={"family": "simulation"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_failed_command_api_creates_unassigned_alert(api):
    from app.infrastructure.models import ActuatorStateRow, DeviceRow

    client, connection, _ = api
    devices = provision_test_devices(client)
    pump = next(d for d in devices if d["device_type"] == "water_pump")
    pump_id = UUID(pump["id"])
    old_time = datetime.now(timezone.utc) - timedelta(minutes=31)

    connection.execute(
        update(DeviceRow)
        .where(DeviceRow.id == pump_id)
        .values(location_id=None, zone_id=None)
    )
    connection.execute(
        update(ActuatorStateRow)
        .where(ActuatorStateRow.device_id == pump_id)
        .values(state="running", updated_at=old_time)
    )

    response = client.post(
        "/api/commands",
        json={
            "device_id": str(pump_id),
            "command_type": "stop_pump",
            "payload": {},
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "failed"

    rows = alerts(client)
    assert len(rows) == 1
    assert rows[0]["event_type"] == "command.failed"
    assert rows[0]["severity"] == "warning"
    assert rows[0]["message"] == "Max run time exceeded"
    assert rows[0]["device_id"] == str(pump_id)
    assert rows[0]["location_id"] is None
    assert rows[0]["zone_id"] is None

    state = connection.execute(
        select(
            ActuatorStateRow.state,
            ActuatorStateRow.updated_at,
        ).where(ActuatorStateRow.device_id == pump_id)
    ).one()
    assert tuple(state) == ("running", old_time)


def test_error_transition_api_creates_critical_alert(api):
    client, _, _ = api
    devices = provision_test_devices(client)
    pump = next(d for d in devices if d["device_type"] == "water_pump")

    response = client.post(
        f"/api/devices/{pump['id']}/transition",
        json={"target": "error"},
    )
    assert response.status_code == 200, response.text

    rows = alerts(client)
    assert len(rows) == 1
    assert rows[0]["event_type"] == "state.changed"
    assert rows[0]["severity"] == "critical"
    assert rows[0]["message"] == "Actuator entered error"
    assert rows[0]["device_id"] == pump["id"]

    response = client.post(
        f"/api/devices/{pump['id']}/transition",
        json={"target": "idle"},
    )
    assert response.status_code == 200, response.text
    assert alerts(client) == rows


@pytest.mark.parametrize("tracking", [True, False])
def test_manual_read_api_respects_tracking(api, monkeypatch, tracking):
    from app.domain.sensors.reading import Reading
    from app.infrastructure import reading_dependencies
    from app.infrastructure.models import DeviceRow, ReadingRow

    client, connection, bus = api
    devices = provision_test_devices(client)
    sensor = next(
        d for d in devices if d["device_type"] == "moisture_sensor"
    )
    sensor_id = UUID(sensor["id"])

    connection.execute(
        update(DeviceRow)
        .where(DeviceRow.id == sensor_id)
        .values(tracking_enabled=tracking)
    )

    recorded_at = datetime.now(timezone.utc)

    class FixedAdapter:
        def read(self, device):
            return Reading(
                device_id=device.id,
                value=0.10,
                unit="vwc",
                source="simulation",
                recorded_at=recorded_at,
            )

    monkeypatch.setattr(
        reading_dependencies,
        "select_sensor_adapter",
        lambda device: FixedAdapter(),
    )

    received = []
    bus.subscribe(ReadingCreated, received.append)

    response = client.post(f"/api/sensors/{sensor_id}/read")
    assert response.status_code == 201, response.text

    stored = connection.execute(
        select(ReadingRow.value, ReadingRow.unit).where(
            ReadingRow.device_id == sensor_id,
            ReadingRow.recorded_at == recorded_at,
        )
    ).all()
    assert len(stored) == 1
    assert float(stored[0].value) == 0.10
    assert stored[0].unit == "vwc"

    assert len(received) == (1 if tracking else 0)
    if tracking:
        assert received[0].device_id == sensor_id
        assert received[0].value == 0.10
        assert received[0].recorded_at == recorded_at