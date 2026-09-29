import os
from uuid import uuid4

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
                with TestClient(app) as test_client:
                    yield test_client
            finally:
                app.dependency_overrides.clear()
                app.dependency_overrides.update(previous)
                transaction.rollback()
    finally:
        engine.dispose()


def zone_input(name="Zone 1"):
    return {
        "name": name,
        "moisture_threshold_low": 0.2,
        "moisture_threshold_high": 0.8,
        "schedule": {},
    }


def create_location(client, name="Test location", count=2):
    response = client.post(
        "/api/locations/config",
        json={
            "location_name": name,
            "zones": [
                zone_input(f"Zone {index + 1}")
                for index in range(count)
            ],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_devices(client):
    response = client.post(
        "/api/devices/provision",
        params={"family": "simulation"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def assign(client, device_id, zone_id):
    response = client.patch(
        f"/api/devices/{device_id}/zone",
        json={"zone_id": zone_id},
    )
    assert response.status_code == 200, response.text
    return response.json()


def read_device(client, device_id):
    response = client.get("/api/devices")
    assert response.status_code == 200
    return next(
        device for device in response.json()
        if device["id"] == device_id
    )


def test_create_read_and_list_locations(client):
    first = create_location(client, "First")
    second = create_location(client, "Second")

    first_id = first["location"]["id"]
    second_id = second["location"]["id"]

    response = client.get(f"/api/locations/{first_id}/config")
    assert response.status_code == 200
    saved = response.json()

    assert saved["location"] == first["location"]
    assert len(saved["zones"]) == 2
    assert {zone["id"] for zone in saved["zones"]} == {
        zone["id"] for zone in first["zones"]
    }
    assert all(
        zone["location_id"] == first_id
        for zone in saved["zones"]
    )

    listed = client.get("/api/locations")
    assert listed.status_code == 200
    ids = [location["id"] for location in listed.json()]
    assert first_id in ids
    assert second_id in ids


@pytest.mark.parametrize(
    "payload",
    [
        {"location_name": "", "zones": [zone_input()]},
        {"location_name": "Invalid", "zones": []},
        {
            "location_name": "Invalid",
            "zones": [
                {
                    **zone_input(),
                    "moisture_threshold_low": 0.9,
                }
            ],
        },
        {
            "location_name": "Invalid",
            "zones": [zone_input(), zone_input()],
        },
    ],
)
def test_invalid_create_returns_400_without_saving(client, payload):
    before = client.get("/api/locations").json()

    response = client.post("/api/locations/config", json=payload)

    assert response.status_code == 400
    assert client.get("/api/locations").json() == before


def test_assignment_filter_and_unassign(client):
    config = create_location(client)
    location_id = config["location"]["id"]
    first_zone, second_zone = config["zones"]
    devices = create_devices(client)

    for device in devices[:2]:
        result = assign(client, device["id"], second_zone["id"])
        assert result["location_id"] == location_id
        assert result["zone_id"] == second_zone["id"]

    assign(client, devices[2]["id"], first_zone["id"])

    path = (
        f"/api/locations/{location_id}"
        f"/zones/{second_zone['id']}/devices"
    )
    response = client.get(path)
    assert response.status_code == 200
    assert {device["id"] for device in response.json()} == {
        devices[0]["id"], devices[1]["id"]
    }

    result = assign(client, devices[0]["id"], None)
    assert result["zone_id"] is None
    assert result["location_id"] is None

    saved = read_device(client, devices[0]["id"])
    assert saved["zone_id"] is None
    assert saved["location_id"] is None
    assert {device["id"] for device in client.get(path).json()} == {
        devices[1]["id"]
    }


def test_delete_location_preserves_devices_and_other_location(client):
    first = create_location(client, "Delete me")
    second = create_location(client, "Keep me")
    device = create_devices(client)[0]
    location_id = first["location"]["id"]

    assign(client, device["id"], first["zones"][0]["id"])

    response = client.delete(f"/api/locations/{location_id}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(
        f"/api/locations/{location_id}/config"
    ).status_code == 404

    listed_ids = {
        item["id"] for item in client.get("/api/locations").json()
    }
    assert location_id not in listed_ids
    assert second["location"]["id"] in listed_ids

    saved = read_device(client, device["id"])
    assert saved["zone_id"] is None
    assert saved["location_id"] is None

    # Cascade deletion must also remove the old zone.
    response = client.patch(
        f"/api/devices/{device['id']}/zone",
        json={"zone_id": first["zones"][0]["id"]},
    )
    assert response.status_code == 404


def test_zone_add_edit_delete_and_last_zone_protection(client):
    config = create_location(client, count=1)
    location_id = config["location"]["id"]
    base = f"/api/locations/{location_id}"

    response = client.post(
        f"{base}/zones",
        json=zone_input("New zone"),
    )
    assert response.status_code == 201
    zone = response.json()
    assert zone["location_id"] == location_id

    saved_config = client.get(f"{base}/config").json()
    assert zone["id"] in {
        item["id"] for item in saved_config["zones"]
    }

    zone_path = f"{base}/zones/{zone['id']}"
    response = client.patch(
        zone_path,
        json={
            "name": "Edited zone",
            "schedule": {"hour": 8},
        },
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Edited zone"
    assert response.json()["schedule"] == {"hour": 8}

    response = client.patch(
        zone_path,
        json={"moisture_threshold_low": 0.9},
    )
    assert response.status_code == 400

    saved_zone = next(
        item
        for item in client.get(f"{base}/config").json()["zones"]
        if item["id"] == zone["id"]
    )
    assert saved_zone["moisture_threshold_low"] == 0.2
    assert saved_zone["moisture_threshold_high"] == 0.8

    device = create_devices(client)[0]
    assign(client, device["id"], zone["id"])
    assert client.delete(zone_path).status_code == 204

    saved_device = read_device(client, device["id"])
    assert saved_device["zone_id"] is None
    assert saved_device["location_id"] is None

    remaining = client.get(f"{base}/config").json()["zones"]
    assert len(remaining) == 1
    assert remaining[0]["id"] == config["zones"][0]["id"]

    response = client.delete(
        f"{base}/zones/{remaining[0]['id']}"
    )
    assert response.status_code == 400
    assert len(client.get(f"{base}/config").json()["zones"]) == 1


def test_missing_resources_and_wrong_location_return_404(client):
    first = create_location(client, "First")
    second = create_location(client, "Second")
    device = create_devices(client)[0]
    missing_id = str(uuid4())

    assert client.get(
        f"/api/locations/{missing_id}/config"
    ).status_code == 404
    assert client.delete(
        f"/api/locations/{missing_id}"
    ).status_code == 404

    assert client.patch(
        f"/api/devices/{missing_id}/zone",
        json={"zone_id": None},
    ).status_code == 404

    assert client.patch(
        f"/api/devices/{device['id']}/zone",
        json={"zone_id": missing_id},
    ).status_code == 404

    wrong_path = (
        f"/api/locations/{first['location']['id']}"
        f"/zones/{second['zones'][0]['id']}"
    )
    assert client.get(f"{wrong_path}/devices").status_code == 404
    assert client.patch(
        wrong_path, json={"name": "Wrong"}
    ).status_code == 404
    assert client.delete(wrong_path).status_code == 404