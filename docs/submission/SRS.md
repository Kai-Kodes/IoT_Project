# Software Requirements Specification (SRS)
## Project P_311: Knowledge-Driven IoT Fault Diagnosis Assistant

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) document details the functional, non-functional, hardware, software, and interface requirements for the **P_311 Knowledge-Driven IoT Fault Diagnosis Assistant**. This document establishes the complete technical specification for academic evaluation, software architecture validation, and edge deployment verification.

### 1.2 Scope
Project P_311 is an edge-native, explainable AI IoT software system developed to monitor, detect, diagnose, and prescribe maintenance procedures for 3-phase industrial induction motors. The scope encompasses:
- Decoupled high-throughput telemetry ingestion via MQTT.
- In-memory deterministic fault detection adhering to **ISO 10816-3** and **IEC 60034-1** standards.
- Dual database persistence using PostgreSQL 16 with asynchronous connection pooling and a zero-dependency SQLite fallback.
- Local CPU-bound semantic vector indexing (RAG) over engineering equipment manuals.
- Structured root-cause diagnosis synthesis using a local quantized Large Language Model (`qwen2.5:1.5b-instruct` in Ollama).
- Real-time web visualization featuring Server-Sent Events (SSE), an SVG Digital Twin, audio alarm annunciator, printable maintenance work orders, and an operational Grafana SCADA dashboard.
- A high-fidelity physical motor telemetry simulator supporting 7 operating and fault modes.

### 1.3 Definitions, Acronyms, and Abbreviations
- **FLA**: Full Load Amperes (rated continuous stator current).
- **IEC**: International Electrotechnical Commission.
- **ISO**: International Organization for Standardization.
- **LLM**: Large Language Model.
- **LOTO**: Lockout / Tagout (industrial electrical safety procedure).
- **LWT**: Last Will and Testament (MQTT protocol feature for connection loss detection).
- **MQTT**: Message Queuing Telemetry Transport.
- **MTTR**: Mean Time to Repair.
- **QoS**: Quality of Service (MQTT message delivery guarantee level).
- **RAG**: Retrieval-Augmented Generation.
- **RMS**: Root Mean Square (vibration velocity measurement).
- **SCADA**: Supervisory Control and Data Acquisition.
- **SSE**: Server-Sent Events (HTTP streaming protocol for one-way server-to-browser push).
- **VRAM**: Video Random Access Memory (GPU memory).

---

## 2. Overall Description

### 2.1 System Architecture Overview
The system consists of six decoupled architectural subsystems:
1. **Telemetry Producer Subsystem**: The `motor_simulator.py` engine publishes 1 Hz JSON telemetry packets to the MQTT broker over `p311/machine/<machine_id>/telemetry`.
2. **Message Broker Subsystem**: Eclipse Mosquitto broker listening on TCP port `1883`.
3. **Core Application Server (FastAPI)**: Runs an asynchronous MQTT consumer thread, validates data with Pydantic schemas, routes telemetry to database pools, evaluates deterministic fault rules, coordinates RAG and LLM diagnostic pipelines, and pushes live updates via SSE.
4. **Data Persistence Subsystem**: Primary PostgreSQL 16 database running in Docker on host port `5433` (with native JSONB columns), automatically falling back to local file-based SQLite (`data/p311.db`) if Docker/PostgreSQL is unavailable.
5. **Knowledge & AI Subsystem**: Local CPU-based vector search using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions) and local LLM inference using Ollama running `qwen2.5:1.5b`.
6. **Dual Presentation Subsystem**:
   - **Operational SCADA**: Grafana OSS 11.2.0 on port `3000` with pre-configured dashboards.
   - **Diagnostic Engineering UI**: React 18 single-page application served via FastAPI on port `8000`.

### 2.2 User Characteristics
- **Plant Control Room Operator**: Requires continuous real-time visual tracking of vibration, current, and temperature, with immediate audible and visual alerts when ISO limits are breached.
- **Maintenance / Reliability Engineer**: Requires detailed root-cause diagnoses, sensor evidence comparisons, manufacturer documentation citations, and printable work orders.
- **Academic Evaluator / Viva Examiner**: Requires an interactive digital twin, remote fault injection capabilities, reproducible benchmark evaluation, and an interactive Viva AI tutor for oral defense.

---

## 3. Functional Requirements

### 3.1 Telemetry Ingestion & Protocol Communication
- **FR-01 (MQTT Broker Connection)**: The system shall connect to an MQTT v3.1.1/v5.0 broker at `localhost:1883` upon startup and automatically attempt reconnection if disconnected.
- **FR-02 (Topic Subscription)**: The backend shall subscribe to the wildcard topic pattern `p311/machine/+/telemetry` with Quality of Service Level 1 (QoS 1).
- **FR-03 (Payload Schema Validation)**: Every incoming JSON message must be validated against the `TelemetryIn` Pydantic model containing:
  - `machine_id` (string)
  - `timestamp` (ISO 8601 UTC timestamp)
  - `temperature` (float, °C)
  - `vibration` (float, mm/s RMS)
  - `current` (float, Amperes)
  - `rpm` (float, Revolutions Per Minute)
  - `voltage` (float, Volts)
  - `pressure` (float, bar)
  - `state` (string: running, warning, critical, stopped)
  Malformed or out-of-range payloads shall be logged and discarded without crashing the ingestion service.

