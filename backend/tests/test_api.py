"""
Integration Tests: FastAPI REST Endpoints
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "mqtt_broker" in data
    assert "database" in data


def test_machines_endpoint(client):
    res = client.get("/machines")
    assert res.status_code == 200
    machines = res.json()
    assert len(machines) >= 1
    assert machines[0]["id"] == "MOTOR-001"


def test_telemetry_history_endpoint(client):
    res = client.get("/telemetry/history?machine_id=MOTOR-001&limit=10")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_knowledge_search_endpoint(client):
    res = client.get("/knowledge/search?q=bearing%20wear&top_k=2")
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert len(data["results"]) > 0


def test_simulation_fault_injection(client):
    res = client.post("/simulation/fault", json={
        "command": "inject_fault",
        "fault_type": "motor_overheating",
        "machine_id": "MOTOR-001"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "success"


def test_simulation_reset(client):
    res = client.post("/simulation/reset", params={"machine_id": "MOTOR-001"})
    assert res.status_code == 200
    assert res.json()["status"] == "success"
