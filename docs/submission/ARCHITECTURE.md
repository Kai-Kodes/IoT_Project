# System Architecture & Engineering Design
## Project P_311: Knowledge-Driven IoT Fault Diagnosis Assistant

---

## 1. Architectural Philosophy & Design Principles

The P_311 architecture is engineered around three core industrial tenets:
1. **Separation of Safety from AI Reasoning**: Emergency equipment shutdown and alarm triggers must be deterministic, mathematically verifiable, and instantaneous (< 5 ms). They must never depend on the non-deterministic latency or probabilistic output of a Large Language Model.
2. **Edge Autonomy (Zero Cloud Footprint)**: Telemetry streams, database storage, vector similarity search, and generative reasoning execute 100% locally on standard workstation hardware without external network dependencies.
3. **Dual Presentation Paradigms**: Complete division of operational time-series monitoring (Grafana SCADA) from interactive engineering root-cause analysis and academic defense (React Application).

---

## 2. Component Architecture Diagram

The following Mermaid diagram illustrates the interconnected software components, network ports, protocols, and data pathways of the implemented system:

```mermaid
graph TD
    subgraph DataProducer ["1. Telemetry Producer Layer"]
        SIM["Motor Telemetry Simulator<br/>(simulator/motor_simulator.py)<br/>11 kW 3-Phase Induction Model"]
        REPLAY["CSV Dataset Replay Adapter<br/>(scripts/replay_dataset.py)"]
    end

    subgraph MessageBroker ["2. Ingestion & Messaging Layer"]
        MOSQ["Eclipse Mosquitto Broker<br/>Port: 1883 (TCP / QoS 1)<br/>Topic: p311/machine/+/telemetry"]
    end

    subgraph CoreBackend ["3. Application & Intelligence Engine (FastAPI)"]
        MQTT_CONS["Async MQTT Consumer<br/>(paho-mqtt v2 thread)"]
        VAL["Schema Validation & Parser<br/>(Pydantic: TelemetryIn)"]
        
        DETECTOR["Deterministic Fault Detector<br/>(ISO 10816-3 & IEC 60034-1)<br/>Execution: &lt; 5 ms"]
        
        RAG["Local RAG Engine<br/>(all-MiniLM-L6-v2 on CPU)<br/>384-dim Cosine Search: &lt; 1 ms"]
        KB[("Knowledge Base Corpus<br/>knowledge_base/*.md<br/>34 Chunk Embeddings")]
        
        LLM_CLIENT["Local LLM Client (Ollama)<br/>Model: qwen2.5:1.5b (1.35 GB VRAM)<br/>Enforced JSON Mode"]
        FALLBACK["Deterministic Rule Fallback Engine<br/>(Zero-Crash Standby)"]
        
        SSE["Server-Sent Events (SSE) Broadcaster<br/>Endpoint: /api/telemetry/stream"]
        REST["FastAPI REST Endpoints<br/>Port: 8000 (/api/*)"]
    end

    subgraph PersistenceLayer ["4. Dual Storage Layer"]
        PG[("PostgreSQL 16 (Primary)<br/>Port: 5433 (Docker)<br/>asyncpg Pool (2-10 conn)<br/>JSONB Schema")]
        SQLITE[("SQLite 3 (Fallback)<br/>data/p311.db (WAL Mode)")]
    end

    subgraph PresentationLayer ["5. Dual Presentation Layer"]
        GRAFANA["Grafana SCADA Dashboard<br/>Port: 3000 (Docker)<br/>Direct SQL Time-Series Queries<br/>ISO Limit Lines"]
        REACT["React 18 + Vite Dashboard<br/>Port: 8000 (Web UI)<br/>Live Telemetry Sparklines<br/>SVG Digital Twin Motor<br/>Audio Alarm Annunciator<br/>Printable Work Order<br/>Viva AI Tutor Chat"]
    end

    %% Data Flow Connections
    SIM -->|MQTT Publish| MOSQ
    REPLAY -->|MQTT Publish| MOSQ
    MOSQ -->|MQTT Subscribe| MQTT_CONS
    MQTT_CONS --> VAL
    VAL --> DETECTOR
    VAL -->|Async Insert| PG
    VAL -.->|Fallback Insert| SQLITE
    
    DETECTOR -->|Normal| SSE
    DETECTOR -->|Fault Event Triggered| RAG
    KB -.->|Indexed Chunks| RAG
    RAG -->|Top-3 Excerpts & Evidence| LLM_CLIENT
    LLM_CLIENT -->|HTTP :11434| OLLAMA["Ollama Daemon"]
    OLLAMA -->|Structured JSON| LLM_CLIENT
    LLM_CLIENT -.->|On Timeout / Offline| FALLBACK
    
    LLM_CLIENT -->|Persist Diagnosis| PG
    FALLBACK -->|Persist Diagnosis| PG
    
    VAL --> SSE
    SSE -->|1 Hz SSE Stream| REACT
    REST -->|Control RPC / Work Order| REACT
    PG -->|SQL Ingestion| GRAFANA
    REACT -->|Fault Injection RPC| REST
    REST -->|p311/machine/+/command| MOSQ
```

