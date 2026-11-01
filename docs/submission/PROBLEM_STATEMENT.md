# Project Problem Statement: P_311

## Project Title
**P_311: Knowledge-Driven IoT Fault Diagnosis Assistant for Industrial Rotating Machinery**

---

## 1. The Industrial Maintenance Problem

Electric motors account for over **70% of total electrical energy consumption in heavy manufacturing and industrial plants** (pumps, compressors, conveyers, CNC spindles, cooling towers, and centrifugal fans). In high-throughput industrial environments—such as automotive assembly, chemical processing, pharmaceutical manufacturing, and water distribution—the unscheduled failure of a critical 3-phase induction motor results in immediate line stoppage.

According to industrial reliability benchmarks (EPRI and IEEE motor reliability studies):
- **Unplanned Industrial Downtime Costs**: Large manufacturing facilities experience average downtime costs ranging between **$20,000 to $250,000 per hour** depending on production throughput.
- **Root Failure Distribution in Induction Motors**:
  1. **Bearing Failures (41% – 51%)**: Caused by lubrication breakdown, contaminated grease, raceway fatigue spalling, and mechanical cage degradation.
  2. **Stator Winding Failures (28% – 36%)**: Triggered by thermal insulation aging (IEC Class F/H thermal degradation), sustained electrical overcurrent, cooling blockage, or voltage unbalance.
  3. **Rotor Bar & Shaft Dynamic Faults (8% – 12%)**: Stemming from shaft misalignment, rotor unbalance, dynamic eccentricity, and mechanical soft foot.
  4. **External System Faults (Remaining %)**: Lubrication/cooling circuit depressurization, driven load binding, and sensor circuit disconnects.

When an electric motor suffers mechanical or thermal degradation, early physical warning signals manifest days or weeks before catastrophic seizure. However, modern factory floors struggle to capture and translate these signals into effective, timely maintenance interventions.

---

## 2. Why Traditional Monitoring Systems Are Insufficient

Despite the widespread adoption of Supervisory Control and Data Acquisition (SCADA) systems and basic programmable logic controllers (PLCs), existing plant monitoring exhibits several critical engineering deficiencies:

1. **Reactive Run-to-Failure vs. Static Threshold Beeps**:
   Conventional programmable threshold alarms operate as binary triggers (e.g., sound a horn if vibration velocity exceeds 4.5 mm/s). These alerts provide no contextual explanation of the underlying physical degradation mechanism.
2. **Alarm Fatigue and Nuisance Alarms**:
   In complex plants with thousands of I/O points, transient spikes trigger cascading alarms. Operators are overwhelmed with unprioritized warnings, leading to delayed reactions during genuine failure precursors.
3. **The Diagnostic Knowledge Chasm**:
   A raw alarm state (e.g., `ALARM: CH-04 HIGH`) informs the operator *that* an anomaly exists, but does not identify *why* it occurred or *what* immediate corrective action is required. Junior technicians must manually locate physical equipment binders, cross-reference ISO standards, and hypothesize root causes, inflating Mean Time to Repair (MTTR).
4. **Cloud-Centric Predictive Maintenance Failures**:
   Many modern predictive maintenance platforms require continuous transmission of high-frequency sensor telemetry to external cloud servers (AWS, Azure, Google Cloud). This approach encounters severe hurdles in manufacturing:
   - **Data Privacy & IP Risks**: Factory operational patterns, machine speeds, and output rates represent proprietary trade secrets that plant security policies forbid transmitting outside internal corporate networks.
   - **Bandwidth & Latency Vulnerability**: Continuous multi-channel 1 Hz to 1 kHz telemetry streams congest factory WAN links. In remote facilities or air-gapped plants, cloud connectivity is intermittent or non-existent.
   - **High Subscription Costs**: Recurring cloud ingestion and API inference fees (e.g., proprietary cloud LLM APIs) make scaling across hundreds of motor assets economically prohibitive.

---

## 3. Why Intelligent Fault Diagnosis Is Useful

Intelligent, knowledge-driven fault diagnosis bridges the gap between descriptive data collection and prescriptive engineering action:

- **From Descriptive to Prescriptive**: Rather than simply plotting a rising temperature curve, an intelligent system correlates the temperature rise with vibration amplitude and motor current, diagnoses bearing lubrication starvation, and prescribes the exact grease volume (e.g., 25g polyurea) and safety lockout procedures.
- **Explainability and Auditable Decision Making**: Industrial safety requires explainable AI. Plant managers cannot accept black-box machine learning classifications that cannot cite empirical evidence or standards. A knowledge-driven system must ground its reasoning in verified international standards (**ISO 10816-3**, **IEC 60034-1**) and manufacturer technical manuals.
- **Reduced Mean Time to Repair (MTTR)**: By automatically generating a structured maintenance work order with categorized checklists within seconds of an alarm, plant technicians can execute targeted repairs before catastrophic secondary damage occurs (e.g., preventing a bearing failure from damaging the stator laminations).

