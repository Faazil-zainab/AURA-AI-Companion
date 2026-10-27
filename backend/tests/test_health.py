from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_health_returns_ok_and_request_id(tmp_path):
    settings = Settings(database_path=tmp_path / "aura.db")

    with TestClient(create_app(settings)) as client:
        response = client.get("/health", headers={"X-Request-ID": "test-request"})

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "AURA Local Companion",
        "version": "0.2.0-phase2",
        "request_id": "test-request",
    }
    assert response.headers["X-Request-ID"] == "test-request"


def test_startup_initializes_local_database(tmp_path):
    database_path = tmp_path / "nested" / "aura.db"
    with TestClient(create_app(Settings(database_path=database_path))):
        pass

    assert database_path.exists()
