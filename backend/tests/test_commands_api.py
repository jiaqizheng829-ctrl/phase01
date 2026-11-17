import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select, update
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.infrastructure.models import (
    ActuatorExecutionLogRow,
    ActuatorStateRow,
    CommandLogRow,
)


@pytest.fixture
def api():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is required")

    if make_url(url).database != "greenhouse_phase3_test":
        pytest.fail("Tests must use greenhouse_phase3_test")

    from app.infrastructure.db import get_session
    from app.main import app

    engine = create_engine(url)

    try:
        with engine.connect() as connection:
            transaction = connection.begin()

            # These deletions are rolled back after each test.
            connection.execute(delete(CommandLogRow))
            connection.execute(delete(ActuatorExecutionLogRow))

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
                    response = client.post(
                        "/api/devices/provision",
                        params={"family": "simulation"},
                    )
                    assert response.status_code == 201, response.text
                    yield client, connection, response.json()
            finally:
                app.dependency_overrides.clear()
                app.dependency_overrides.update(previous)
                transaction.rollback()
    finally:
        engine.dispose()


def device_id(devices, device_type):
    return next(
        device["id"]
        for device in devices
        if device["device_type"] == device_type
    )


def post_command(client, identifier, command_type, payload=None):
    body = {
        "device_id": identifier,
        "command_type": command_type,
    }
    if payload is not None:
        body["payload"] = payload
    return client.post("/api/commands", json=body)


def state_snapshot(connection, identifier):
    row = connection.execute(
        select(
            ActuatorStateRow.state,
            ActuatorStateRow.updated_at,
        ).where(
            ActuatorStateRow.device_id == UUID(identifier)
        )
    ).one()
    return tuple(row)


def history(client):
    response = client.get("/api/commands")
    assert response.status_code == 200, response.text
    return response.json()


def execution_logs(connection, identifier):
    return connection.execute(
        select(
            ActuatorExecutionLogRow.success,
            ActuatorExecutionLogRow.policy_applied,
            ActuatorExecutionLogRow.message,
        ).where(
            ActuatorExecutionLogRow.device_id == UUID(identifier)
        )
    ).mappings().all()


def test_start_and_stop_update_state_and_save_logs(api):
    client, connection, devices = api
    pump = device_id(devices, "water_pump")

    for command_type, expected_state in [
        ("start_pump", "running"),
        ("stop_pump", "idle"),
    ]:
        response = post_command(client, pump, command_type)
        assert response.status_code == 200, response.text
        row = response.json()

        assert row["status"] == "success"
        assert row["command_type"] == command_type
        assert row["device_id"] == pump
        assert row["payload"] == {}
        assert row["error_message"] is None
        assert state_snapshot(connection, pump)[0] == expected_state
        assert row in history(client)

    logs = execution_logs(connection, pump)
    assert len(logs) == 2
    assert all(log["success"] for log in logs)


def test_rejected_command_does_not_apply_or_change_state(api):
    client, connection, devices = api
    pump = device_id(devices, "water_pump")

    before = state_snapshot(connection, pump)
    response = post_command(client, pump, "stop_pump")

    assert response.status_code == 409, response.text
    row = response.json()
    assert row["status"] == "rejected"
    assert row["error_message"]
    assert state_snapshot(connection, pump) == before
    assert execution_logs(connection, pump) == []
    assert history(client) == [row]


def test_runtime_failure_keeps_state_and_both_failure_logs(api):
    client, connection, devices = api
    pump = device_id(devices, "water_pump")

    connection.execute(
        update(ActuatorStateRow)
        .where(ActuatorStateRow.device_id == UUID(pump))
        .values(
            state="running",
            updated_at=datetime.now(timezone.utc) - timedelta(minutes=31),
        )
    )
    before = state_snapshot(connection, pump)

    response = post_command(client, pump, "stop_pump")

    assert response.status_code == 200, response.text
    row = response.json()
    assert row["status"] == "failed"
    assert row["error_message"] == "Max run time exceeded"
    assert state_snapshot(connection, pump) == before
    assert history(client) == [row]

    logs = execution_logs(connection, pump)
    assert len(logs) == 1
    assert logs[0]["success"] is False
    assert logs[0]["policy_applied"] == ["maxRunTime", "logging"]
    assert logs[0]["message"] == "Max run time exceeded"


def test_running_light_can_change_level_without_state_write(api):
    client, connection, devices = api
    light = device_id(devices, "grow_light")

    first = post_command(client, light, "set_light_level", {"level": 1})
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "success"
    assert state_snapshot(connection, light)[0] == "running"

    # Use a distinct timestamp so an unnecessary state write is detectable.
    connection.execute(
        update(ActuatorStateRow)
        .where(ActuatorStateRow.device_id == UUID(light))
        .values(updated_at=datetime.now(timezone.utc) - timedelta(minutes=1))
    )
    before = state_snapshot(connection, light)

    second = post_command(
        client, light, "set_light_level", {"level": 0.5}
    )
    assert second.status_code == 200, second.text
    assert second.json()["status"] == "success"
    assert second.json()["payload"] == {"level": 0.5}
    assert state_snapshot(connection, light) == before
    assert len(history(client)) == 2
    assert len(execution_logs(connection, light)) == 2


def test_unknown_command_returns_400_without_logs(api):
    client, connection, devices = api
    pump = device_id(devices, "water_pump")
    before = state_snapshot(connection, pump)

    response = post_command(client, pump, "unknown_command")

    assert response.status_code == 400, response.text
    assert history(client) == []
    assert execution_logs(connection, pump) == []
    assert state_snapshot(connection, pump) == before


@pytest.mark.parametrize("kind", ["missing", "sensor"])
def test_non_actuator_returns_404_without_logs(api, kind):
    client, connection, devices = api
    identifier = (
        str(uuid4())
        if kind == "missing"
        else next(d["id"] for d in devices if d["role"] == "sensor")
    )

    response = post_command(client, identifier, "start_pump")

    assert response.status_code == 404, response.text
    assert history(client) == []
    assert execution_logs(connection, identifier) == []


def test_history_is_newest_first_and_respects_limit(api):
    client, connection, devices = api
    pump = device_id(devices, "water_pump")
    ids = []

    for index, name in enumerate(["start_pump", "stop_pump", "start_pump"]):
        response = post_command(client, pump, name)
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "success"
        identifier = response.json()["id"]
        ids.append(identifier)

        # Explicit timestamps avoid ties inside the test transaction.
        connection.execute(
            update(CommandLogRow)
            .where(CommandLogRow.id == UUID(identifier))
            .values(
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
                + timedelta(seconds=index)
            )
        )

    assert [row["id"] for row in history(client)] == ids[::-1]

    response = client.get("/api/commands", params={"limit": 2})
    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == ids[::-1][:2]


@pytest.mark.parametrize("limit", [0, -1, 201, "invalid"])
def test_invalid_history_limit_returns_422(api, limit):
    client, _, _ = api
    response = client.get("/api/commands", params={"limit": limit})
    assert response.status_code == 422