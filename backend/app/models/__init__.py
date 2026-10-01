"""
P_311 Pydantic Validation & Data Transfer Models
Strict type-checking and schema definition for IoT telemetry, faults, and diagnosis.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class TelemetryIn(BaseModel):
    machine_id: str = Field(..., json_schema_extra={"example": "MOTOR-001"})
    timestamp: str = Field(..., json_schema_extra={"example": "2026-09-30T11:00:00Z"})
    temperature: float = Field(..., ge=-50.0, le=1200.0, description="Temperature in °C")
    vibration: float = Field(..., ge=0.0, le=100.0, description="Vibration velocity RMS in mm/s")
    current: float = Field(..., ge=0.0, le=100.0, description="Stator current in Amperes")
    rpm: float = Field(..., ge=0.0, le=5000.0, description="Rotational speed in RPM")
    voltage: float = Field(..., ge=0.0, le=1000.0, description="Line voltage in Volts")
    pressure: float = Field(..., ge=0.0, le=50.0, description="Lube/Cooling pressure in bar")
    state: str = Field(default="running")


class TelemetryOut(TelemetryIn):
    id: Optional[int] = None


class MachineInfo(BaseModel):
    id: str
    name: str
    type: str
    rated_voltage: float
    rated_current: float
    rated_rpm: float
    status: str
    created_at: Optional[str] = None


class FaultEventModel(BaseModel):
    id: str
    machine_id: str
    timestamp: str
    fault_type: str
    severity: str
    confidence: float
    sensor_evidence: Dict[str, float]
    triggered_rules: List[str]
    resolved_at: Optional[str] = None


class DiagnosisModel(BaseModel):
    id: str
    fault_event_id: str
    machine_id: str
    timestamp: str
    fault_title: str
    severity: str
    sensor_evidence: Dict[str, Any]
    likely_causes: List[str]
    recommended_checks: List[str]
    corrective_actions: List[str]
    confidence: float
    uncertainty: str
    knowledge_sources: List[str]
    raw_llm_response: Optional[str] = None
    execution_time_ms: int
    is_fallback: bool = False


class SimulationCommand(BaseModel):
    command: str = Field(..., json_schema_extra={"example": "inject_fault"})  # inject_fault, reset, stop, start
    fault_type: Optional[str] = Field(None, json_schema_extra={"example": "bearing_degradation"})
    machine_id: Optional[str] = Field("MOTOR-001")


class HealthResponse(BaseModel):
    status: str
    mqtt_broker: bool
    database: bool
    database_type: str = "postgresql"
    grafana_url: Optional[str] = "http://localhost:3000"
    ollama_llm: bool
    model_name: str
    vector_store_chunks: int
    active_machine: str
    timestamp: str
