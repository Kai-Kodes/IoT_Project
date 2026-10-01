#!/usr/bin/env bash
# ============================================================
# P_311: Stop Public Tunnel
# ============================================================
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "Stopping Wormhole tunnel..."

if [ -f logs/tunnel.pid ]; then
    PID=$(cat logs/tunnel.pid)
    kill -15 "$PID" 2>/dev/null || kill -9 "$PID" 2>/dev/null || true
    rm -f logs/tunnel.pid
    echo "  [✓] Tunnel stopped (PID: $PID)"
fi

pkill -f "wormhole http" 2>/dev/null || true
pkill -f "cloudflared tunnel" 2>/dev/null || true

echo "All public tunnels stopped."
