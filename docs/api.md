# REST & Real-Time API Specification

FastAPI automatically generates an interactive Swagger UI at `http://localhost:8000/docs` and ReDoc at `http://localhost:8000/redoc`.

## 1. System Health
### `GET /health` or `GET /api/health`
Returns runtime status of all system components.
```json
{
  "status": "healthy",
  "mqtt_broker": true,
  "database": true,
  "ollama_llm": true,
  "model_name": "qwen2.5:1.5b",
  "vector_store_chunks": 34,
  "active_machine": "MOTOR-001",
  "timestamp": "2026-09-30T11:00:00Z"
}
```

## 2. Telemetry & Streaming
### `GET /api/telemetry/latest?machine_id=MOTOR-001`
Fetches the most recent sensor telemetry snapshot.

### `GET /api/telemetry/history?machine_id=MOTOR-001&limit=60`
Fetches the last $N$ telemetry samples for charts.

### `GET /api/telemetry/stream` (SSE Live Feed)
Opens an HTTP persistent connection streaming 1 Hz Server-Sent Events.
**Example Event**:
```
data: {"type": "telemetry", "data": {"temperature": 52.1, "vibration": 1.4, ...}, "active_fault": null, "status": "healthy"}
```

## 3. Faults & Diagnoses
### `GET /api/faults?machine_id=MOTOR-001&limit=50`
Retrieves historical fault records.

### `GET /api/faults/{fault_id}`
Retrieves a specific fault event.

### `GET /api/diagnosis/latest?machine_id=MOTOR-001`
Retrieves the most recent explainable AI diagnostic report.

### `GET /api/diagnosis/{diagnosis_id}`
Retrieves a specific diagnosis by ID.

## 4. Simulator Remote Control
### `POST /api/simulation/fault`
Injects a physical fault into the motor simulator over MQTT.
```json
{
  "command": "inject_fault",
  "fault_type": "bearing_degradation",
  "machine_id": "MOTOR-001"
}
```

### `POST /api/simulation/reset`
Resets the machine back to normal operating parameters.

### `POST /api/simulation/start` & `POST /api/simulation/stop`
Starts or halts the simulator loop.

## 5. Knowledge Base & Vector Search
### `POST /api/knowledge/ingest`
Re-indexes all technical manuals in `knowledge_base/` into the local vector index.

### `GET /api/knowledge/search?q={query}&top_k=3`
Executes semantic vector search against the technical documentation library.
