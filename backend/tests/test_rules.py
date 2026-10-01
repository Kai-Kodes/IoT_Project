"""
Unit Tests: Deterministic Fault Detection Rules Matrix
"""
import pytest
from backend.app.detection.fault_detector import FaultDetector


@pytest.fixture
def detector():
    return FaultDetector()


def test_normal_operation(detector):
    data = {
        "machine_id": "MOTOR-001",
        "timestamp": "2026-09-30T11:00:00Z",
        "temperature": 52.0,
        "vibration": 1.4,
        "current": 8.8,
        "rpm": 1485.0,
        "voltage": 230.0,
        "pressure": 4.2
    }
    fault, is_new = detector.evaluate_telemetry(data)
    assert fault is None
    assert is_new is False


def test_bearing_degradation_detection(detector):
    data = {
        "machine_id": "MOTOR-001",
        "timestamp": "2026-09-30T11:00:01Z",
        "temperature": 88.0,
        "vibration": 8.2,
        "current": 11.8,
        "rpm": 1465.0,
        "voltage": 230.0,
        "pressure": 4.1
    }
    fault, is_new = detector.evaluate_telemetry(data)
    assert fault is not None
    assert is_new is True
    assert fault["fault_type"] == "bearing_degradation"
    assert fault["severity"] == "critical"
    assert "HIGH_VIBRATION_ZONE_D_TRIP" in fault["triggered_rules"]
    assert "HIGH_TEMPERATURE_FRICTION" in fault["triggered_rules"]


def test_motor_overheating_detection(detector):
    data = {
        "machine_id": "MOTOR-001",
        "timestamp": "2026-09-30T11:00:02Z",
        "temperature": 104.0,
        "vibration": 2.0, # Normal vibration
        "current": 9.1,
        "rpm": 1480.0,
        "voltage": 230.0,
        "pressure": 4.1
    }
    fault, is_new = detector.evaluate_telemetry(data)
    assert fault is not None
    assert fault["fault_type"] == "motor_overheating"
    assert "CRITICAL_TEMPERATURE_HOTSPOT" in fault["triggered_rules"]


def test_motor_overload_detection(detector):
    data = {
        "machine_id": "MOTOR-001",
        "timestamp": "2026-09-30T11:00:03Z",
        "temperature": 85.0,
        "vibration": 3.2,
        "current": 15.5, # Overload current
        "rpm": 1395.0, # High slip speed drop
        "voltage": 230.0,
        "pressure": 4.1
    }
    fault, is_new = detector.evaluate_telemetry(data)
    assert fault is not None
    assert fault["fault_type"] == "motor_overload"
    assert "EXCESSIVE_STATOR_CURRENT_OVER_FLA" in fault["triggered_rules"]
    assert "ROTOR_SPEED_DROP_HIGH_SLIP" in fault["triggered_rules"]


def test_sensor_anomaly_detection(detector):
    data = {
        "machine_id": "MOTOR-001",
        "timestamp": "2026-09-30T11:00:04Z",
        "temperature": 999.0, # Thermocouple open-circuit spike
        "vibration": 1.4,
        "current": 8.8,
        "rpm": 1485.0,
        "voltage": 230.0,
        "pressure": 4.2
    }
    fault, is_new = detector.evaluate_telemetry(data)
    assert fault is not None
    assert fault["fault_type"] == "sensor_anomaly"
    assert "SENSOR_OUT_OF_PHYSICAL_RANGE" in fault["triggered_rules"]


def test_fault_resolution_transition(detector):
    # 1. Trigger fault
    bearing_data = {
        "machine_id": "MOTOR-001",
        "timestamp": "2026-09-30T11:00:01Z",
        "temperature": 88.0,
        "vibration": 8.2,
        "current": 11.8,
        "rpm": 1465.0,
        "voltage": 230.0,
        "pressure": 4.1
    }
    detector.evaluate_telemetry(bearing_data)
    assert detector.active_faults.get("MOTOR-001") is not None

    # 2. Return to normal
    normal_data = {
        "machine_id": "MOTOR-001",
        "timestamp": "2026-09-30T11:00:02Z",
        "temperature": 52.0,
        "vibration": 1.4,
        "current": 8.8,
        "rpm": 1485.0,
        "voltage": 230.0,
        "pressure": 4.2
    }
    f, is_resolution = detector.evaluate_telemetry(normal_data)
    assert f is None
    assert is_resolution is True
    assert detector.active_faults.get("MOTOR-001") is None