### 3.2 Deterministic Fault Detection
- **FR-04 (Sub-Millisecond Rule Evaluation)**: The backend shall evaluate incoming telemetry against centralized engineering thresholds in `< 5 ms` per packet.
- **FR-05 (ISO 10816-3 Vibration Severity Rules)**:
  - `VIBRATION_ZONE_C_ALARM`: Vibration velocity $> 4.5\text{ mm/s}$ triggers a warning state.
  - `VIBRATION_ZONE_D_TRIP`: Vibration velocity $\ge 7.1\text{ mm/s}$ triggers a critical emergency alarm.
- **FR-06 (IEC Thermal Insulation Rules)**:
  - Stator temperature $> 75.0^\circ\text{C}$ triggers a thermal warning.
  - Stator temperature $> 85.0^\circ\text{C}$ triggers a high thermal alarm.
  - Stator temperature $\ge 95.0^\circ\text{C}$ triggers an emergency Class F thermal trip.
- **FR-07 (Multi-Sensor Compound Fault Classifications)**:
  - **Bearing Degradation**: Triggered when vibration $> 4.5\text{ mm/s}$ AND temperature $> 75.0^\circ\text{C}$.
  - **Motor Overload**: Triggered when stator current $> 11.5\text{ A}$ (exceeding 125% FLA) AND rotor speed $< 1450\text{ RPM}$.
  - **Motor Overheating**: Triggered when temperature $> 85.0^\circ\text{C}$ AND vibration $\le 4.5\text{ mm/s}$.
  - **Excessive Vibration / Unbalance**: Triggered when vibration $> 4.5\text{ mm/s}$ without thermal elevation.
  - **Low Lubrication Pressure**: Triggered when oil pressure $< 3.0\text{ bar}$ (critical trip if $< 2.0\text{ bar}$).
  - **Sensor Physical Anomaly**: Triggered when any sensor reading violates physical boundaries (e.g., temperature $< -20^\circ\text{C}$ or $> 160^\circ\text{C}$; voltage $< 100\text{ V}$ or $> 500\text{ V}$).
- **FR-08 (Stateful Debouncing & Resolution)**: The fault engine shall track active fault states per machine. When a fault resolves back to nominal limits, a resolution event shall be recorded.

### 3.3 Semantic Retrieval-Augmented Generation (RAG)
- **FR-09 (Knowledge Base Ingestion)**: The system shall parse markdown engineering manuals from `knowledge_base/`, segment documents into semantic chunks by headers, and compute 384-dimensional dense vectors using `sentence-transformers/all-MiniLM-L6-v2`.
- **FR-10 (Persistent Vector Store)**: Chunks and embeddings shall be cached locally in `data/vector_store/chunks.json` and `data/vector_store/embeddings.npy`.
- **FR-11 (Sub-Millisecond Cosine Vector Search)**: Upon a fault event, the system shall execute cosine similarity search against indexed chunks and return the top 3 most relevant documentation sections with similarity scores $\ge 0.30$ in $< 1\text{ ms}$.

### 3.4 Local AI Diagnosis Synthesis & Fallback
- **FR-12 (Local LLM Invocation)**: The backend shall construct a structured prompt incorporating measured telemetry, triggered ISO rules, and retrieved manual excerpts, and query Ollama (`qwen2.5:1.5b`) with an enforced JSON schema.
- **FR-13 (Structured Diagnostic Output)**: The generated JSON diagnosis must include:
  - `fault_title` (string)
  - `severity` (string: warning, high, critical)
  - `sensor_evidence` (key-value numerical snapshot)
  - `likely_causes` (list of strings)
  - `recommended_checks` (list of strings)
  - `corrective_actions` (list of strings)
  - `confidence` (float between 0.0 and 1.0)
  - `uncertainty` (string)
  - `knowledge_sources` (list of document titles and sections)
- **FR-14 (Deterministic Fallback Mode)**: If Ollama is unreachable or times out ($> 45\text{ seconds}$), the system shall automatically synthesize a deterministic, standards-based diagnostic report from pre-compiled rule templates and direct manual excerpts without crashing or dropping telemetry.

### 3.5 Data Persistence & Storage
- **FR-15 (Dual Database Support)**:
  - Primary: Asynchronous connection pool (`asyncpg`, 2–10 connections) to PostgreSQL 16 on port `5433` using native JSONB columns.
  - Fallback: Local SQLite database (`data/p311.db`) using `aiosqlite` with WAL mode.
- **FR-16 (Automated Telemetry Trimming)**: The database manager shall purge old telemetry records every 100 incoming samples, maintaining a configurable rolling window (default: 10,000 records) to prevent disk exhaustion.

