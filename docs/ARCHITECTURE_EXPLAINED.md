# P_311: Architecture Deep Dive & Engineering Design

## 1. Executive Summary & Philosophy

**Project P_311** is an AI-assisted IoT Fault Diagnosis system engineered for industrial rotating machinery (specifically 3-phase induction motors and driven equipment). The architecture combines deterministic physical telemetry threshold analysis, semantic Retrieval-Augmented Generation (RAG), and local Large Language Model (LLM) reasoning into a cohesive, production-grade monitoring pipeline.

The design strictly obeys the following priorities:
1. **Reliability & Determinism**: Critical safety trips and alarms do not depend on probabilistic LLM responses. Deterministic ISO-standard algorithms detect faults instantly (< 5 ms).
2. **Local Hardware Constraint**: The entire stack runs self-contained on a standard workstation (Intel Core i5-12450H, 16 GB RAM, NVIDIA GeForce RTX 2050 4 GB VRAM) with zero cloud dependencies.
3. **Dual Visualization Strategy**: Separation of operational time-series monitoring (**Grafana**) from interactive AI engineering diagnosis and academic viva workflows (**React Application**).

---

## 2. End-to-End System Architecture

```
                       ┌────────────────────────────┐
                       │  REAL DATA / CSV REPLAY    │
                       │  OR MOTOR SIMULATOR        │
                       └─────────────┬──────────────┘
                                     │ MQTT QoS 1
                                     ▼
                       ┌────────────────────────────┐
                       │   MOSQUITTO BROKER (1883)  │
                       └─────────────┬──────────────┘
                                     │ p311/machine/+/telemetry
                                     ▼
                       ┌────────────────────────────┐
                       │      FASTAPI BACKEND       │
                       │   (Async Consumer Daemon)  │
                       └──────┬──────────────┬──────┘
                              │              │
             Async Bulk Insert│              │ Telemetry Evaluation (< 5 ms)
                              ▼              ▼
                     ┌────────────┐   ┌───────────────────────────┐
                     │ POSTGRESQL │   │  DETERMINISTIC DETECTOR   │
                     │  (Port     │   │ (ISO 10816, FLA, Thermal) │
                     │   5433)    │   └─────────────┬─────────────┘
                     └──────┬─────┘                 │
                            │                       │ Fault Event Triggered
                            │                       ▼
                            │             ┌───────────────────────────┐
                            │             │     LOCAL RAG PIPELINE    │
                            │             │ (all-MiniLM-L6-v2 Embed)  │
                            │             └─────────────┬─────────────┘
                            │                           │ Retrieved Context
                            │                           ▼
                            │             ┌───────────────────────────┐
                            │             │   LOCAL LLM INFERENCE     │
                            │             │   (Ollama: qwen2.5:1.5b)  │
                            │             └─────────────┬─────────────┘
                            │                           │ Structured JSON
                            │     Diagnosis Persisted   │
                            ├───────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
    ┌──────────────────┐        ┌──────────────────┐
    │     GRAFANA      │        │      REACT       │
    │  (Port 3000)     │        │  (Port 8000)     │
    │ Operational      │        │ AI Diagnosis,    │
    │ SCADA Dashboard  │        │ Evidence, RAG,   │
    │ & Time-Series    │        │ Viva AI Tutor    │
    └──────────────────┘        └──────────────────┘
```

---

## 3. Component Breakdown

### A. Ingestion & Message Broker (Eclipse Mosquitto)
- **Role**: High-throughput, asynchronous publish-subscribe message broker.
- **Protocol**: MQTT v3.1.1 / v5.0 over TCP port `1883`.
- **Decoupling**: Telemetry sources (physical sensors, CSV replay adapters, simulators) publish anonymously to `p311/machine/<machine_id>/telemetry`. The ingestion pipeline is completely decoupled from the data producer.

### B. Core Application Service (FastAPI)
- **Role**: Central orchestrator, API server, and stream distributor.
- **Asyncpg Connection Pool**: Manages 2 to 10 persistent connections to PostgreSQL with native JSONB serialization/deserialization codecs.
- **Server-Sent Events (SSE)**: Streams live 1 Hz telemetry packets, active alarms, and newly arrived diagnoses to connected frontend clients without browser polling.
- **Remote Simulator RPC**: Publishes control payloads to `p311/machine/<machine_id>/command` to dynamically inject faults or trigger emergency stops.