---

## 4. Proposed Solution: Project P_311

**P_311** introduces an **edge-ready, explainable AI-assisted IoT Fault Diagnosis system** tailored for 3-phase industrial induction motors. The solution is architected as an air-gapped, self-contained software appliance that integrates real-time telemetry streaming, sub-millisecond deterministic safety trips, semantic Retrieval-Augmented Generation (RAG), and local Large Language Model (LLM) reasoning:

1. **Lightweight Edge Ingestion (MQTT v3.1.1 / v5.0)**:
   Decoupled publish-subscribe message routing using an industrial Eclipse Mosquitto broker running on TCP port `1883`. Accepts 1 Hz JSON telemetry packets containing 7 physical variables: Stator Temperature, Vibration Velocity RMS, 3-Phase Line Current, Rotor Speed, 3-Phase Voltage, Auxiliary Lubrication Pressure, and Operating State.
2. **Sub-Millisecond Deterministic Safety Layer**:
   Critical safety trips and alarms never depend on probabilistic AI models. Telemetry is evaluated in `< 5 ms` by a deterministic rule engine strictly adhering to:
   - **ISO 10816-3**: Mechanical vibration severity grading (Zone A Good, Zone B Acceptable, Zone C Alarm > 4.5 mm/s, Zone D Danger/Trip > 7.1 mm/s).
   - **IEC 60034-1**: Stator thermal insulation ratings (Class F thermal warning at 75°C, alarm at 85°C, and trip at 95°C).
   - **Electrical Overload Limits**: Line current exceeding 125% Full Load Amperes (FLA > 11.25 A) coupled with elevated rotor slip.
   - **Hydraulic/Pneumatic Limits**: Lubrication pressure depletion (< 2.0 bar).
3. **Local Semantic RAG Pipeline**:
   When an anomalous condition triggers, an in-process vector retrieval engine queries pre-indexed technical manuals using the `all-MiniLM-L6-v2` embedding model (384 dimensions) running purely on CPU. In `< 1 ms`, it extracts the top 3 relevant paragraphs directly citing manufacturer troubleshooting procedures.
4. **Edge AI Reasoning via Local Quantized LLM**:
   A locally hosted 1.5B parameter language model (`qwen2.5:1.5b-instruct` in Ollama, quantized to 4-bit Q4_K_M) receives the sensor telemetry snapshot and retrieved manual excerpts. It synthesizes an actionable, structured JSON maintenance report containing likely root causes, diagnostic checklists, immediate safety actions, and document citations.
   - **Graceful Fallback Mode**: If the local LLM daemon is offline, times out, or experiences GPU VRAM pressure, the backend deterministically constructs a complete diagnostic work order using pre-compiled rule templates and direct manual references without interrupting telemetry ingestion.
5. **Dual Visualization Strategy**:
   - **Grafana SCADA (Port 3000)**: Operational time-series dashboard for plant operators, featuring high-density historical queries over PostgreSQL, ISO reference limit lines, and system health status.
   - **React 18 + Vite AI Assistant (Port 8000)**: Interactive engineering interface for maintenance personnel and academic defense, featuring real-time Server-Sent Events (SSE) telemetry sparklines, SVG Digital Twin motor animation, audio alarm annunciator, remote fault injection RPC controls, printable PDF work orders, and an interactive Viva AI tutor chat.

---

## 5. Expected Outcomes & Success Metrics

| Dimension | Target Metric | Engineering Justification |
| :--- | :--- | :--- |
| **Fault Detection Latency** | **< 5 ms** | Realized via deterministic threshold evaluation in Python without network hops or LLM delays. |
| **Detection Accuracy** | **> 98%** | Validated on a 4,000-sample benchmark dataset across 7 operational modes with an overall accuracy of **99.38%** (Macro F1: 0.9931). |
| **RAG Retrieval Precision** | **MRR = 1.0, Hit@1 = 100%** | Demonstrated across 7 fault domain queries against 34 indexed knowledge chunks with an average top-1 similarity score of 0.6499. |
| **Local Memory Footprint** | **< 1.5 GB VRAM, < 1.2 GB RAM** | Entire stack (PostgreSQL, Mosquitto, Grafana, FastAPI, Ollama, Simulator) fits comfortably within standard edge hardware (4 GB VRAM GPU, 16 GB RAM). |
| **Cloud Dependency** | **0% (Air-Gapped)** | Zero API calls to external cloud vendors; zero recurring subscription costs; zero proprietary data leakage. |
| **Diagnostic Output** | **Structured Work Order** | Generates an auditable, printable HTML/PDF work order complete with technician signatures, ISO reference limits, and safety Lockout/Tagout (LOTO) procedures. |
