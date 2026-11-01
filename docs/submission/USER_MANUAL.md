# User & Operations Manual
## Project P_311: Knowledge-Driven IoT Fault Diagnosis Assistant

---

## 1. System Requirements & Prerequisites

### 1.1 Hardware Specifications
- **Host Workstation / Laptop**:
  - **Processor**: Intel Core i5 (10th Gen or newer) / AMD Ryzen 5 or equivalent (Minimum: 4 cores).
  - **System Memory (RAM)**: Minimum 8 GB (16 GB Recommended).
  - **Storage**: Minimum 10 GB free SSD storage.
  - **GPU (Optional for LLM Acceleration)**: NVIDIA GPU with $\ge 4\text{ GB}$ VRAM (e.g., RTX 2050 / 3050 / GTX 1650). CPU inference is supported automatically as a fallback.
- **Operating System**: Linux (Debian 12/13, Ubuntu 22.04/24.04 LTS, or Fedora).

### 1.2 Software Dependencies
Ensure the following packages are installed on the host system:
1. **Python 3.10 to 3.13**: `sudo apt install -y python3 python3-venv python3-pip`
2. **Node.js (v18+) & npm**: `sudo apt install -y nodejs npm`
3. **Docker & Docker Compose**: `sudo apt install -y docker.io docker-compose-plugin`
4. **Ollama (Local LLM Daemon)**: Installed from [ollama.com](https://ollama.com):
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ollama pull qwen2.5:1.5b
   ```

---

## 2. Installation & Environment Configuration

### 2.1 Clone Repository & Workspace Navigation
```bash
git clone https://github.com/Kai-Kodes/IoT_Project.git
cd IoT_Project
```

### 2.2 Environment Configuration (`.env`)
A template configuration file is provided at `.env.example`. Create your local `.env`:
```bash
cp .env.example .env
```
Default parameters in `.env`:
```ini
# MQTT Broker Settings
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_TELEMETRY_TOPIC_SUB=p311/machine/+/telemetry

# PostgreSQL Database Settings
USE_POSTGRES=true
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=p311_iot
POSTGRES_USER=p311_admin
POSTGRES_PASSWORD=p311_industrial_secret

# Grafana SCADA Settings
GRAFANA_PORT=3000
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
GRAFANA_URL=http://localhost:3000

# Local LLM (Ollama) Settings
LLM_MODEL=qwen2.5:1.5b
LLM_BASE_URL=http://localhost:11434
LLM_NUM_CTX=2048
LLM_TIMEOUT_SECONDS=45.0

# Local RAG Embedding Settings
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
VECTOR_STORE_PATH=data/vector_store
KNOWLEDGE_BASE_DIR=knowledge_base
```

---

## 3. Starting the Application

### 3.1 One-Click Master "Boss" Script (Recommended)
The repository includes a fully automated master start script that handles container orchestration, virtual environment setup, background daemons, and public tunneling with automatic fallback:
```bash
./start.sh
```

**Execution Pipeline performed by `./start.sh`:**
1. **Infrastructure Containers**: Starts PostgreSQL (port 5433) and Grafana (port 3000) via Docker Compose. Dynamically checks if Mosquitto is active on the host (port 1883) to avoid port collision errors.
2. **Local LLM Health Check**: Pings Ollama on port 11434; verifies `qwen2.5:1.5b` availability.
3. **Python Virtual Environment**: Verifies `.venv` exists and dependencies are satisfied.
4. **FastAPI Application**: Launches Uvicorn server on port 8000 serving both API endpoints and the compiled React frontend.
5. **Industrial Motor Simulator**: Starts `simulator/motor_simulator.py` streaming 1 Hz telemetry to MQTT.
6. **Public Web Tunnel**: Launches a secure tunnel (Cloudflare QUIC / Wormhole) and displays the public live URL.

### 3.2 Manual Multi-Terminal Startup (Alternative)
If preferred for debugging, services can be launched manually in separate terminals:

**Terminal 1: Start Docker Infrastructure**
```bash
docker compose up -d postgres grafana
```

**Terminal 2: Start Backend Application**
```bash
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3: Start Motor Telemetry Simulator**
```bash
source .venv/bin/activate
python simulator/motor_simulator.py
```

---

## 4. Accessing System Interfaces

Once the application is running, the following endpoints are available:

| Service | Access URL | Default Credentials | Description |
| :--- | :--- | :--- | :--- |
| **React AI Diagnostic Dashboard** | [http://localhost:8000](http://localhost:8000) | *None (Direct Access)* | Main diagnostic interface, Digital Twin, fault injection, and Viva AI chat. |
| **Grafana SCADA Dashboard** | [http://localhost:3000](http://localhost:3000) | *Anonymous Viewer Enabled*<br/>Admin: `admin` / `admin` | Operational time-series SCADA trends with ISO limit lines. |
| **Interactive OpenAPI Documentation** | [http://localhost:8000/docs](http://localhost:8000/docs) | *None* | Interactive Swagger UI for testing all REST endpoints. |
| **System Health API** | [http://localhost:8000/api/health](http://localhost:8000/api/health) | *None* | JSON diagnostic health status. |

---

## 5. Dashboard User Guide & Operating Instructions

### 5.1 Monitoring Real-Time Telemetry
1. Open [http://localhost:8000](http://localhost:8000) in any modern browser (Chrome, Firefox, Edge).
2. The dashboard connects immediately to the `/api/telemetry/stream` Server-Sent Events endpoint.
3. Verify live sensor values:
   - **Stator Temperature**: Normal baseline $45^\circ\text{C} - 65^\circ\text{C}$.
   - **Vibration Velocity RMS**: Normal baseline $< 1.8\text{ mm/s}$ (ISO Zone A).
   - **Stator Current**: Rated nominal $8.8\text{ A} - 9.0\text{ A}$.
   - **Shaft Speed**: Nominal $1485\text{ RPM}$.
   - **Lubrication Pressure**: Nominal $3.8\text{ bar} - 4.5\text{ bar}$.
4. Observe the **SVG Digital Twin Motor**: The motor rotor spins in real-time proportional to RPM, and the stator housing illuminates dynamically reflecting temperature.

### 5.2 Injecting Faults for Demonstration
The dashboard provides a dedicated **Simulation Control Panel** with one-click buttons to inject 6 physical failure modes:

| Fault Mode | Injected Physical Anomaly | Standard Triggered |
| :--- | :--- | :--- |
| **Bearing Degradation** | Vibration climbs to $5.8\text{ mm/s}$; thermal friction increases temperature to $> 78^\circ\text{C}$. | ISO 10816 Zone C Alarm |
| **Motor Overheating** | Temperature rises rapidly to $> 88^\circ\text{C}$ without mechanical vibration. | IEC Class F Thermal Warning |
| **Motor Overload** | Current climbs to $12.5\text{ A}$ ($> 125\%$ FLA); rotor speed drops to $1410\text{ RPM}$. | Electrical FLA Slip Trip |
| **Excessive Vibration** | Mechanical looseness; vibration spikes to $> 7.2\text{ mm/s}$. | ISO 10816 Zone D Trip |
| **Low Pressure** | Lubrication pump failure; oil pressure drops to $< 2.2\text{ bar}$. | Auxiliary Circuit Warning |
| **Sensor Anomaly** | Temperature probe disconnects; reading registers an impossible $155^\circ\text{C}$. | Physical Range Anomaly |
| **Reset Baseline** | Clears all faults and restores motor to normal nominal operation. | Normal State |

### 5.3 Reviewing AI Diagnostic Reports
When a fault triggers:
1. The **Audio Alarm Annunciator** emits an industrial warning tone (can be muted using the audio toggle).
2. The **Active Diagnosis Card** displays:
   - **Root Cause Analysis**: Identified failure mechanism.
   - **Severity Badge**: WARNING (Yellow), HIGH (Orange), or CRITICAL (Red).
   - **Diagnostic Checklist**: Numbered inspection steps for plant electricians.
   - **Corrective Actions**: Specific maintenance interventions (e.g., grease replenishment, impeller cleaning).
   - **RAG Manual Citations**: Clickable badges citing exact sections from equipment handbooks.

### 5.4 Generating Printable Maintenance Work Orders
1. In the diagnosis section, click the **"Print Work Order"** button (or navigate to `http://localhost:8000/api/reports/work-order`).
2. An industrial HTML work order is generated containing asset specifications, measured sensor evidence at alarm time, mandatory Lockout/Tagout (LOTO) safety instructions, checklist items, and technician sign-off blocks.
3. Click **"Print / Save as PDF"** to produce an official physical or digital maintenance order.

### 5.5 Interacting with the Viva AI Tutor Chat
1. Scroll to the **Viva Assistant Chat** section at the bottom of the dashboard.
2. Ask any technical viva question, such as:
   - *"Why did the bearing degradation alarm trigger?"*
   - *"What is ISO 10816-3 Zone C?"*
   - *"What safety precautions should I take before opening the terminal box?"*
3. The AI assistant responds in real-time, synthesizing answers grounded in the retrieved engineering manuals and current machine telemetry.

---

## 6. Stopping the Application

To shut down all running background processes, disconnect tunnels, and stop Docker containers cleanly, execute the master stop script:
```bash
./stop.sh
```

**Cleanup performed by `./stop.sh`:**
- Terminates public tunnel background processes (Cloudflare / Wormhole).
- Stops the Python telemetry simulator.
- Stops the FastAPI application server on port 8000.
- Executes `docker compose down` for PostgreSQL and Grafana containers.
- Removes temporary PID files from `logs/`.

---

## 7. Troubleshooting Guide

### 7.1 Port 1883 Already in Use (Mosquitto Conflict)
- **Symptom**: Docker reports `failed to bind host port 0.0.0.0:1883/tcp: address already in use`.
- **Cause**: A native Mosquitto broker service is already running on the host system (`/usr/sbin/mosquitto`).
- **Solution**: The master start script (`./start.sh`) automatically detects native Mosquitto and launches only PostgreSQL and Grafana in Docker (`docker compose up -d postgres grafana`). If starting manually, do not start the Docker Mosquitto container if the host service is active.

### 7.2 Ollama Daemon Unreachable / Offline
- **Symptom**: Dashboard shows `Ollama LLM: Offline (Fallback Mode Ready)`.
- **Cause**: The Ollama service is not running or the model `qwen2.5:1.5b` is not downloaded.
- **Solution**:
  1. Check if Ollama is running: `curl http://localhost:11434/api/version`.
  2. Start Ollama: `systemctl --user start ollama` or `ollama serve &`.
  3. Pull model: `ollama pull qwen2.5:1.5b`.
  - *Note*: If Ollama remains offline, the application continues operating seamlessly in **Fallback Mode** with zero data loss.

### 7.3 PostgreSQL Connection Error (Port 5433)
- **Symptom**: Backend logs display `PostgreSQL connection pool failed. Falling back to SQLite`.
- **Cause**: Docker container `p311-postgres` is still initializing or stopped.
- **Solution**:
  1. Check container status: `docker compose ps`.
  2. Restart database container: `docker compose up -d postgres`.
  3. Wait 5 seconds for healthcheck: `docker compose logs postgres`.
  - *Note*: The backend automatically falls back to local SQLite (`data/p311.db`), ensuring continuous monitoring.

### 7.4 Virtual Environment Package Mismatch
- **Symptom**: `ModuleNotFoundError: No module named 'fastapi'` or similar.
- **Solution**: Re-install dependencies into `.venv`:
  ```bash
  .venv/bin/pip install -r requirements.txt
  ```
