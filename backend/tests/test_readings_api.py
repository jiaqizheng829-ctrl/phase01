import os
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.infrastructure.models import ReadingRow


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


def create_sensor(client):
    response = client.post(
        "/api/sensors",
        json={"type": "moisture"},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_reads_append_rows_and_history_is_newest_first(api):
    client, connection = api
    sensor_id = create_sensor(client)

    first = client.post(f"/api/sensors/{sensor_id}/read")
    second = client.post(f"/api/sensors/{sensor_id}/read")

    assert first.status_code == 201
    assert second.status_code == 201

    reading = second.json()
    assert reading["device_id"] == sensor_id
    assert 0.2 <= reading["value"] <= 0.6
    assert reading["unit"] == "vwc"
    assert reading["source"] == "simulation"
    assert reading["recorded_at"]

    count = connection.scalar(
        select(func.count())
        .select_from(ReadingRow)
        .where(ReadingRow.device_id == UUID(sensor_id))
    )
    assert count == 2

    history = client.get(f"/api/sensors/{sensor_id}/readings")
    assert history.status_code == 200
    assert history.json() == [second.json(), first.json()]

    latest = client.get(
        f"/api/sensors/{sensor_id}/readings",
        params={"limit": 1},
    )
    assert latest.status_code == 200
    assert latest.json() == [second.json()]


def test_sampling_settings_persist_and_manual_read_works_when_off(api):
    client, _ = api
    sensor_id = create_sensor(client)

    response = client.patch(
        f"/api/devices/{sensor_id}/sampling",
        json={
            "sampling_interval_seconds": 15,
            "tracking_enabled": False,
        },
    )
    assert response.status_code == 200
    assert response.json() == {
        "device_id": sensor_id,
        "sampling_interval_seconds": 15,
        "tracking_enabled": False,
    }

    sensors = client.get("/api/sensors")
    assert sensors.status_code == 200
    saved = next(
        sensor for sensor in sensors.json()
        if sensor["id"] == sensor_id
    )
    assert saved["sampling_interval_seconds"] == 15
    assert saved["tracking_enabled"] is False

    reading = client.post(f"/api/sensors/{sensor_id}/read")
    assert reading.status_code == 201

    history = client.get(f"/api/sensors/{sensor_id}/readings")
    assert history.status_code == 200
    assert len(history.json()) == 1


def test_invalid_interval_does_not_change_saved_settings(api):
    client, _ = api
    sensor_id = create_sensor(client)

    response = client.patch(
        f"/api/devices/{sensor_id}/sampling",
        json={
            "sampling_interval_seconds": 2,
            "tracking_enabled": False,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"]

    sensors = client.get("/api/sensors")
    assert sensors.status_code == 200
    saved = next(
        sensor for sensor in sensors.json()
        if sensor["id"] == sensor_id
    )
    assert saved["sampling_interval_seconds"] == 300
    assert saved["tracking_enabled"] is True


def test_missing_device_returns_404(api):
    client, _ = api
    missing_id = uuid4()

    assert client.post(
        f"/api/sensors/{missing_id}/read"
    ).status_code == 404

    assert client.get(
        f"/api/sensors/{missing_id}/readings"
    ).status_code == 404

    assert client.patch(
        f"/api/devices/{missing_id}/sampling",
        json={
            "sampling_interval_seconds": 30,
            "tracking_enabled": True,
        },
    ).status_code == 404


def test_actuator_read_is_rejected_without_saving(api):
    client, connection = api

    response = client.post(
        "/api/devices/provision",
        params={"family": "simulation"},
    )
    assert response.status_code == 201
    actuator_id = next(
        device["id"] for device in response.json()
        if device["role"] == "actuator"
    )

    reading = client.post(f"/api/sensors/{actuator_id}/read")
    assert reading.status_code == 400

    count = connection.scalar(
        select(func.count())
        .select_from(ReadingRow)
        .where(ReadingRow.device_id == UUID(actuator_id))
    )
    assert count == 0


@pytest.mark.parametrize("limit", [0, -1, 101])
def test_invalid_history_limit_returns_400(api, limit):
    client, _ = api
    sensor_id = create_sensor(client)

    response = client.get(
        f"/api/sensors/{sensor_id}/readings",
        params={"limit": limit},
    )
    assert response.status_code == 400

def test_mqtt_translation_is_persisted_through_ingest(api):
    from app.application.readings.service import ReadingIngest
    from app.domain.devices.entity import Device
    from app.infrastructure.adapters.sensors.mqtt import (
        MqttSensorAdapter,
    )
    from app.infrastructure.adapters.sensors.selector import (
        select_sensor_adapter,
    )
    from app.infrastructure.device_repository import DeviceRepository
    from app.infrastructure.reading_repository import ReadingRepository

    client, connection = api

    with Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    ) as session:
        devices = DeviceRepository(session)
        readings = ReadingRepository(session)

        device = devices.save_device(
            Device(
                id=None,
                device_type="moisture_sensor",
                role="sensor",
                device_family="edge",
                display_name="MQTT test sensor",
                default_config={"protocol": "mqtt"},
            )
        )
        assert device.id is not None
        device_id = device.id

        reading = MqttSensorAdapter().translate(
            device,
            {"value": 0.41, "unit": "vwc"},
        )

        service = ReadingIngest(
            devices,
            readings,
            select_sensor_adapter,
        )
        saved = service.record(device_id, reading)

        assert saved.value == pytest.approx(0.41)
        assert saved.source == "mqtt"

    # A separate API request must see the persisted reading.
    history = client.get(f"/api/sensors/{device_id}/readings")
    assert history.status_code == 200
    assert len(history.json()) == 1

    stored = history.json()[0]
    assert stored["device_id"] == str(device_id)
    assert stored["value"] == pytest.approx(0.41)
    assert stored["unit"] == "vwc"
    assert stored["source"] == "mqtt"

    # MQTT devices must not generate a simulated manual reading.
    response = client.post(f"/api/sensors/{device_id}/read")
    assert response.status_code == 400

    count = connection.scalar(
        select(func.count())
        .select_from(ReadingRow)
        .where(ReadingRow.device_id == device_id)
    )
    assert count == 1