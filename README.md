# P_311: Knowledge-Driven IoT Fault Diagnosis Assistant

An edge-ready, explainable AI-assisted IoT fault diagnosis system designed for industrial electric motors.

---

## 🌟 Key Highlights

- **Edge IoT Architecture**: Decoupled MQTT pub-sub telemetry streaming at 1 Hz with zero cloud dependencies.
- **Deterministic Fault Detection**: Instant, auditable rule-based detection adhering to **ISO 10816-3** vibration standards and **IEC Class F** motor thermal ratings.
- **Local RAG Pipeline**: In-process semantic retrieval using CPU-bound embeddings (`all-MiniLM-L6-v2`) over 7 technical equipment manuals in <1 ms.
- **Resource-Aware Local LLM**: Powered by `qwen2.5:1.5b-instruct` running in Ollama (~1.35 GB VRAM), strictly within the 4 GB VRAM envelope of a laptop NVIDIA RTX 2050 GPU.
- **Resilient Fallback Mode**: Gracefully degrades to rule-and-manual deterministic reports if the LLM is offline or times out.
- **Real-Time Web Dashboard**: React 18 + Vite + Tailwind CSS with Server-Sent Events (SSE) and Recharts live multi-sensor visualization.

---

## 🏗 Target Architecture

```
REAL DATA / CSV REPLAY / SIMULATOR
                ↓
              MQTT (1 Hz JSON)
                ↓
            MOSQUITTO (Port 1883)
                ↓
          FASTAPI BACKEND
                ↓
       ┌────────┴──────────────┐
       │                       │
       ▼                       ▼
  POSTGRESQL             FAULT DETECTOR
  (Port 5433)            (ISO 10816, FLA, Thermal)
       │                       │
       │                       ▼
       │                      RAG (all-MiniLM-L6-v2)
       │                       │
       │                       ▼
       │                     OLLAMA (qwen2.5:1.5b)
       │                       │
       │               Diagnosis Persisted
       ├───────────────────────┘
       │
       ▼
    GRAFANA (Port 3000)      REACT DASHBOARD (Port 8000)
    Operational SCADA &      AI Diagnosis, RAG Citations,
    Time-Series Monitoring   Viva Tutor, Simulator Controls
```

---

## 🖥 Visualization Division: Grafana vs. React

