from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.system import health as health_module


def test_health_check_returns_alive_and_timestamp():
    app = FastAPI()
    app.include_router(health_module.router, prefix="/health")

    client = TestClient(app)
    resp = client.get("/health/")
    assert resp.status_code == 200

    data = resp.json()
    assert data.get("status") == "alive"
    assert "timestamp" in data
    # Ensure timestamp is isoformat-parsable
    ts = data.get("timestamp")
    parsed = datetime.fromisoformat(ts)
    assert parsed.tzinfo is not None
    assert "service" in data
