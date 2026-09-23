import os
from collections import Counter

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session


@pytest.fixture
def client():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is required for API tests")

    if make_url(url).database != "greenhouse_phase3_test":
        pytest.fail("API tests must use greenhouse_phase3_test")

    from app.infrastructure.db import get_session
    from app.main import app

    engine = create_engine(url)

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
            with TestClient(app) as test_client:
                yield test_client
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)
            transaction.rollback()

    engine.dispose()


def test_provision_and_filter_families(client):
    created_ids = set()

    for family in ("simulation", "edge"):
        response = client.post(
            "/api/devices/provision",
            params={"family": family},
        )

        assert response.status_code == 201
        devices = response.json()

        assert len(devices) == 4
        assert {d["device_family"] for d in devices} == {family}
        assert Counter(d["role"] for d in devices) == {
            "sensor": 2,
            "actuator": 2,
        }

        ids = {d["id"] for d in devices}
        assert len(ids) == 4
        assert created_ids.isdisjoint(ids)
        created_ids.update(ids)

        # A new request must be able to read the saved devices.
        listed = client.get(
            "/api/devices",
            params={"family": family},
        )
        assert listed.status_code == 200
        assert ids <= {d["id"] for d in listed.json()}
        assert all(
            d["device_family"] == family
            for d in listed.json()
        )

    # Both families now exist, so filters must exclude other devices.
    for family in ("simulation", "edge"):
        response = client.get(
            "/api/devices",
            params={"family": family, "role": "actuator"},
        )
        assert response.status_code == 200
        devices = response.json()

        assert all(
            d["device_family"] == family
            and d["role"] == "actuator"
            for d in devices
        )
        assert len([
            d for d in devices if d["id"] in created_ids
        ]) == 2


def test_unknown_family_returns_400_without_creating_devices(client):
    before = client.get("/api/devices")
    assert before.status_code == 200

    response = client.post(
        "/api/devices/provision",
        params={"family": "unknown"},
    )
    assert response.status_code == 400

    after = client.get("/api/devices")
    assert after.status_code == 200
    assert {d["id"] for d in before.json()} == {
        d["id"] for d in after.json()
    }


def test_phase2_sensor_api_still_works(client):
    response = client.post(
        "/api/sensors",
        json={"type": "moisture"},
    )
    assert response.status_code == 201
    sensor_id = response.json()["id"]

    sensors = client.get("/api/sensors")
    assert sensors.status_code == 200
    assert sensor_id in {d["id"] for d in sensors.json()}

    devices = client.get(
        "/api/devices",
        params={"family": "simulation", "role": "sensor"},
    )
    assert devices.status_code == 200
    assert sensor_id in {d["id"] for d in devices.json()}