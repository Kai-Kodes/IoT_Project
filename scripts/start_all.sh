#!/usr/bin/env bash
# ============================================================
# P_311: Start All Services Script (Native Debian Environment)
# ============================================================
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "============================================================"
echo " Starting P_311: Knowledge-Driven IoT Fault Diagnosis System"
echo "============================================================"

# 1. Check Python Virtual Environment
if [ ! -d ".venv" ]; then
    echo "[!] Virtual environment .venv not found. Setting up..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

# 2. Check Mosquitto MQTT Broker
echo "[1/4] Checking Mosquitto MQTT Broker..."
if ss -tuln | grep -q ":1883 "; then
    echo "  [✓] Mosquitto is active on port 1883"
else
    echo "  [!] Mosquitto is not running on port 1883."
    echo "      Starting local Mosquitto..."
    mosquitto -d -p 1883 || docker run -d --name p311-mosquitto -p 1883:1883 eclipse-mosquitto:2
fi

# 3. Check Local LLM (Ollama)
echo "[2/4] Checking Local Ollama Service..."
if curl -s http://localhost:11434/api/version > /dev/null; then
    echo "  [✓] Ollama is online"
else
    echo "  [!] Ollama is not responding at http://localhost:11434"
    echo "      The system will run in Graceful Fallback Mode (Deterministic Rules + RAG)."
fi

# 4. Start Backend Service
echo "[3/4] Starting FastAPI Backend (Port 8000)..."
mkdir -p logs
nohup .venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
disown $BACKEND_PID 2>/dev/null || true
echo $BACKEND_PID > logs/backend.pid
echo "  [✓] Backend running (PID: $BACKEND_PID, Log: logs/backend.log)"

# Wait for backend health check
sleep 3

# 5. Start Industrial Machine Simulator
echo "[4/4] Starting Industrial Motor Telemetry Simulator..."
nohup .venv/bin/python simulator/motor_simulator.py > logs/simulator.log 2>&1 &
SIM_PID=$!
disown $SIM_PID 2>/dev/null || true
echo $SIM_PID > logs/simulator.pid
echo "  [✓] Simulator running (PID: $SIM_PID, Log: logs/simulator.log)"

echo "============================================================"
echo " SYSTEM ACTIVE AND READY!"
echo "============================================================"
echo " - Dashboard URL:       http://localhost:8000"
echo " - OpenAPI / Docs URL:  http://localhost:8000/docs"
echo " - Health API:          http://localhost:8000/api/health"
echo ""
echo " To run the 13-step automated demo:"
echo "   .venv/bin/python scripts/run_demo.py"
echo ""
echo " To stop all services:"
echo "   ./scripts/stop_all.sh"
echo "============================================================"
