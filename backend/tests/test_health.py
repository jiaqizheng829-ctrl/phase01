import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg2://greenhouse:greenhouse@localhost:5432/greenhouse",
)

from fastapi.testclient import TestClient

from app.main import app
from app.interfaces.api import health


client = TestClient(app)


def test_health_returns_degraded_when_database_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        health,
        "check_database_connection",
        lambda: False,
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "degraded",
        "db": "fail",
    }


def test_root_points_to_api_documentation() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["api_reference"] == "/scalar"
    assert response.json()["openapi"] == "/openapi.json"


def test_default_docs_are_disabled() -> None:
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
