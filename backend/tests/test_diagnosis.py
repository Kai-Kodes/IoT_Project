"""
Unit Tests: Explainable Diagnosis Engine & Offline Fallback
"""
import pytest
from unittest.mock import AsyncMock, patch
from backend.app.diagnosis.diagnosis_engine import diagnosis_engine


@pytest.fixture
def mock_fault():
    return {
        "id": "FAULT-DIAG-01",
        "machine_id": "MOTOR-001",
        "timestamp": "2026-09-30T11:00:00Z",
        "fault_type": "bearing_degradation",
        "severity": "critical",
        "confidence": 0.92,
        "sensor_evidence": {
            "temperature": 91.2,
            "vibration": 8.4,
            "current": 12.0,
            "rpm": 1465.0,
            "voltage": 230.0,
            "pressure": 4.1
        },
        "triggered_rules": ["HIGH_VIBRATION_ZONE_D_TRIP", "HIGH_TEMPERATURE_FRICTION"]
    }


@pytest.mark.asyncio
async def test_llm_success_path(mock_fault):
    mock_llm_result = {
        "fault_title": "Severe Rolling Element Bearing Degradation",
        "severity": "critical",
        "likely_causes": ["Fatigue spalling on outer race", "Grease breakdown"],
        "recommended_checks": ["Measure bearing housing vibration spectrum", "Inspect grease sample"],
        "corrective_actions": ["Immediate machine shutdown", "Replace bearing set"],
        "confidence": 0.94,
        "uncertainty": "Requires mechanical dial indicator verification."
    }

    with patch("backend.app.diagnosis.llm_client.llm_client.generate_json", new=AsyncMock(return_value=mock_llm_result)):
        diag = await diagnosis_engine.diagnose(mock_fault)
        assert diag["fault_title"] == "Severe Rolling Element Bearing Degradation"
        assert diag["is_fallback"] is False
        assert len(diag["likely_causes"]) == 2
        assert len(diag["recommended_checks"]) == 2
        assert len(diag["knowledge_sources"]) > 0


@pytest.mark.asyncio
async def test_llm_offline_fallback_path(mock_fault):
    # Simulate Ollama completely offline or timing out (returns None)
    with patch("backend.app.diagnosis.llm_client.llm_client.generate_json", new=AsyncMock(return_value=None)):
        diag = await diagnosis_engine.diagnose(mock_fault)
        assert diag["is_fallback"] is True
        assert "Bearing Mechanical Degradation" in diag["fault_title"]
        assert len(diag["likely_causes"]) >= 2
        assert len(diag["recommended_checks"]) >= 3
        assert "NOTICE: Local LLM is offline" in diag["uncertainty"]
