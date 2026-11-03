import os
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.infrastructure.models import ActuatorStateRow


IDLE_COMMANDS = {
    "start",
    "turn_off",
    "enter_maintenance",
    "report_error",
}


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

            previous_overrides = app.dependency_overrides.copy()
            app.dependency_overrides[get_session] = test_session

            try:
                with TestClient(app) as client:
                    yield client, connection
            finally:
                app.dependency_overrides.clear()
                app.dependency_overrides.update(previous_overrides)
                transaction.rollback()
    finally:
        engine.dispose()


def provision(client, family="simulation"):
    response = client.post(
        "/api/devices/provision",
        params={"family": family},
    )
    assert response.status_code == 201, response.text
    return response.json()


def pump_id(devices):
    return next(
        device["id"]
        for device in devices
        if device["device_type"] == "water_pump"
    )


def stored_state(connection, device_id):
    return connection.scalar(
        select(ActuatorStateRow.state).where(
            ActuatorStateRow.device_id == UUID(device_id)
        )
    )


@pytest.mark.parametrize("family", ["simulation", "edge"])
def test_new_actuators_have_persisted_idle_states(api, family):
    client, connection = api
    devices = provision(client, family)

    for device in devices:
        device_id = device["id"]

        if device["role"] == "actuator":
            assert device["state"] == "idle"
            assert set(device["allowed_commands"]) == IDLE_COMMANDS
            assert stored_state(connection, device_id) == "idle"

            response = client.get(
                f"/api/devices/{device_id}/state"
            )
            assert response.status_code == 200
            assert response.json()["state"] == "idle"
            assert set(
                response.json()["allowed_commands"]
            ) == IDLE_COMMANDS
        else:
            assert device["state"] is None
            assert device["allowed_commands"] == []
            assert stored_state(connection, device_id) is None


def test_transition_is_saved_and_visible_in_new_requests(api):
    client, connection = api
    devices = provision(client)
    device_id = pump_id(devices)

    response = client.post(
        f"/api/devices/{device_id}/transition",
        json={"target": "running"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "running"
    assert set(response.json()["allowed_commands"]) == {
        "stop",
        "report_error",
    }
    assert stored_state(connection, device_id) == "running"

    # This request uses a new database session.
    current = client.get(f"/api/devices/{device_id}/state")
    assert current.status_code == 200
    assert current.json()["state"] == "running"

    listed = client.get("/api/devices")
    assert listed.status_code == 200
    saved = next(
        device
        for device in listed.json()
        if device["id"] == device_id
    )
    assert saved["state"] == "running"
    assert set(saved["allowed_commands"]) == {
        "stop",
        "report_error",
    }

    # Other actuators must not change.
    for device in devices:
        if device["role"] == "actuator" and device["id"] != device_id:
            assert stored_state(connection, device["id"]) == "idle"


@pytest.mark.parametrize(
    "target",
    ["maintenance", "off", "running", "unknown"],
)
def test_illegal_transition_does_not_change_database(api, target):
    client, connection = api
    device_id = pump_id(provision(client))

    started = client.post(
        f"/api/devices/{device_id}/transition",
        json={"target": "running"},
    )
    assert started.status_code == 200

    before = connection.execute(
        select(
            ActuatorStateRow.state,
            ActuatorStateRow.updated_at,
        ).where(
            ActuatorStateRow.device_id == UUID(device_id)
        )
    ).one()

    rejected = client.post(
        f"/api/devices/{device_id}/transition",
        json={"target": target},
    )
    assert rejected.status_code == 409, rejected.text

    after = connection.execute(
        select(
            ActuatorStateRow.state,
            ActuatorStateRow.updated_at,
        ).where(
            ActuatorStateRow.device_id == UUID(device_id)
        )
    ).one()

    assert tuple(after) == tuple(before)

    current = client.get(f"/api/devices/{device_id}/state")
    assert current.status_code == 200
    assert current.json()["state"] == "running"
    assert set(current.json()["allowed_commands"]) == {
        "stop",
        "report_error",
    }


def test_lifecycle_sequence_is_persisted(api):
    client, connection = api
    device_id = pump_id(provision(client))

    for target in [
        "off",
        "idle",
        "maintenance",
        "error",
        "idle",
        "running",
        "idle",
    ]:
        response = client.post(
            f"/api/devices/{device_id}/transition",
            json={"target": target},
        )
        assert response.status_code == 200, response.text
        assert response.json()["state"] == target
        assert stored_state(connection, device_id) == target


def test_missing_device_returns_404(api):
    client, _ = api
    device_id = uuid4()

    response = client.get(f"/api/devices/{device_id}/state")
    assert response.status_code == 404

    response = client.post(
        f"/api/devices/{device_id}/transition",
        json={"target": "running"},
    )
    assert response.status_code == 404


def test_sensor_cannot_receive_actuator_state(api):
    client, connection = api
    devices = provision(client)
    device_id = next(
        device["id"]
        for device in devices
        if device["role"] == "sensor"
    )

    response = client.get(f"/api/devices/{device_id}/state")
    assert response.status_code == 404

    response = client.post(
        f"/api/devices/{device_id}/transition",
        json={"target": "running"},
    )
    assert response.status_code == 404

    assert stored_state(connection, device_id) is None