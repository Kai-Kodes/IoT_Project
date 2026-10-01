#!/usr/bin/env bash
# ==============================================================================
# 🛑 P_311 Master "Boss" Stop Script
# Shuts down EVERYTHING cleanly: Tunnels, Simulators, Backend & Docker Containers
# ==============================================================================
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}${YELLOW}==============================================================================${NC}"
echo -e "${BOLD}${YELLOW} 🛑 Stopping P_311: Full Industrial IoT Stack & Public Tunnels${NC}"
echo -e "${BOLD}${YELLOW}==============================================================================${NC}"

# 1. Stop Public Tunnels
echo -e "\n${BOLD}[1/4] Stopping Public Tunnels...${NC}"
if [ -f logs/tunnel.pid ]; then
    PID=$(cat logs/tunnel.pid)
    kill -15 "$PID" 2>/dev/null || kill -9 "$PID" 2>/dev/null || true
    rm -f logs/tunnel.pid
    echo -e "  ${GREEN}✓${NC} Tunnel stopped (PID: $PID)"
fi
pkill -9 -f "wormhole" 2>/dev/null || true
pkill -9 -f "cloudflared" 2>/dev/null || true
echo -e "  ${GREEN}✓${NC} All public tunnels disconnected"

# 2. Stop Industrial Motor Simulator
echo -e "\n${BOLD}[2/4] Stopping Industrial Motor Telemetry Simulator...${NC}"
if [ -f logs/simulator.pid ]; then
    PID=$(cat logs/simulator.pid)
    kill -15 "$PID" 2>/dev/null || kill -9 "$PID" 2>/dev/null || true
    rm -f logs/simulator.pid
    echo -e "  ${GREEN}✓${NC} Simulator stopped (PID: $PID)"
fi
pkill -9 -f "simulator.motor_simulator" 2>/dev/null || true
echo -e "  ${GREEN}✓${NC} Simulator stopped"

# 3. Stop Backend Service
echo -e "\n${BOLD}[3/4] Stopping FastAPI Backend & React Server...${NC}"
if [ -f logs/backend.pid ]; then
    PID=$(cat logs/backend.pid)
    kill -15 "$PID" 2>/dev/null || kill -9 "$PID" 2>/dev/null || true
    rm -f logs/backend.pid
    echo -e "  ${GREEN}✓${NC} Backend stopped (PID: $PID)"
fi
pkill -9 -f "backend.app.main:app" 2>/dev/null || true
echo -e "  ${GREEN}✓${NC} Backend stopped"

# 4. Stop Docker Compose Containers
echo -e "\n${BOLD}[4/4] Stopping Docker Infrastructure (PostgreSQL, Grafana, Mosquitto)...${NC}"
if command -v docker &>/dev/null && docker compose ps -q &>/dev/null; then
    docker compose down
    echo -e "  ${GREEN}✓${NC} Docker containers stopped"
else
    echo -e "  ${GREEN}✓${NC} No active docker compose containers"
fi

# Clean up stray PID files
rm -f logs/*.pid 2>/dev/null || true

echo -e "\n${BOLD}${GREEN}==============================================================================${NC}"
echo -e "${BOLD}${GREEN} [✓] ALL SERVICES AND TUNNELS SHUT DOWN SUCCESSFULLY!${NC}"
echo -e "${BOLD}${GREEN}==============================================================================${NC}\n"
