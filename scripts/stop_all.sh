#!/usr/bin/env bash
# ============================================================
# P_311: Stop All Services Script
# ============================================================
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "Stopping P_311 processes..."

if [ -f logs/simulator.pid ]; then
    PID=$(cat logs/simulator.pid)
    kill -15 "$PID" 2>/dev/null || kill -9 "$PID" 2>/dev/null || true
    rm -f logs/simulator.pid
    echo "  [✓] Simulator stopped (PID: $PID)"
fi

if [ -f logs/backend.pid ]; then
    PID=$(cat logs/backend.pid)
    kill -15 "$PID" 2>/dev/null || kill -9 "$PID" 2>/dev/null || true
    rm -f logs/backend.pid
    echo "  [✓] Backend stopped (PID: $PID)"
fi

# Fallback pattern kill for any orphaned instances
pkill -f "simulator.motor_simulator" 2>/dev/null || true
pkill -f "uvicorn backend.app.main:app" 2>/dev/null || true

echo "All P_311 services stopped."
