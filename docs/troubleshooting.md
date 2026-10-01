# Troubleshooting & Common Issues Guide

## 1. Port 1883 Already in Use
### Symptom
`OSError: [Errno 98] Address already in use` when starting Mosquitto.
### Root Cause
Mosquitto is likely already running as a systemd service in Debian.
### Resolution
Check active services:
```bash
sudo systemctl status mosquitto
```
If already running, you do not need to start another instance—the backend and simulator will connect to `localhost:1883` automatically.

---

## 2. Local Ollama LLM Offline / Fallback Active
### Symptom
Dashboard displays badge: `LLM Fallback Active`.
### Root Cause
Ollama daemon is either stopped or the model is not yet pulled.
### Resolution
1. Verify Ollama status:
   ```bash
   ollama list
   ```
2. Pull the required lightweight model if missing:
   ```bash
   ollama pull qwen2.5:1.5b
   ```
3. Test inference manually:
   ```bash
   ollama run qwen2.5:1.5b "Hello"
   ```
4. Note that P_311 is designed to operate 100% reliably in Fallback Mode even if Ollama is never installed.

---

## 3. High VRAM Usage or Laptop Fan Noise
### Symptom
GPU memory approaching 4 GB or system thermal throttling.
### Root Cause
An unnecessarily large model (such as a 7B or 14B model) was selected.
### Resolution
Ensure `.env` specifies the recommended 1.5B model:
```bash
LLM_MODEL=qwen2.5:1.5b
LLM_NUM_CTX=2048
```
Restart backend using `./scripts/stop_all.sh && ./scripts/start_all.sh`.

---

## 4. Telemetry Stream Disconnected in Dashboard
### Symptom
Dashboard status indicates `Connecting...` or telemetry stops updating.
### Root Cause
The simulator process may have terminated or backend was restarted.
### Resolution
Restart all background services cleanly:
```bash
make stop
make run
```
Check log files for exceptions:
```bash
tail -n 25 logs/backend.log
tail -n 25 logs/simulator.log
```