---

## 3. End-to-End Data Flow Architecture

The data lifecycle proceeds through 5 distinct sequential stages:

```mermaid
sequenceDiagram
    autonumber
    participant Sim as Motor Simulator
    participant Broker as Mosquitto (1883)
    participant Backend as FastAPI Ingestion
    participant Detector as Rule Detector (<5ms)
    participant DB as PostgreSQL (5433)
    participant RAG as RAG Vector Store
    participant LLM as Ollama (qwen2.5)
    participant UI as React UI (8000)
    participant SCADA as Grafana (3000)

    Sim->>Broker: MQTT Publish (1 Hz JSON payload)
    Broker->>Backend: Message Delivered (p311/machine/MOTOR-001/telemetry)
    Backend->>Backend: Pydantic Validation (TelemetryIn)
    
    par In-Memory Detection & Persistence
        Backend->>Detector: Evaluate Telemetry against ISO Thresholds
        Backend->>DB: Async Bulk Insert (telemetry table)
        Backend->>UI: Broadcast Telemetry via SSE (/api/telemetry/stream)
    end
    
    opt Fault Event Detected (e.g., Vibration > 4.5 mm/s & Temp > 75°C)
        Detector->>DB: Persist Fault Event (fault_events table)
        Detector->>RAG: Query Vector Store (Cosine Similarity on CPU)
        RAG-->>Detector: Return Top-3 Manual Excerpts (similarity >= 0.30)
        
        alt Ollama LLM is Online
            Detector->>LLM: POST /api/generate (Telemetry + Rules + Manuals)
            LLM-->>Detector: Structured Diagnosis JSON (< 3.5s)
        else Ollama Offline or Timed Out
            Detector->>Detector: Execute Deterministic Fallback Template
        end
        
        Detector->>DB: Persist Diagnosis (diagnoses table)
        Detector->>UI: Broadcast Diagnosis Event via SSE
    end
    
    Note over SCADA,DB: Grafana queries PostgreSQL directly every 2s for SCADA trends
```

---

## 4. Deployment Architecture

Project P_311 is deployed across a combination of containerized infrastructure services and host-native execution processes to maximize hardware efficiency and GPU acceleration:

```mermaid
graph LR
    subgraph HostWorkstation ["Debian Linux Host Workstation (redsheronin)"]
        subgraph DockerCompose ["Docker Compose Stack (proj_default)"]
            PG_CONT["Container: p311-postgres<br/>Image: postgres:16-alpine<br/>Port: 5433:5432<br/>Vol: p311_postgres_data"]
            GRAF_CONT["Container: p311-grafana<br/>Image: grafana:11.2.0<br/>Port: 3000:3000<br/>Vol: p311_grafana_data"]
            MOSQ_CONT["Container: p311-mosquitto<br/>(or Native Host Mosquitto)<br/>Port: 1883:1883"]
        end

        subgraph NativeProcesses ["Host Native Run-Time (Python 3.13 venv)"]
            APP["FastAPI Server (uvicorn)<br/>backend/app/main.py<br/>Port: 8000"]
            SIM_PROC["Motor Simulator<br/>simulator/motor_simulator.py"]
            VEC["RAG Pipeline<br/>all-MiniLM-L6-v2 (CPU)"]
        end

        subgraph LocalAI ["Local GPU Acceleration"]
            OLLAMA_SRV["Ollama Daemon (systemd)<br/>Port: 11434<br/>Model: qwen2.5:1.5b<br/>GPU: NVIDIA RTX 2050 (1.35 GB VRAM)"]
        end
    end

    SIM_PROC -->|TCP 1883| MOSQ_CONT
    APP -->|TCP 1883| MOSQ_CONT
    APP -->|TCP 5433| PG_CONT
    GRAF_CONT -->|Internal Bridge| PG_CONT
    APP -->|HTTP 11434| OLLAMA_SRV
```

---

## 5. Database Architecture & Schema Design

The storage layer implements a dual-database pattern:
- **Primary Database**: PostgreSQL 16 Alpine running in Docker, utilizing native `JSONB` data types for flexible storage of sensor evidence, triggered rule lists, recommended checklists, and manual citations.
- **Fallback Database**: SQLite 3 (`data/p311.db`) configured with Write-Ahead Logging (WAL) and synchronous normal mode, storing structured JSON as serialized text strings.

### 5.1 Entity-Relationship (ER) Diagram

