"""
Unit Tests: SQLite Database Layer Operations
"""
import os
import tempfile
import pytest
from backend.app.db.database import DatabaseManager


@pytest.fixture
async def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = DatabaseManager(db_path=path)
    await db.init_db()
    yield db
    if os.path.exists(path):
        os.remove(path)


@pytest.mark.asyncio
async def test_db_init_and_seed(temp_db):
    machines = await temp_db.get_machines()
    assert len(machines) >= 1
    assert machines[0]["id"] == "MOTOR-001"


@pytest.mark.asyncio
async def test_telemetry_insert_and_purge(temp_db):
    for i in range(15):
        await temp_db.insert_telemetry({
            "machine_id": "MOTOR-001",
            "timestamp": f"2026-09-30T11:00:{i:02d}Z",
            "temperature": 50.0 + i,
            "vibration": 1.2,
            "current": 8.8,
            "rpm": 1485.0,
            "voltage": 230.0,
            "pressure": 4.2,
            "state": "running"
        })

    recent = await temp_db.get_recent_telemetry("MOTOR-001", limit=10)
    assert len(recent) == 10
    # Verify chronological order
    assert recent[-1]["temperature"] == 64.0

    # Test purge
    await temp_db.purge_old_telemetry(keep_latest=5)
    remaining = await temp_db.get_recent_telemetry("MOTOR-001", limit=20)
    assert len(remaining) == 5


@pytest.mark.asyncio
async def test_fault_and_diagnosis_storage(temp_db):
    fault_data = {
        "id": "FAULT-TEST-DB",
        "machine_id": "MOTOR-001",
        "timestamp": "2026-09-30T11:00:00Z",
        "fault_type": "bearing_degradation",
        "severity": "high",
        "confidence": 0.92,
        "sensor_evidence": {"temperature": 88.0, "vibration": 8.0},
        "triggered_rules": ["HIGH_VIBRATION"]
    }
    await temp_db.insert_fault_event(fault_data)

    retrieved_fault = await temp_db.get_fault_event_by_id("FAULT-TEST-DB")
    assert retrieved_fault is not None
    assert retrieved_fault["fault_type"] == "bearing_degradation"
    assert retrieved_fault["sensor_evidence"]["vibration"] == 8.0

    diag_data = {
        "id": "DIAG-TEST-DB",
        "fault_event_id": "FAULT-TEST-DB",
        "machine_id": "MOTOR-001",
        "timestamp": "2026-09-30T11:00:01Z",
        "fault_title": "Bearing Fault Test",
        "severity": "high",
        "sensor_evidence": {"temperature": 88.0},
        "likely_causes": ["Bearing wear"],
        "recommended_checks": ["Check vibration"],
        "corrective_actions": ["Replace bearing"],
        "confidence": 0.9,
        "uncertainty": "Demo test caveat",
        "knowledge_sources": ["Bearing Guide"],
        "raw_llm_response": "{}",
        "execution_time_ms": 120,
        "is_fallback": False
    }
    await temp_db.insert_diagnosis(diag_data)

    latest_diag = await temp_db.get_latest_diagnosis("MOTOR-001")
    assert latest_diag is not None
    assert latest_diag["id"] == "DIAG-TEST-DB"
    assert latest_diag["likely_causes"] == ["Bearing wear"]
