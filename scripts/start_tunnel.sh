#!/usr/bin/env bash
# ============================================================
# P_311: Start Public Tunnel (wormhole.bar)
# ============================================================
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
mkdir -p logs

SUBDOMAIN="${1:-redsheronin}"
PORT="${2:-8000}"

echo "Checking for existing tunnel processes..."
if [ -f logs/tunnel.pid ]; then
    PID=$(cat logs/tunnel.pid)
    kill -15 "$PID" 2>/dev/null || kill -9 "$PID" 2>/dev/null || true
    rm -f logs/tunnel.pid
fi
pkill -f "wormhole http" 2>/dev/null || true

echo "Starting Wormhole tunnel (https://${SUBDOMAIN}.wormhole.bar -> http://localhost:${PORT})..."
nohup wormhole http "${PORT}" --subdomain "${SUBDOMAIN}" --headless --no-inspect > logs/tunnel.log 2>&1 &
TUNNEL_PID=$!
disown $TUNNEL_PID 2>/dev/null || true
echo $TUNNEL_PID > logs/tunnel.pid

sleep 3

if kill -0 "$TUNNEL_PID" 2>/dev/null; then
    echo "  [✓] Tunnel active (PID: $TUNNEL_PID)"
    echo "  [✓] Live URL: https://${SUBDOMAIN}.wormhole.bar"
    echo "  [✓] Logs:     logs/tunnel.log"
else
    echo "  [✗] Tunnel failed to start. Log output:"
    cat logs/tunnel.log
    exit 1
fi