### C. Persistent Storage Layer (PostgreSQL 16)
- **Role**: Primary relational time-series and diagnostic knowledge store.
- **Port Mapping**: Docker container listens internally on port `5432` and maps to host port `5433` (preventing conflicts with host PostgreSQL services).
- **Data Model**:
  - `machines`: Asset registry (rated voltage, rated FLA, rated RPM, health state).
  - `telemetry`: High-frequency operational time-series data with indexing on `(machine_id, timestamp DESC)`.
  - `fault_events`: Historical alarm log with deterministic rule triggers and sensor snapshots stored as JSONB.
  - `diagnoses`: AI-synthesized root-cause analyses, recommended checklists, corrective maintenance procedures, and RAG knowledge citations.
  - `knowledge_documents`: Markdown manuals, operating limits, and ISO guidelines.

### D. Deterministic Fault Detector
- **Execution Budget**: < 5 ms per telemetry packet.
- **Standard Standards**:
  - **ISO 10816-3**: Mechanical vibration severity evaluation across Zone A (Good), Zone B (Acceptable), Zone C (Warning > 4.5 mm/s), Zone D (Trip > 7.1 mm/s).
  - **IEC 60034-1**: Stator thermal insulation limits (Class F thermal trip at 95.0 °C).
  - **Overload / Stall**: Stator line current exceeding 125% Full Load Amperes (FLA > 11.25 A) with rotor speed drop (slip > 6%).
  - **Lubrication**: Forced oil lubrication circuit depletion (< 2.0 bar).
  - **Zero Hallucination Safety**: LLM is never called to determine whether an emergency trip is required. Trips are executed deterministically.

### E. Semantic Retrieval-Augmented Generation (Local RAG)
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` running natively on CPU.
- **Dimensionality**: 384 dimensions, cosine similarity search.
- **Corpus**: Engineering manuals under `knowledge_base/` covering:
  - Bearing fatigue, raceway spalling, lubrication breakdown.
  - Induction motor overheating, cooling fan cowls, ventilation clogs.
  - Mechanical overload, driven load binding, voltage unbalance.
  - Mechanical unbalance, soft foot, and laser alignment.
  - Auxiliary lubrication and oil pressure loss.
- **Top-K Retrieval**: Extracts top 3 most relevant documentation sections and constructs a grounded prompt context for the LLM.

### F. Local LLM (Ollama & Qwen 2.5)
- **Model**: `qwen2.5:1.5b` (Q4_K_M quantization).
- **VRAM Footprint**: ~1.35 GB VRAM on NVIDIA GeForce RTX 2050 (4 GB total), leaving > 2.5 GB headroom for OS display rendering.
- **Inference Speed**: ~30 tokens/sec.
- **Guaranteed Output**: Enforced JSON schema mode (`format: "json"`). If the LLM is unavailable or times out, the backend gracefully falls back to deterministic rule-based template generation without dropping telemetry or crashing the server.

---

## 4. Division of Responsibility: Grafana vs. React

| Feature / Responsibility | Grafana (Port 3000) | React Application (Port 8000) |
| :--- | :---: | :---: |
| **Primary Audience** | Plant Operators / SCADA Engineers | Reliability Engineers & Academic Evaluators |
| **Telemetry Time-Series (Temp, Current, Vib, RPM)** | **Primary (High-density SQL plots)** | Secondary (50-sample rolling sparklines) |
| **Operational Threshold Reference Lines** | **Primary (Zone C / Zone D limits)** | Secondary |
| **Aggregations, Min/Max/Avg Windows** | **Primary (PostgreSQL SQL queries)** | None |
| **AI Root Cause Diagnosis & Likely Causes** | None | **Primary (Interactive inspection)** |
| **RAG Documentation Citations & Similarity** | None | **Primary (Inspect manual excerpts)** |
| **Sensor Evidence vs Inferred Data Audit** | Secondary (Raw JSON view) | **Primary (Structured side-by-side comparison)** |
| **Printable Maintenance Work Order Generator** | None | **Primary (HTML / PDF print layout)** |
| **Interactive Viva AI Tutor & Q&A Assistant** | None | **Primary (Chat with RAG context)** |
| **Remote Simulator Fault Injection Controls** | None | **Primary (Inject 7 fault modes, Reset, Stop)** |
| **Digital Twin Dynamic Motor Animation** | None | **Primary (SVG rotor RPM & thermal glow)** |

---

## 5. Security & Persistence Strategy

- **PostgreSQL Volume**: `p311_postgres_data` Docker volume retains telemetry history across container restarts and host reboots.
- **Grafana Provisioning**: Datasources and dashboards are auto-provisioned declaratively from `docker/grafana/provisioning/`. No manual configuration is required when deploying to a clean system.
- **Anonymous Viewer Access**: Grafana is configured with anonymous Viewer permissions (`GF_AUTH_ANONYMOUS_ENABLED=true`), enabling instant access without login hurdles during university project demonstrations.
