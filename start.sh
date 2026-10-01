#!/usr/bin/env bash
# ==============================================================================
# 🚀 P_311 Master "Boss" Start Script
# Starts EVERYTHING: Docker Containers, Ollama, Backend, Simulator & Public Tunnel
# ==============================================================================
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"
mkdir -p logs

BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}${CYAN}==============================================================================${NC}"
echo -e "${BOLD}${CYAN} 🚀 Starting P_311: Full Industrial IoT Stack & Public Tunnel${NC}"
echo -e "${BOLD}${CYAN}==============================================================================${NC}"

# ------------------------------------------------------------------------------
# 1. Clean Stale Local App & Tunnel Processes
# ------------------------------------------------------------------------------
if [ -f logs/backend.pid ]; then
    kill -9 $(cat logs/backend.pid) 2>/dev/null || true
    rm -f logs/backend.pid
fi
if [ -f logs/simulator.pid ]; then
    kill -9 $(cat logs/simulator.pid) 2>/dev/null || true
    rm -f logs/simulator.pid
fi
if [ -f logs/tunnel.pid ]; then
    kill -9 $(cat logs/tunnel.pid) 2>/dev/null || true
    rm -f logs/tunnel.pid
fi
pkill -9 -f "wormhole" 2>/dev/null || true
pkill -9 -f "cloudflared" 2>/dev/null || true
pkill -9 -f "simulator.motor_simulator" 2>/dev/null || true
pkill -9 -f "backend.app.main:app" 2>/dev/null || true

# ------------------------------------------------------------------------------
# 2. Start Infrastructure Containers (PostgreSQL, Grafana, Mosquitto)
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[1/5] Launching Infrastructure Containers (PostgreSQL, Grafana, Mosquitto)...${NC}"
if command -v docker &>/dev/null && docker info &>/dev/null; then
    if ss -tuln | grep -q ":1883 "; then
        echo -e "  ${GREEN}✓${NC} Mosquitto is active on host (port 1883)"
        docker compose up -d postgres grafana
    else
        echo -e "  [*] Starting Mosquitto, PostgreSQL and Grafana..."
        docker compose up -d
    fi
    echo -e "  ${GREEN}✓${NC} Infrastructure containers running"
else
    echo -e "  ${YELLOW}!${NC} Docker daemon unavailable. Attempting native service connections..."
fi

# ------------------------------------------------------------------------------
# 3. Check Local LLM (Ollama)
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[2/5] Checking Local Ollama AI Service...${NC}"
if curl -s http://localhost:11434/api/version &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Ollama is active on port 11434"
else
    echo -e "  ${YELLOW}!${NC} Ollama is not responding. Attempting to start service..."
    systemctl --user start ollama 2>/dev/null || sudo systemctl start ollama 2>/dev/null || true
    sleep 2
    if curl -s http://localhost:11434/api/version &>/dev/null; then
        echo -e "  ${GREEN}✓${NC} Ollama started successfully"
    else
        echo -e "  ${YELLOW}!${NC} Ollama offline. Backend will run in Graceful Fallback Mode (Deterministic Rules + RAG)."
    fi
fi

# ------------------------------------------------------------------------------
# 4. Check Virtual Environment & Dependencies
# ------------------------------------------------------------------------------
if [ ! -d ".venv" ]; then
    echo -e "\n${BOLD}[*] Setting up Python virtual environment...${NC}"
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

# ------------------------------------------------------------------------------
# 5. Start Backend Service (FastAPI + React UI)
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[3/5] Starting FastAPI Backend & React UI (Port 8000)...${NC}"
nohup .venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
BACKEND_PID=$!
disown $BACKEND_PID 2>/dev/null || true
echo $BACKEND_PID > logs/backend.pid

# Wait up to 10 seconds for backend health
READY=0
for i in {1..10}; do
    if curl -s http://127.0.0.1:8000/api/health | grep -q '"status":"healthy"' &>/dev/null; then
        READY=1
        break
    fi
    sleep 1
done

