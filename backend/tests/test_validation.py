"""
Unit Tests: Telemetry Ingestion and Schema Validation
"""
import pytest
from pydantic import ValidationError
from backend.app.models.schemas import TelemetryIn, SimulationCommand


def test_valid_telemetry():
    valid_payload = {
        "machine_id": "MOTOR-001",
        "timestamp": "2026-09-30T11:00:00Z",
        "temperature": 52.4,
        "vibration": 1.6,
        "current": 8.9,
        "rpm": 1485.0,
        "voltage": 230.0,
        "pressure": 4.2,
        "state": "running"
    }
    t = TelemetryIn(**valid_payload)
    assert t.machine_id == "MOTOR-001"
    assert t.temperature == 52.4
    assert t.vibration == 1.6


def test_missing_fields_rejected():
    with pytest.raises(ValidationError):
        TelemetryIn(
            machine_id="MOTOR-001",
            timestamp="2026-09-30T11:00:00Z",
            # missing temperature, vibration, etc.
        )


def test_out_of_range_rejected():
    with pytest.raises(ValidationError):
        TelemetryIn(
            machine_id="MOTOR-001",
            timestamp="2026-09-30T11:00:00Z",
            temperature=1500.0, # Exceeds physical max 1200
            vibration=1.0,
            current=8.0,
            rpm=1480.0,
            voltage=230.0,
            pressure=4.0
        )


def test_simulation_command_validation():
    cmd = SimulationCommand(command="inject_fault", fault_type="bearing_degradation")
    assert cmd.command == "inject_fault"
    assert cmd.fault_type == "bearing_degradation"
    assert cmd.machine_id == "MOTOR-001"