```mermaid
erDiagram
    MACHINES ||--o{ TELEMETRY : "records"
    MACHINES ||--o{ FAULT_EVENTS : "triggers"
    MACHINES ||--o{ DIAGNOSES : "has"
    FAULT_EVENTS ||--|| DIAGNOSES : "analyzed_by"

    MACHINES {
        varchar(64) id PK
        varchar(255) name
        varchar(255) type
        double_precision rated_voltage
        double_precision rated_current
        double_precision rated_rpm
        varchar(32) status
        timestamptz created_at
    }

    TELEMETRY {
        bigserial id PK
        varchar(64) machine_id FK
        timestamptz timestamp
        double_precision temperature
        double_precision vibration
        double_precision current
        double_precision rpm
        double_precision voltage
        double_precision pressure
        varchar(32) operating_state
    }

    FAULT_EVENTS {
        varchar(64) id PK
        varchar(64) machine_id FK
        timestamptz timestamp
        varchar(64) fault_type
        varchar(32) severity
        double_precision confidence
        jsonb sensor_evidence
        jsonb triggered_rules
        timestamptz resolved_at
    }

    DIAGNOSES {
        varchar(64) id PK
        varchar(64) fault_event_id FK
        varchar(64) machine_id FK
        timestamptz timestamp
        varchar(255) fault_title
        varchar(32) severity
        jsonb sensor_evidence
        jsonb likely_causes
        jsonb recommended_checks
        jsonb corrective_actions
        double_precision confidence
        text uncertainty
        jsonb knowledge_sources
        text raw_llm_response
        integer execution_time_ms
        boolean is_fallback
    }
```

---

## 6. MQTT Topic Hierarchy & Communication Protocol

The MQTT layer follows an industrial topic hierarchy organized by machine namespace:

```
p311/
└── machine/
    └── {machine_id}/
        ├── telemetry   (Publisher: Simulator/Sensors  -> Subscriber: Backend)
        ├── status      (Publisher: Simulator/Sensors  -> Subscriber: Backend / LWT)
        ├── command     (Publisher: Backend REST RPC   -> Subscriber: Simulator)
        └── fault       (Publisher: Simulator/Backend  -> Subscriber: SCADA Alarms)
```

### 6.1 Topic Specifications

| Topic Pattern | QoS | Direction | Retain | Description |
| :--- | :---: | :---: | :---: | :--- |
| `p311/machine/{id}/telemetry` | **1** | Producer $\rightarrow$ Backend | `false` | Continuous 1 Hz numerical sensor vector. |
| `p311/machine/{id}/status` | **1** | Producer $\rightarrow$ Backend | `true` | Node operational state (`running`, `stopped`, `offline`). Configured as MQTT Last Will and Testament (LWT). |
| `p311/machine/{id}/command` | **1** | Backend $\rightarrow$ Producer | `false` | Remote procedure call (`inject_fault`, `reset`, `start`, `stop`). |
| `p311/machine/{id}/fault` | **1** | Backend $\rightarrow$ SCADA | `false` | High-priority event notifications when safety limits trip. |

### 6.2 Sample Telemetry JSON Payload
```json
{
  "machine_id": "MOTOR-001",
  "timestamp": "2026-11-01T09:15:32.418Z",
  "temperature": 78.4,
  "vibration": 5.12,
  "current": 9.45,
  "rpm": 1478.2,
  "voltage": 229.8,
  "pressure": 4.15,
  "state": "warning"
}
```

---

## 7. AI Diagnosis & RAG Retrieval Pipeline

The diagnostic pipeline bridges quantitative physical alarms with qualitative engineering handbooks:

```mermaid
flowchart TD
    A["Alarm Triggered (e.g. BEARING_DEGRADATION)"] --> B["Construct Semantic Query<br/>'bearing degradation high vibration zone c alarm high temperature friction'"]
    B --> C["Compute Query Embedding Vector<br/>all-MiniLM-L6-v2 (CPU: 384 dims, &lt; 1 ms)"]
    C --> D["Cosine Similarity Search vs 34 Knowledge Chunks<br/>(Dot Product over Normalized Unit Vectors)"]
    D --> E["Extract Top-3 Sections (Score &gt;= 0.30)<br/>1. bearing_troubleshooting_guide.md (Root Causes)<br/>2. bearing_troubleshooting_guide.md (Corrective Actions)<br/>3. preventive_maintenance_checklist.md"]
    E --> F["Assemble Grounded Prompt Context<br/>- Measured Telemetry Evidence<br/>- Triggered ISO Rules<br/>- Retrieved Manual Procedures"]
    F --> G{"Ollama Health Probe<br/>GET http://localhost:11434/api/version"}
    
    G -->|Online| H["Execute LLM Inference<br/>qwen2.5:1.5b (format: json, temp: 0.1)"]
    H -->|Valid JSON Output| I["Structured Diagnosis Record"]
    H -->|Timeout &gt; 45s / Parse Error| J["Activate Fallback Generator"]
    G -->|Offline / Unreachable| J
    
    J -->|Rule-Based Templates + Direct Manual Quotes| I
    I --> K["Persist to diagnoses Table (PostgreSQL / SQLite)"]
    I --> L["Broadcast to React UI via Server-Sent Events"]
```
