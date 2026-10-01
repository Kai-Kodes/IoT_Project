# System Architecture Specification

## 1. Overview
The **P_311 Knowledge-Driven IoT Fault Diagnosis Assistant** is an end-to-end, edge-ready industrial monitoring system. It unites high-frequency IoT sensor telemetry, asynchronous MQTT communication, deterministic rule-based fault detection, local Retrieval-Augmented Generation (RAG), and a local instruction-tuned Large Language Model (LLM) to deliver real-time, explainable diagnostic guidance.

## 2. High-Level Data Flow Architecture

```
                       ┌────────────────────────┐
                       │   Industrial Machine   │
                       │   Motor Simulator      │
                       └───────────┬────────────┘
                                   │ MQTT (1 Hz JSON)
                                   ▼
                       ┌────────────────────────┐
                       │   Eclipse Mosquitto    │
                       │   MQTT Broker (:1883)  │
                       └───────────┬────────────┘
                                   │ Subscribe (p311/machine/+/telemetry)
                                   ▼
                       ┌────────────────────────┐
                       │   FastAPI Core Backend │
                       │                        │
                       │  - Pydantic Validator  │
                       │  - SQLite (WAL Mode)   │
                       │  - Fault Rule Detector │
                       └───────────┬────────────┘
                                   │ Fault Trigger Event
                                   ▼
                       ┌────────────────────────┐
                       │   RAG Semantic Pipeline│
                       │  - MiniLM-L6-v2 (CPU)  │
                       │  - Cosine Vector Store │
                       └───────────┬────────────┘
                                   │ Context + Sensor Readings
                                   ▼
                       ┌────────────────────────┐
                       │   Local Ollama LLM     │
                       │   qwen2.5:1.5b-instruct│
                       │  (Fallback Resilient)  │
                       └───────────┬────────────┘
                                   │ Structured JSON Diagnosis
                                   ▼
                       ┌────────────────────────┐
                       │   React Web Dashboard  │
                       │  - Live SSE Telemetry  │
                       │  - Recharts Visualizer │
                       │  - Fault Checklist     │
                       └────────────────────────┘
```

## 3. Component Breakdown

### A. Industrial Machine Simulator (`simulator/motor_simulator.py`)
- Simulates an 11 kW, 400V 3-phase squirrel cage induction motor operating under realistic thermal, electrical, and mechanical slip dynamics.
- Emits telemetry every 1.0s to `p311/machine/MOTOR-001/telemetry`.
- Implements 6 deterministic fault injection modes:
  1. `bearing_degradation` (vibration surge to 8.4 mm/s, bearing temperature climb to 89°C, current rise).
  2. `motor_overheating` (cooling fan blockage; temperature exceeds 104°C).
  3. `motor_overload` (mechanical binding; current jumps to 15.8A, rotor slip drops RPM to 1395).
  4. `excessive_vibration` (unbalance/misalignment; vibration spikes to 11.2 mm/s).
  5. `low_pressure` (auxiliary lube pressure collapses below 2.0 bar).
  6. `sensor_anomaly` (open-circuit thermocouple failure spikes reading to 999°C).

### B. MQTT Messaging Backbone (`backend/app/mqtt/consumer.py`)
- Standard Eclipse Mosquitto broker running on port 1883.
- Python `paho-mqtt` client operating within an asynchronous background thread.
- Auto-reconnection logic and Last Will and Testament (LWT) for disconnected node awareness.

### C. Deterministic Rule-Based Fault Detector (`backend/app/detection/fault_detector.py`)
- Grounded in industrial ISO 10816-3 vibration limits and Class F motor insulation thermal curves.
- **Why not use an LLM directly for detection?** LLMs are probabilistic text predictors prone to hallucinations, non-determinism, and latency spikes. Industrial safety standards demand deterministic, sub-millisecond, auditable threshold evaluation.

### D. Local RAG Pipeline (`backend/app/rag/knowledge_indexer.py`)
- Ingests 7 technical equipment manuals from `knowledge_base/`.
- Extracts semantic chunks (300-500 characters) preserving document title and section headings.
- Encodes queries and chunks into 384-dimensional unit vectors using `sentence-transformers/all-MiniLM-L6-v2` executed on the CPU (80 MB RAM footprint).
- Computes exact cosine similarities and retrieves top-3 relevant procedure excerpts in < 1 ms.

### E. Local LLM & Resilient Diagnosis Engine (`backend/app/diagnosis/`)
- Interfaces with local Ollama running `qwen2.5:1.5b-instruct` (1.35 GB VRAM footprint, fits comfortably on 4GB RTX 2050).
- Assembles a structured prompt containing:
  - `[MEASURED SENSOR EVIDENCE]` (ground truth telemetry).
  - `[TRIGGERED RULES]` (exact threshold violations).
  - `[RETRIEVED TECHNICAL KNOWLEDGE]` (manual excerpts).
- Requests strict JSON schema response.
- **Resilience Guarantee**: If Ollama is offline or times out (> 25s), the engine automatically executes a deterministic fallback generator that produces the diagnostic report directly from the triggered rules and manuals.

### F. Web Monitoring Dashboard (`frontend/`)
- React 18 single-page application built with Vite and Tailwind CSS.
- Real-time streaming via Server-Sent Events (SSE) from `/api/telemetry/stream`.
- Visualizations built with Recharts, featuring ISO threshold reference lines.