if [ $READY -eq 1 ]; then
    echo -e "  ${GREEN}✓${NC} Backend healthy (PID: $BACKEND_PID)"
else
    echo -e "  ${YELLOW}!${NC} Backend started (PID: $BACKEND_PID, warming up...)"
fi

# ------------------------------------------------------------------------------
# 6. Start Industrial Telemetry Simulator
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[4/5] Starting Industrial Motor Telemetry Simulator...${NC}"
nohup .venv/bin/python simulator/motor_simulator.py > logs/simulator.log 2>&1 &
SIM_PID=$!
disown $SIM_PID 2>/dev/null || true
echo $SIM_PID > logs/simulator.pid
echo -e "  ${GREEN}✓${NC} Simulator active (PID: $SIM_PID, Target: MOTOR-001)"

# ------------------------------------------------------------------------------
# 7. Start Public Tunnel with Resilient Auto-Fallback
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}[5/5] Launching Public Tunnel...${NC}"
PUBLIC_URL=""

# Try Wormhole with custom subdomain first
nohup wormhole http 8000 --subdomain redsheronin --headless --no-inspect > logs/tunnel.log 2>&1 &
TUNNEL_PID=$!
echo $TUNNEL_PID > logs/tunnel.pid
sleep 2

# Check if Wormhole connected or encountered TLS/network proxy error
if grep -q "tunnel established" logs/tunnel.log 2>/dev/null && kill -0 "$TUNNEL_PID" 2>/dev/null; then
    PUBLIC_URL="https://redsheronin.wormhole.bar"
    disown $TUNNEL_PID 2>/dev/null || true
    echo -e "  ${GREEN}✓${NC} Wormhole tunnel active (Custom Subdomain)"
else
    # Fallback to Cloudflare Tunnel (uses QUIC/UDP, bypasses network firewall proxies)
    kill -9 "$TUNNEL_PID" 2>/dev/null || true
    pkill -f "wormhole http" 2>/dev/null || true
    echo -e "  ${YELLOW}!${NC} Network firewall intercepted TLS. Falling back to Cloudflare QUIC Tunnel..."
    
    nohup ~/.local/bin/cloudflared tunnel --url http://127.0.0.1:8000 > logs/tunnel.log 2>&1 &
    TUNNEL_PID=$!
    disown $TUNNEL_PID 2>/dev/null || true
    echo $TUNNEL_PID > logs/tunnel.pid
    
    for i in {1..12}; do
        PUBLIC_URL=$(grep -oE "https://[a-zA-Z0-9-]+\.trycloudflare\.com" logs/tunnel.log 2>/dev/null | head -n 1 || true)
        if [ -n "$PUBLIC_URL" ]; then
            break
        fi
        sleep 1
    done
    echo -e "  ${GREEN}✓${NC} Cloudflare Tunnel active (Firewall-safe)"
fi

echo "$PUBLIC_URL" > logs/tunnel.url

# ------------------------------------------------------------------------------
# Finished!
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}${GREEN}==============================================================================${NC}"
echo -e "${BOLD}${GREEN} 🎉 ALL SYSTEMS ONLINE AND DEPLOYED!${NC}"
echo -e "${BOLD}${GREEN}==============================================================================${NC}"
echo -e " ${BOLD}🌐 Public Live URL:${NC}       ${CYAN}${PUBLIC_URL}${NC}"
echo -e " ${BOLD}💻 Local React Dashboard:${NC} http://localhost:8000"
echo -e " ${BOLD}📊 Grafana SCADA:${NC}         http://localhost:3000"
echo -e " ${BOLD}📑 OpenAPI / Swagger:${NC}     http://localhost:8000/docs"
echo -e " ${BOLD}🩺 Health API:${NC}            http://localhost:8000/api/health"
echo -e "------------------------------------------------------------------------------"
echo -e " To stop all services cleanly at any time, simply run:"
echo -e "   ${YELLOW}./stop.sh${NC}"
echo -e "${BOLD}${GREEN}==============================================================================${NC}\n"
