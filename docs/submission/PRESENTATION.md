# Presentation Slide Deck Outline (Viva Voce & Final Defense)
## Project P_311: Knowledge-Driven IoT Fault Diagnosis Assistant

---

### Slide 1: Title Slide
- **Title**: P_311: Knowledge-Driven IoT Fault Diagnosis Assistant for Industrial Rotating Machinery
- **Subtitle**: An Edge-Native, Explainable AI Architecture Integrating ISO 10816-3 Deterministic Detection, Local Semantic RAG, and Quantized LLMs
- **Presented by**: `[Student Name 1]` & `[Student Name 2]` (Reg. Nos: `[Reg No 1]`, `[Reg No 2]`)
- **Under Guidance of**: `[Guide Name]`, `[Department Name]`
- **Institution**: `[Name of College / University]`

---

### Slide 2: Industrial Context & The Maintenance Problem
- **Electric Motor Criticality**: Induction motors consume $> 70\%$ of industrial electrical energy; drive pumps, fans, compressors, conveyors.
- **Downtime Costs**: Unplanned industrial outages cost between **$20,000 to $250,000 per hour**.
- **Root Failure Distribution**:
  - Bearing Failures: **41% – 51%** (lubrication breakdown, spalling).
  - Stator Winding Failures: **28% – 36%** (thermal aging, overcurrent).
  - Mechanical Rotor/Shaft Faults: **8% – 12%** (unbalance, misalignment).
- **Core Challenge**: Physical degradation produces early warning signals, but factory floors lack tools to translate signals into actionable repairs.

---

### Slide 3: Limitations of Traditional Monitoring
- **Binary SCADA Thresholds**: Simple alarms ("CH-02 HIGH") trigger beeps without explaining *why* the fault occurred or *how* to fix it.
- **Alarm Fatigue**: Operators are inundated with hundreds of unprioritized alarms, leading to delayed reactions or muted horns.
- **The Knowledge Chasm**: Manuals exist in static PDF binders; junior technicians must guess root causes under emergency conditions.
- **Cloud Predictive Maintenance Bottlenecks**:
  - Exposes proprietary operational secrets to external clouds.
  - Requires continuous high-bandwidth internet (unsuitable for air-gapped plants).
  - Incurs high recurring cloud subscription fees.

---

### Slide 4: Project Objectives
1. **High-Speed Decoupled Ingestion**: 1 Hz telemetry streaming over MQTT (Mosquitto port 1883).
2. **Instant Deterministic Safety Tripping**: Sub-millisecond evaluation (< 5 ms) adhering strictly to **ISO 10816-3** and **IEC 60034-1** standards.
3. **Local Semantic RAG**: In-process vector retrieval (< 1 ms) over 7 plant equipment manuals using `all-MiniLM-L6-v2` embeddings on CPU.
4. **Edge AI Diagnostic Work Orders**: Local 1.5B LLM (`qwen2.5:1.5b` in Ollama) generating structured JSON maintenance reports with zero data leakage.
5. **Dual Visualization**: Operational time-series SCADA (Grafana 3000) alongside an interactive engineering dashboard (React 8000).

---

### Slide 5: End-to-End System Architecture
- *(Display Architecture Diagram: Telemetry $\rightarrow$ MQTT $\rightarrow$ FastAPI $\rightarrow$ ISO Detector $\rightarrow$ RAG Vector Store $\rightarrow$ Local Ollama $\rightarrow$ PostgreSQL/SQLite $\rightarrow$ Grafana & React UI)*
- **Strict Separation of Concerns**: Safety limits execute in $< 1\text{ ms}$; qualitative LLM diagnosis executes asynchronously without blocking telemetry.
- **100% Air-Gapped Local Operation**: Zero cloud calls; zero external internet requirements.

---

### Slide 6: Technology Stack & Engineering Choices
- **Messaging**: Eclipse Mosquitto MQTT v3.1.1 / v5.0 (2-byte header, QoS 1, Last Will and Testament).
- **Backend**: FastAPI (Python 3.13), asyncpg connection pool (2–10 connections), Pydantic validation.
- **Database**: Dual storage pattern — PostgreSQL 16 Alpine (JSONB schema) with automatic local SQLite fallback.
- **RAG & Embeddings**: SentenceTransformers `all-MiniLM-L6-v2` (384 dimensions, CPU cosine search in 0.62 ms).
- **Local LLM**: Ollama running `qwen2.5:1.5b` (Q4_K_M 4-bit quantization, ~1.35 GB VRAM).
- **Frontend**: React 18, Vite, Tailwind CSS, Recharts, Server-Sent Events (SSE).
- **SCADA**: Grafana OSS 11.2.0 (declaratively provisioned).

---

### Slide 7: MQTT Telemetry & Digital Twin Simulator
- **Simulator Physics**: Models continuous differential state equations of an 11 kW motor with realistic Gaussian sensor noise and thermal inertia lag curves.
- **7 Monitored Physical Channels**:
  1. Stator / Bearing Temperature (°C)
  2. Vibration Velocity RMS (mm/s)
  3. Stator Line Current (A)
  4. Shaft Speed (RPM)
  5. 3-Phase Voltage (V)
  6. Auxiliary Lubrication Pressure (bar)
  7. Operating State (running, warning, critical, stopped)
- **MQTT Topic Structure**: `p311/machine/<id>/telemetry`, `status`, `command`, `fault`.

---