| System | URL | Core Responsibilities |
| :--- | :--- | :--- |
| **Grafana SCADA Monitor** | [http://localhost:3000](http://localhost:3000) | Operational time-series telemetry (Temperature, Vibration RMS, Current, RPM, Pressure, Voltage), ISO threshold reference lines, active alarm states, recent fault audit logs. |
| **React AI Assistant** | [http://localhost:8000](http://localhost:8000) | Explainable AI root-cause diagnosis, sensor evidence vs inferred data, retrieved technical manual citations, interactive Viva AI tutor, remote fault injection simulator, and printable PDF maintenance work orders. |

---

## 💻 Hardware Prerequisites & Resource Budget

This project is tailored specifically for consumer laptop hardware running Debian Linux:
- **CPU**: Intel Core i5-12450H (12th Gen)
- **RAM**: 16 GB (Application stack + Docker containers use < 1.2 GB RAM total)
  - `p311-postgres`: ~66 MiB RAM
  - `p311-grafana`: ~49 MiB RAM
  - `FastAPI + Mosquitto + Simulator`: ~150 MiB RAM
  - `Ollama daemon`: ~300 MiB RAM (CPU baseline)
- **GPU**: NVIDIA GeForce RTX 2050 (4 GB VRAM) — LLM uses ~1.35 GB VRAM
- **OS**: Debian Linux (Debian 12/13 / Ubuntu compatible)

---

## 🚀 Quick Start (Complete Stack)

### ⚡ One-Click Master "Boss" Scripts (Recommended)
You can start or stop the entire stack (PostgreSQL, Grafana, Mosquitto, Ollama, Backend, Telemetry Simulator, and Public Tunnel) with single commands:

```bash
# Start EVERYTHING
./start.sh

# Stop EVERYTHING cleanly
./stop.sh
```

---

### Manual Setup & Commands

### 1. Prerequisites Installation
Ensure Python 3.10+, Node.js 18+, Docker Compose, and Ollama are installed:
```bash
sudo apt update && sudo apt install -y python3-venv docker-compose-plugin
```

Ensure Ollama is running and pull the lightweight model:
```bash
ollama pull qwen2.5:1.5b
```

### 2. Start PostgreSQL & Grafana Infrastructure
Launch Mosquitto, PostgreSQL (port 5433), and Grafana (port 3000) via Docker Compose:
```bash
docker compose up -d
```
*Note: Grafana datasources and SCADA dashboards are automatically provisioned with anonymous Viewer access enabled.*

### 3. Setup Python Backend & Build React Frontend
```bash
make setup
```

### 4. Run Application & Simulator
```bash
make run
```
Access the services:
- 📊 **Grafana SCADA Telemetry**: [http://localhost:3000](http://localhost:3000) *(Direct dashboard access, no login needed)*
- 🌐 **React AI Diagnosis Dashboard**: [http://localhost:8000](http://localhost:8000)
- 📖 **Interactive API Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 🩺 **Health Status Endpoint**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 5. Replay Real-World / Benchmark Datasets
Stream external or benchmark telemetry CSV files over MQTT directly into the system:
```bash
# Accelerated 5x replay
.venv/bin/python scripts/replay_dataset.py --file data/synthetic_motor_telemetry.csv --rate 5.0

# 24/7 continuous SCADA monitoring loop
.venv/bin/python scripts/replay_dataset.py --file data/synthetic_motor_telemetry.csv --loop
```

### 6. SQLite to PostgreSQL Migration Utility
If historical data exists in SQLite (`data/p311.db`), migrate it seamlessly to PostgreSQL:
```bash
.venv/bin/python scripts/migrate_sqlite_to_postgres.py
```

### 7. Run the Automated College Viva Demo
Run the automated evaluation sequence in your terminal:
```bash
make demo
```
or inject fault modes interactively via the **Fault Simulator** tab on the React web dashboard!

### 8. Stop Services
```bash
make stop
docker compose stop
```

---

## 🧪 Automated Test Suite
Run the 25 unit and integration tests:
```bash
make test
```
**Test Coverage Includes**:
- Pydantic schema validation & physical boundary checks.
- Matrix verification of all deterministic fault detection rules.
- SQLite WAL mode persistence, indexing, and retention pruning.
- Local RAG chunking, MiniLM embeddings, and cosine vector retrieval.
- Local LLM diagnosis formatting and offline deterministic fallback.
- FastAPI REST endpoints and SSE streaming.
- Live MQTT publish-subscribe ingestion loop.

---

## 🐳 Optional Docker Deployment

If you prefer running via Docker containers:
```bash
make docker-up
```
Stop containers:
```bash
make docker-down
```

---

## 📚 Technical Documentation Library

- [Architecture Specification](docs/architecture.md)
- [MQTT Protocol & Topics](docs/mqtt.md)
- [Deterministic Fault Detection](docs/fault-detection.md)
- [RAG & Vector Retrieval](docs/rag.md)
- [Local LLM Constraints & Strategy](docs/llm.md)
- [Database Schema & Storage Policy](docs/database.md)
- [REST & SSE API Specification](docs/api.md)
- [Official 13-Step Demonstration Guide](docs/demo.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
- [Viva Voce & Oral Defense Notes](docs/viva-notes.md)

---

## 📊 Dataset and Experimental Evaluation

To answer the core academic and viva question:
> *"What data did you use, how was it generated, how large is it, what are the fault classes, and how well does your system detect them?"*

### 1. Data Source & Generation Methodology
- **Physical Apparatus**: Simulated 3-phase Squirrel-Cage Induction Motor (11 kW, 400V, 50Hz, 4-Pole, TEFC).
- **Physics Engine**: Multi-variable differential equation model incorporating torque-slip curves, thermal inertia exponential moving average lag, dynamic lubrication viscosity breakdown, and Gaussian sensor noise (`simulator/dataset_generator.py`).
- **Reproducibility**: 100% deterministic generation using random seed `seed=42`.
- **Preserved Pipeline**: The generated dataset integrates alongside the real-time SQLite database (`data/p311.db`) without altering the live MQTT architecture.
- **Export Artifacts**: Labeled CSV at [`data/synthetic_motor_telemetry.csv`](data/synthetic_motor_telemetry.csv) with JSON metadata at [`data/dataset_metadata.json`](data/dataset_metadata.json).

### 2. Dataset Size & Features
- **Total Records**: **4,000 samples** (recorded at 1.0 Hz = 4,000 seconds / ~66.7 minutes of operation).
- **Telemetry Schema**:
  1. `timestamp` (ISO 8601 UTC)
  2. `machine_id` (`MOTOR-001`)
  3. `temperature` (Stator surface, °C)
  4. `vibration` (Velocity RMS, mm/s ISO 10816-3)
  5. `current` (Motor line current, A)
  6. `rpm` (Shaft rotational speed, RPM)
  7. `voltage` (Line voltage, V)
  8. `pressure` (Auxiliary lubrication/cooling, bar)
  9. `operating_state` (`running`, `warning`, `alarm`, `sensor_error`)
  10. `fault_label` (Ground truth operating condition)
  11. `severity` (`normal`, `warning`, `high`, `critical`)

### 3. Fault Classes & Class Distribution
| Fault Class | Description | Physical Symptoms | Samples | Percentage |
| :--- | :--- | :--- | :--- | :--- |
| `normal` | Baseline steady-state operation | Temp ~51.5°C, Vib ~1.45 mm/s, Curr ~8.8A, RPM ~1485 | 1,800 | 45.0% |
| `bearing_degradation` | Spalling on bearing raceway & friction | Vib > 4.5 mm/s (Zone D: 8.4 mm/s), Temp > 75°C (89.5°C) | 400 | 10.0% |
| `motor_overheating` | Cooling fan failure / blocked cowl | Temp > 85°C (104.2°C), Vib normal (2.1 mm/s) | 400 | 10.0% |
| `motor_overload` | Driven mechanical overload / stall | Current > 11.5A (15.8A), RPM drops to 1395, high slip | 400 | 10.0% |
| `excessive_vibration` | Mechanical unbalance or loose bolts | Vib > 4.5 mm/s (11.2 mm/s), Temp normal (62.0°C) | 400 | 10.0% |
| `low_pressure` | Lubrication oil delivery loss | Pressure drops < 3.0 bar (1.6 bar) | 400 | 10.0% |
| `sensor_anomaly` | Instrument open-circuit / probe failure | Sensor spike to 999.0°C (out of physical bounds) | 200 | 5.0% |

### 4. Experimental Detection Results
The existing **deterministic rule-based fault detector** was evaluated across all 4,000 ground-truth samples without any machine learning training:

- **Overall Accuracy**: **99.38%** (3,975 / 4,000 correct)
- **Macro Precision**: **99.02%**
- **Macro Recall**: **99.61%**
- **Macro F1-Score**: **99.31%**
- **Weighted F1-Score**: **99.38%**

#### Per-Class Performance
| Class Name | Precision | Recall | F1-Score | Support |
| :--- | :--- | :--- | :--- | :--- |
| `normal` | 99.72% | 99.00% | 99.36% | 1,800 |
| `bearing_degradation` | 99.75% | 99.25% | 99.50% | 400 |
| `motor_overheating` | 98.76% | 99.25% | 99.00% | 400 |
| `motor_overload` | 99.75% | 100.00% | 99.88% | 400 |
| `excessive_vibration` | 99.01% | 100.00% | 99.50% | 400 |
| `low_pressure` | 99.50% | 99.75% | 99.63% | 400 |
| `sensor_anomaly` | 96.62% | 100.00% | 98.28% | 200 |

*Physical Transition Note*: The minor 0.62% discrepancy reflects realistic physical inertia: when bearing degradation is injected, vibration spikes instantly while frictional heating requires 2–3 seconds to cross the 75°C threshold, correctly exhibiting transient excessive vibration during thermal ramp-up.

### 5. Vector RAG Retrieval Relevance
Evaluated across 7 benchmark domain-specific technical queries matching industrial equipment manuals:
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (Local CPU)
- **Total Indexed Chunks**: 34 chunks across 7 technical manuals
- **Mean Reciprocal Rank (MRR)**: **1.0000**
- **Top-1 Hit Rate**: **100.00%**
- **Top-3 Hit Rate**: **100.00%**
- **Average Top-1 Cosine Similarity**: **0.6499**

### 6. Visualizations & Plots
Academic publication figures are saved in [`experiments/plots/`](experiments/plots/):
1. **`experiments/plots/sensor_time_series.png`**: 4-panel time series showing Temperature, Vibration, Current, and Pressure with shaded, color-coded fault episodes.
2. **`experiments/plots/normal_vs_fault_distributions.png`**: Boxplots showing distinct sensor distributions separating normal vs fault modes.
3. **`experiments/plots/class_distribution.png`**: Labeled sample counts and percentage share across all 7 classes.
4. **`experiments/plots/confusion_matrix.png`**: 7x7 annotated confusion matrix heatmap.

### 7. How to Reproduce All Experiments
Generate dataset, evaluate detector, evaluate RAG, and recreate all plots with one command:
```bash
make experiments
```
Or run individually:
```bash
make dataset                                # Generates CSV & Metadata
.venv/bin/python experiments/evaluate_detector.py # Runs detector evaluation
.venv/bin/python experiments/evaluate_rag.py      # Runs RAG benchmark
.venv/bin/python experiments/plot_generator.py    # Generates 300 DPI figures
```

---

## 👨‍💻 College Viva Summary
For oral examinations, refer to [docs/viva-notes.md](docs/viva-notes.md) for detailed explanations of:
1. *Why MQTT is superior to HTTP in sensor networks.*
2. *Why deterministic rule systems must precede probabilistic LLMs.*
3. *How RAG eliminates hallucinations using technical manuals.*
4. *Why local 1.5B quantized LLMs are optimal for edge laptop hardware.*
5. *How the system achieves zero-downtime graceful fallback when Ollama is offline.*
6. *How synthetic physical telemetry was generated and validated against ISO 10816-3 standards.*