### 3.6 Visualization, API, and Reporting
- **FR-17 (Server-Sent Events Streaming)**: The backend shall expose `/api/telemetry/stream` pushing real-time 1 Hz telemetry packets to connected browsers with automatic reconnect and keep-alive pings.
- **FR-18 (RESTful Management API)**: Provide documented OpenAPI endpoints:
  - `GET /api/health`: System health and component status.
  - `GET /api/machines`: Asset inventory.
  - `GET /api/telemetry/latest` & `/api/telemetry/history`: Time-series query endpoints.
  - `GET /api/faults` & `/api/diagnosis/latest`: Alarm and diagnosis logs.
  - `POST /api/simulation/fault`: Remote fault injection RPC over MQTT.
  - `POST /api/simulation/reset`: Remote simulator baseline reset.
  - `POST /api/assistant/chat`: RAG-grounded Viva Q&A assistant chat.
  - `GET /api/reports/work-order`: Printable HTML/PDF industrial maintenance work order.
- **FR-19 (React Diagnostic Dashboard)**: The web interface shall display:
  - Live metric cards and 50-sample rolling sparklines for all 7 physical channels.
  - Interactive SVG Digital Twin motor with rotor RPM rotation and thermal color gradients.
  - Audio alarm synthesizer using Web Audio API with user mute controls.
  - Real-time diagnostic cards displaying causes, checklists, and manual citations.
  - Fault injection control panel supporting 6 physical fault modes plus normal reset.
- **FR-20 (Grafana SCADA Dashboard)**: Provide operational time-series visualization on port `3000` connected directly to PostgreSQL with ISO threshold limit lines and anonymous Viewer access.

---

## 4. External Interface Requirements

### 4.1 Hardware Interfaces
- No direct physical embedded sensor hardware interface is required for the baseline software simulator implementation.
- Hardware requirements for physical IoT deployment are detailed in the Bill of Materials (BOM).

### 4.2 Software Interfaces
1. **MQTT Broker**: TCP socket on port `1883` using Paho-MQTT Client library.
2. **PostgreSQL Database**: TCP connection on host port `5433` (container port `5432`) via `asyncpg`.
3. **Local LLM Engine**: HTTP REST interface to Ollama daemon on `http://localhost:11434`.
4. **Grafana SCADA**: HTTP interface on `http://localhost:3000`.
5. **Web Browser Clients**: HTTP/1.1 and HTTP/2 on port `8000` supporting Server-Sent Events (`text/event-stream`).

---

## 5. Non-Functional Requirements

### 5.1 Performance Requirements
- **NFR-01 (Detection Latency)**: Deterministic fault detection shall execute in $\le 5\text{ ms}$ from telemetry arrival.
- **NFR-02 (RAG Search Latency)**: Top-3 vector retrieval across the technical knowledge base shall execute in $\le 1\text{ ms}$ on CPU.
- **NFR-03 (LLM Inference Time)**: Local LLM response generation shall complete within $1.5\text{ to }4.0\text{ seconds}$ on an NVIDIA RTX 2050 GPU (or gracefully fallback on timeout).
- **NFR-04 (UI Telemetry Refresh)**: The React dashboard shall update sensor cards and sparklines at $1\text{ Hz}$ with visual lag $< 100\text{ ms}$ from the SSE stream.

### 5.2 Reliability & Fault Tolerance
- **NFR-05 (Zero Ingestion Disruption)**: An LLM outage, GPU out-of-memory condition, or database slowdown must never halt MQTT ingestion or cause incoming telemetry packets to be dropped.
- **NFR-06 (Automatic Graceful Degradation)**: The system shall operate fully in Fallback Mode (deterministic diagnosis) when Ollama is offline or uninstalled.
- **NFR-07 (Connection Resiliency)**: The MQTT client, SSE broadcaster, and database connection pools must automatically detect disconnects and reconnect with exponential backoff.

### 5.3 Resource & Hardware Constraints
- **NFR-08 (VRAM Envelope)**: The local LLM and embedding pipeline shall consume $\le 1.5\text{ GB}$ of VRAM, operating within a 4 GB VRAM budget (leaving $> 2.5\text{ GB}$ for OS display rendering).
- **NFR-09 (System Memory Envelope)**: The combined stack (PostgreSQL, Grafana, Mosquitto, FastAPI, Ollama, React build) shall consume $\le 1.2\text{ GB}$ of system RAM.
- **NFR-10 (Zero Cloud Dependency)**: The entire software pipeline must operate 100% offline in an air-gapped environment without internet access.

### 5.4 Security & Data Privacy
- **NFR-11 (On-Premises Data Privacy)**: Operational telemetry, fault logs, and asset profiles shall never leave the local workstation.
- **NFR-12 (Credential Sanitization)**: No production passwords, secret keys, or cloud access tokens shall be hardcoded in version-controlled files.
- **NFR-13 (CORS Policy)**: Backend REST and SSE endpoints shall support controlled Cross-Origin Resource Sharing.

### 5.5 Maintainability & Standards Compliance
- **NFR-14 (Code Modularity)**: The codebase shall strictly follow layered modular architecture: Core, Database, MQTT, Detection, RAG, Diagnosis, Models, and API.
- **NFR-15 (Industrial Standards Compliance)**: Vibration and thermal thresholds shall comply with **ISO 10816-3** (Class II medium machines) and **IEC 60034-1** (Class F insulation).