### Slide 8: Deterministic Safety Detection (No Probabilistic Safety)
- **Why LLMs Must Never Directly Trip Machines**:
  - LLMs have multi-second response latency (1.5–3.5 s).
  - LLMs are probabilistic generators prone to non-deterministic outputs and hallucinations.
- **ISO 10816-3 Vibration Severity Envelopes**:
  - Zone A/B (Normal): $< 2.8\text{ mm/s}$
  - Zone C (Warning): $> 4.5\text{ mm/s}$
  - Zone D (Immediate Trip): $\ge 7.1\text{ mm/s}$
- **IEC 60034-1 Stator Thermal Limits**: Warning at 75°C, Alarm at 85°C, Trip at 95°C.
- **Compound Multi-Sensor Rules**: Evaluates combinations (e.g., Bearing Degradation = High Vibration + High Temperature).

---

### Slide 9: Local RAG Pipeline & Semantic Knowledge Retrieval
- **Curated Corpus**: 7 engineering manuals covering bearing wear, motor maintenance, vibration diagnostics, electrical overload, lubrication loss, and preventive checklists.
- **Chunking & Indexing**: 34 discrete semantic chunks indexed by section into `chunks.json` and `embeddings.npy`.
- **Search Execution**: Cosine similarity dot product on CPU executed in **0.62 ms**.
- **Empirical RAG Benchmark**:
  - **Mean Reciprocal Rank (MRR)**: **1.000** (Perfect rank-1 retrieval across all test queries).
  - **Hit Rate @ 1**: **100.0%**
  - **Hit Rate @ 3**: **100.0%**
  - **Average Top-1 Similarity**: **0.6499**

---

### Slide 10: Local LLM Synthesis & Guaranteed Fallback Resilience
- **In-Process Prompt Construction**: Merges real-time telemetry, triggered ISO rules, and retrieved manual excerpts into an enforced JSON schema.
- **Structured Work Order Output**:
  - Likely Root Causes
  - Diagnostic Checklists
  - Corrective Actions
  - Mandatory Lockout/Tagout (LOTO) Safety Rules
  - Manual Citations with Similarity Scores
- **Deterministic Fallback Engine**: If Ollama crashes, times out (> 45s), or GPU VRAM is full, the backend deterministically builds a standards-compliant report in $< 2\text{ ms}$. Zero telemetry dropped; zero crashes.

---

### Slide 11: Real-Time Visualization & Digital Twin
- **React 18 Dashboard**:
  - Real-time 1 Hz telemetry cards with 50-sample rolling sparklines.
  - SVG Digital Twin motor with real-time rotor RPM rotation and thermal color shift.
  - Web Audio API industrial alarm annunciator with mute toggle.
  - One-click fault injection control panel (7 operational modes).
  - Printable HTML/PDF industrial maintenance work order generator.
  - Interactive Viva AI tutor chat for student/operator Q&A.
- **Grafana SCADA**:
  - High-density operational time-series graphs with ISO limit threshold lines.
  - Direct PostgreSQL queries; anonymous viewer access enabled.

---

### Slide 12: Testing Strategy & Empirical Results
- **Automated Pytest Suite**: 25 automated tests covering validation, detection rules, RAG, LLM fallback, MQTT, DB persistence, and REST APIs (**100% Pass Rate in 14.68s**).
- **Benchmark Evaluation (4,000 Industrial Samples)**:
  - **Overall Classification Accuracy**: **99.38%**
  - **Macro Precision**: **0.9902**
  - **Macro Recall**: **0.9961**
  - **Macro F1-Score**: **0.9931**
- **Latency Verification**:
  - Rule Detection: **0.84 ms** (Budget: < 5 ms)
  - RAG Retrieval: **0.62 ms** (Budget: < 5 ms)
  - LLM Inference: **2.18 s** on NVIDIA RTX 2050 (Budget: < 5 s)

---

### Slide 13: Hardware Footprint & BOM Distinction
- **Actual Workstation Footprint**:
  - RAM Consumption: **$< 1.2\text{ GB}$** (Stack total).
  - GPU VRAM: **~1.35 GB** on RTX 2050 (Leaves $> 2.5\text{ GB}$ for OS).
  - Actual Cost: **₹0 / $0** (Leveraged existing student laptop and open-source software).
- **Prospective Physical BOM (Honest Disclosure)**:
  - No physical motors were damaged in the lab; all tests used the software digital twin.
  - Benchtop physical deployment estimated at **₹6,250 (~$75)** using ESP32-S3, ADXL345, Pt100, and SCT-013 current clamp.

---

### Slide 14: Limitations & Future Scope
- **Current Limitations**:
  - Single primary monitored asset (`MOTOR-001`).
  - English-only technical manual corpus.
  - Physical motor testing pending industrial partner collaboration.
- **Future Enhancements**:
  - Port telemetry ingestion to physical ESP32-S3 microcontroller nodes.
  - Motor Current Signature Analysis (MCSA) via Fast Fourier Transform (FFT) for broken rotor bar detection.
  - Multi-asset fleet management across factory cells.

---

### Slide 15: Conclusion & Summary
- **Bridging the Industrial IoT Gap**: P_311 successfully moves beyond raw data collection to actionable, explainable prescriptive maintenance.
- **Proven Engineering Highlights**:
  - Sub-millisecond deterministic safety tripping adhering to ISO 10816-3.
  - Zero cloud dependency, zero data leaks, and zero recurring subscription fees.
  - 99.38% fault classification accuracy and 1.0 MRR RAG retrieval.
  - Dual SCADA and AI Digital Twin visualization.
- **Thank you! Questions & Answers (Q&A)**.
