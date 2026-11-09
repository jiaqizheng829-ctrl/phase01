import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, select, update
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.application.devices.execution_service import ActuatorExecutionService
from app.infrastructure.actuator_execution_repository import (
    ActuatorExecutionNotFoundError,
)
from app.infrastructure.adapters.actuators.max_run_time import (
    MaxRunTimeExceededError,
)
from app.infrastructure.models import (
    ActuatorExecutionLogRow,
    ActuatorStateRow,
)


NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


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

            # This deletion is rolled back after each test.
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
                    yield client, connection
            finally:
                app.dependency_overrides.clear()
                app.dependency_overrides.update(previous)
                transaction.rollback()
    finally:
        engine.dispose()


def provision(client):
    response = client.post(
        "/api/devices/provision",
        params={"family": "simulation"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def get_pump(devices):
    return UUID(next(
        device["id"]
        for device in devices
        if device["device_type"] == "water_pump"
    ))


def get_logs(client, limit=20):
    response = client.get(
        "/api/actuators/executions",
        params={"limit": limit},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_empty_log_returns_empty_list(api):
    client, _ = api
    assert get_logs(client) == []


def test_success_is_persisted_and_returned(api):
    client, connection = api
    device_id = get_pump(provision(client))

    with Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    ) as session:
        service = ActuatorExecutionService(session)
        service.apply(device_id, "unknown_command", {"value": 1})
        assert len(service.adapter.commands) == 1

    logs = get_logs(client)
    assert len(logs) == 1

    log = logs[0]
    assert UUID(log["id"])
    assert log["device_id"] == str(device_id)
    assert log["success"] is True
    assert log["policy_applied"] == ["logging"]
    assert log["message"] is None

    timestamp = datetime.fromisoformat(
        log["created_at"].replace("Z", "+00:00")
    )
    assert timestamp.utcoffset() is not None

    # Execution must not change the lifecycle state.
    state = connection.scalar(
        select(ActuatorStateRow.state).where(
            ActuatorStateRow.device_id == device_id
        )
    )
    assert state == "idle"


def test_blocked_attempt_is_persisted_after_error(api):
    client, connection = api
    device_id = get_pump(provision(client))
    started_at = NOW - timedelta(minutes=30)

    connection.execute(
        update(ActuatorStateRow)
        .where(ActuatorStateRow.device_id == device_id)
        .values(state="running", updated_at=started_at)
    )

    with Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    ) as session:
        service = ActuatorExecutionService(
            session,
            clock=lambda: NOW,
        )

        with pytest.raises(
            MaxRunTimeExceededError,
            match="Max run time exceeded",
        ):
            service.apply(device_id, "start", {})

        assert service.adapter.commands == []

    # A separate API request must still find the failed log.
    logs = get_logs(client)
    assert len(logs) == 1
    assert logs[0]["device_id"] == str(device_id)
    assert logs[0]["success"] is False
    assert logs[0]["policy_applied"] == ["maxRunTime", "logging"]
    assert logs[0]["message"] == "Max run time exceeded"

    state = connection.execute(
        select(
            ActuatorStateRow.state,
            ActuatorStateRow.updated_at,
        ).where(ActuatorStateRow.device_id == device_id)
    ).one()
    assert state.state == "running"
    assert state.updated_at == started_at


def test_logs_are_newest_first_and_limited(api):
    client, connection = api
    device_id = get_pump(provision(client))
    ids = [uuid4() for _ in range(25)]

    with Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    ) as session:
        session.add_all([
            ActuatorExecutionLogRow(
                id=log_id,
                device_id=device_id,
                success=True,
                policy_applied=["logging"],
                message=None,
                created_at=NOW + timedelta(seconds=index),
            )
            for index, log_id in enumerate(ids)
        ])
        session.commit()

    response = client.get("/api/actuators/executions")
    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == [
        str(log_id) for log_id in reversed(ids[-20:])
    ]

    assert [row["id"] for row in get_logs(client, limit=2)] == [
        str(ids[-1]),
        str(ids[-2]),
    ]


@pytest.mark.parametrize("limit", [0, -1, 101, "invalid"])
def test_invalid_limit_is_rejected(api, limit):
    client, _ = api
    response = client.get(
        "/api/actuators/executions",
        params={"limit": limit},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("kind", ["missing", "sensor"])
def test_invalid_device_is_rejected_before_execution(api, kind):
    client, connection = api
    devices = provision(client)

    if kind == "missing":
        device_id = uuid4()
    else:
        device_id = UUID(next(
            device["id"]
            for device in devices
            if device["role"] == "sensor"
        ))

    with Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    ) as session:
        service = ActuatorExecutionService(session)

        with pytest.raises(ActuatorExecutionNotFoundError):
            service.apply(device_id, "start", {})

        assert service.adapter.commands == []

    assert get_logs(client) == []