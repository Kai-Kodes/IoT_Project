# P_311: Data Contracts, Schemas & API Specifications

## 1. MQTT Data Contracts

### A. Ingestion Telemetry Topic
**Topic Pattern:** `p311/machine/<machine_id>/telemetry`  
**Direction:** Edge Sensor / Simulator / Replay Adapter -> Mosquitto Broker -> FastAPI Backend  
**QoS:** 1 (At least once delivery)  
**Encoding:** UTF-8 JSON

#### Payload Schema:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TelemetryIn",
  "type": "object",
  "required": [
    "machine_id",
    "timestamp",
    "temperature",
    "vibration",
    "current",
    "rpm",
    "voltage",
    "pressure"
  ],
  "properties": {
    "machine_id": {
      "type": "string",
      "description": "Unique identifier of the monitored asset",
      "example": "MOTOR-001"
    },
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC timestamp",
      "example": "2026-09-30T10:15:30.123456Z"
    },
    "temperature": {
      "type": "number",
      "minimum": -50.0,
      "maximum": 1200.0,
      "description": "Stator / Bearing housing temperature in °C",
      "example": 52.4
    },
    "vibration": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 100.0,
      "description": "Overall vibration velocity RMS in mm/s",
      "example": 1.45
    },
    "current": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 100.0,
      "description": "Motor phase line current in Amperes",
      "example": 8.92
    },
    "rpm": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 5000.0,
      "description": "Rotor rotational shaft speed in RPM",
      "example": 1485.0
    },
    "voltage": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 1000.0,
      "description": "Supply phase-to-neutral or line voltage in Volts",
      "example": 230.2
    },
    "pressure": {
      "type": "number",
      "minimum": 0.0,
      "maximum": 50.0,
      "description": "Auxiliary lube/cooling oil pressure in bar",
      "example": 4.18
    },
    "state": {
      "type": "string",
      "enum": ["running", "starting", "stopping", "idle", "tripped"],
      "default": "running"
    }
  }
}
```

---

### B. Remote Simulator Control Topic
**Topic Pattern:** `p311/machine/<machine_id>/command`  
**Direction:** FastAPI Backend -> Mosquitto Broker -> Motor Simulator  
**QoS:** 1  

#### Payload Examples:
```json
// Inject Fault
{
  "command": "inject_fault",
  "fault_type": "bearing_degradation"
}

// Reset to Nominal Operating Baseline
{
  "command": "reset"
}

// Emergency Stop
{
  "command": "stop"
}
```

---

## 2. PostgreSQL Relational Schema (DDL)

```sql
-- 1. Asset Registry
CREATE TABLE IF NOT EXISTS machines (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL,
    rated_voltage DOUBLE PRECISION NOT NULL,
    rated_current DOUBLE PRECISION NOT NULL,
    rated_rpm DOUBLE PRECISION NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'healthy',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. Telemetry Time-Series
CREATE TABLE IF NOT EXISTS telemetry (
    id BIGSERIAL PRIMARY KEY,
    machine_id VARCHAR(64) NOT NULL REFERENCES machines(id),
    timestamp TIMESTAMPTZ NOT NULL,
    temperature DOUBLE PRECISION NOT NULL,
    vibration DOUBLE PRECISION NOT NULL,
    current DOUBLE PRECISION NOT NULL,
    rpm DOUBLE PRECISION NOT NULL,
    voltage DOUBLE PRECISION NOT NULL,
    pressure DOUBLE PRECISION NOT NULL,
    operating_state VARCHAR(32) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_telemetry_machine_time
ON telemetry (machine_id, timestamp DESC);

-- 3. Fault Events Audit Log
CREATE TABLE IF NOT EXISTS fault_events (
    id VARCHAR(64) PRIMARY KEY,
    machine_id VARCHAR(64) NOT NULL REFERENCES machines(id),
    timestamp TIMESTAMPTZ NOT NULL,
    fault_type VARCHAR(64) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    sensor_evidence JSONB NOT NULL,
    triggered_rules JSONB NOT NULL,
    resolved_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_fault_events_machine_time
ON fault_events (machine_id, timestamp DESC);

-- 4. Root Cause Diagnoses
CREATE TABLE IF NOT EXISTS diagnoses (
    id VARCHAR(64) PRIMARY KEY,
    fault_event_id VARCHAR(64) NOT NULL REFERENCES fault_events(id),
    machine_id VARCHAR(64) NOT NULL REFERENCES machines(id),
    timestamp TIMESTAMPTZ NOT NULL,
    fault_title VARCHAR(255) NOT NULL,
    severity VARCHAR(32) NOT NULL,
    sensor_evidence JSONB NOT NULL,
    likely_causes JSONB NOT NULL,
    recommended_checks JSONB NOT NULL,
    corrective_actions JSONB NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    uncertainty TEXT NOT NULL,
    knowledge_sources JSONB NOT NULL,
    raw_llm_response TEXT,
    execution_time_ms INTEGER NOT NULL,
    is_fallback BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_diagnoses_machine_time
ON diagnoses (machine_id, timestamp DESC);

-- 5. Knowledge Base Corpus
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id VARCHAR(64) PRIMARY KEY,
    doc_title VARCHAR(255) NOT NULL,
    section VARCHAR(255) NOT NULL,
    raw_text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. REST API Specifications

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Comprehensive system health check (MQTT, Postgres, Ollama, Vector Store). |
| `GET` | `/api/machines` | Returns registered machines and current health status. |
| `GET` | `/api/telemetry/latest?machine_id=MOTOR-001` | Returns the single latest sensor reading. |
| `GET` | `/api/telemetry/history?machine_id=MOTOR-001&limit=40` | Returns recent rolling telemetry points. |
| `GET` | `/api/telemetry/stream` | Server-Sent Events (SSE) 1 Hz live event stream. |
| `GET` | `/api/faults?machine_id=MOTOR-001&limit=20` | Returns historical fault events list. |
| `GET` | `/api/diagnosis/latest?machine_id=MOTOR-001` | Returns latest AI-synthesized diagnosis with RAG citations. |
| `POST`| `/api/simulation/fault` | Injects a physical fault mode into the motor simulator. |
| `POST`| `/api/simulation/reset` | Resets simulator back to healthy nominal baseline. |
| `POST`| `/api/assistant/chat` | Interactive Viva AI Tutor grounded in live telemetry and technical manuals. |
| `GET` | `/api/reports/work-order?machine_id=MOTOR-001` | Generates printable industrial Maintenance Work Order (HTML). |
