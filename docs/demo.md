# Official 13-Step Demonstration Guide

Follow this guide to execute the full evaluation demonstration during a viva or project presentation.

---

## Preparation (Terminal 1)
Start the complete application stack:
```bash
make run
```
Or natively:
```bash
./scripts/start_all.sh
```
Verify the dashboard is accessible at:
👉 **`http://localhost:8000`**

---

## Method A: Visual Interactive Browser Demo

### STEP 1: Launch & System Verification
- Open `http://localhost:8000` in your web browser.
- Observe top status badges:
  - **MQTT Connected** (Green)
  - **SQLite WAL** (Blue)
  - **Ollama qwen2.5:1.5b** (Purple)
  - **Live Stream** (Pulsing blue indicator)

### STEP 2 & 3: Normal Operation Baseline
- The machine header displays **HEALTHY (System Operating Normally)**.
- Navigate to the **Live Telemetry** tab.
- Observe stable baseline readings:
  - Temperature: ~51–53°C (well below 75°C warning line)
  - Vibration: ~1.4–1.7 mm/s (inside ISO Zone A/B)
  - Current: ~8.8 A (within 9.0 A rated FLA)
  - RPM: ~1485 RPM

### STEP 4: Inject Bearing Degradation Fault
- Navigate to the **Fault Simulator** tab.
- Click **Inject Bearing Degradation**.

### STEP 5: Observe Telemetry Shift
- Return to **Live Telemetry** tab.
- Observe the synchronized physical reaction:
  - Vibration spikes rapidly across the ISO Zone C (4.5 mm/s) and Zone D (7.1 mm/s) warning lines to ~8.4 mm/s.
  - Temperature begins a gradual thermal climb past 75°C up to ~89°C.
  - Motor current rises slightly to ~11.8 A due to elevated rolling friction.

### STEP 6: Deterministic Fault Detection
- Look at the top banner: it immediately turns **RED** with **CRITICAL FAULT: BEARING DEGRADATION**.
- Triggered rules appear: `HIGH_VIBRATION_ZONE_D_TRIP`, `HIGH_TEMPERATURE_FRICTION`.

### STEP 7, 8 & 9: RAG Retrieval & AI Diagnosis
- Navigate to the **AI Diagnosis & Evidence** tab.
- Observe the generated diagnosis card:
  - **Title**: *Bearing Mechanical Degradation & Thermal Friction* (or LLM generated title).
  - **Diagnostic Confidence**: 88–94%.
  - **Measured Evidence**: Clearly tabulates actual sensor numbers vs normal baseline.

### STEP 10: Recommended Diagnostic Checks
- Review the maintenance procedures list:
  - *Inspect grease sample from drain port for darkening or metal particles.*
  - *Perform shock-pulse or high-frequency demodulation analysis.*
  - *Rotate shaft by hand (under LOTO) to check for notchiness.*
- Click the interactive checkboxes to demonstrate technician workflow tracking.

### STEP 11: Review RAG Knowledge Sources
- Scroll to **Retrieved Technical Knowledge Sources (RAG Citations)**:
  - Observe citations to *Rolling Element Bearing Troubleshooting Guide* and *ISO 10816-3 Vibration Standards*.

### STEP 12: Reset Machine
- Click the **Reset Machine to Normal** button (or navigate to Simulator tab and click Reset).

### STEP 13: System Returns to Normal
- The simulator transitions sensor values back to nominal baseline.
- Banner turns green: **HEALTHY**.
- Telemetry curves settle back to normal operational bands.

---

## Method B: Automated Single-Command Terminal Demo
You can run the entire 13-step sequence automatically from the command line:
```bash
make demo
```
or:
```bash
.venv/bin/python scripts/run_demo.py
```
This logs each step with timestamps and verifies telemetry assertions in real time.
