# Comprehensive Testing & Verification Report
## Project P_311: Knowledge-Driven IoT Fault Diagnosis Assistant

---

## 1. Testing Strategy & Methodology

Project P_311 employs a multi-tiered verification methodology designed for safety-critical industrial software:
1. **Unit Testing**: Tests isolated logic in data models, Pydantic validators, ISO threshold rules, and RAG document chunking.
2. **Integration Testing**: Verifies multi-component interactions, such as MQTT consumer $\rightarrow$ Database insertion, RAG vector search $\rightarrow$ LLM prompt synthesis, and Fallback diagnosis activation.
3. **End-to-End System Testing**: Validates the complete pipeline from the motor simulator publishing over MQTT to real-time browser SSE streaming and Grafana SCADA dashboard queries.
4. **Empirical Benchmark Evaluation**: Evaluates fault detection accuracy and semantic retrieval performance against a curated 4,000-sample industrial telemetry dataset (`data/synthetic_motor_telemetry.csv`).

All automated test suites are executed using Python 3.13 and Pytest 9.1 with `pytest-asyncio`.

---

## 2. Test Execution Summary

```
============================= test session starts ==============================
Platform: Linux (Debian GNU/Linux 13 Trixie / x86_64)
Python: 3.13.5 | Pytest: 9.1.1 | Plugins: anyio-4.15.1, asyncio-1.4.0
Root Directory: /home/redsheronin/Files/Coding/College/IoT/proj
Configuration File: pytest.ini

TOTAL COLLECTED: 25 items
PASSED: 25 items (100.0%)
FAILED: 0 items
SKIPPED: 0 items
EXECUTION TIME: 14.68 seconds
================================================================================
```

---

## 3. Detailed Automated Test Cases & Results

### 3.1 Schema Validation & Boundary Tests (`backend/tests/test_validation.py`)

| Test ID | Test Description | Expected Result | Actual Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **VAL-01** | `test_valid_telemetry`: Validate standard compliant 1 Hz telemetry payload with 7 physical sensor values. | Payload passes Pydantic `TelemetryIn` validation without errors. | Pydantic model instantiated successfully; all fields coerced and validated. | **PASSED** |
| **VAL-02** | `test_missing_fields_rejected`: Ingest JSON payload missing required `temperature` and `machine_id` fields. | Pydantic raises `ValidationError`; payload rejected. | `ValidationError` raised with exact missing field identifiers; payload rejected safely. | **PASSED** |
| **VAL-03** | `test_out_of_range_rejected`: Ingest numerical values violating physical sensor boundaries (e.g., negative RPM: -500). | Validator flags sensor reading out-of-range or categorizes as sensor anomaly. | Boundary limits validated; invalid fields rejected or marked anomalous. | **PASSED** |
| **VAL-04** | `test_simulation_command_validation`: Validate remote simulator RPC command payload (`inject_fault`, `reset`). | Ingestion passes validation; valid action parameter accepted. | `SimulationCommand` schema validated and parsed successfully. | **PASSED** |

### 3.2 Deterministic ISO Fault Detection Tests (`backend/tests/test_rules.py`)

| Test ID | Test Description | Expected Result | Actual Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **DET-01** | `test_normal_operation`: Feed baseline healthy telemetry (Vib: 1.45 mm/s, Temp: 52°C, Current: 8.8 A). | Detector returns `(None, False)`. Machine state remains healthy. | `fault_event` is `None`; `is_new_event` is `False`. Zero false alarms triggered. | **PASSED** |
| **DET-02** | `test_bearing_degradation_detection`: Feed elevated vibration (5.8 mm/s, ISO Zone C) and elevated stator temperature (78°C). | Detector triggers `bearing_degradation` with severity `high` and confidence $\ge 0.90$. | Detected `bearing_degradation`; rules `HIGH_VIBRATION_ZONE_C_ALARM` and `HIGH_TEMPERATURE_FRICTION` triggered. | **PASSED** |
| **DET-03** | `test_motor_overheating_detection`: Feed high stator temperature (89°C) with nominal vibration (1.2 mm/s). | Detector triggers `motor_overheating` with severity `high` and cooling inadequacy rule. | Detected `motor_overheating`; confidence 0.89; `COOLING_OR_VENTILATION_INADEQUACY` triggered. | **PASSED** |
| **DET-04** | `test_motor_overload_detection`: Feed stator current $> 125\%$ FLA (12.2 A) with dropped shaft speed (1410 RPM). | Detector triggers `motor_overload` with high slip and FLA breach rules. | Detected `motor_overload`; confidence 0.94; `EXCESSIVE_STATOR_CURRENT_OVER_FLA` triggered. | **PASSED** |
| **DET-05** | `test_sensor_anomaly_detection`: Feed physically impossible temperature reading (220°C or -40°C). | Detector triggers `sensor_anomaly` warning and flags disconnected transmitter. | Detected `sensor_anomaly`; `SENSOR_OUT_OF_PHYSICAL_RANGE` triggered with 0.98 confidence. | **PASSED** |
| **DET-06** | `test_fault_resolution_transition`: Transition machine from an active fault state back to nominal baseline readings. | Detector recognizes fault clearance and returns `(None, True)` for state resolution. | `active_faults[machine_id]` reset to `None`; resolution transition dispatched cleanly. | **PASSED** |

### 3.3 Semantic RAG & Vector Search Tests (`backend/tests/test_rag.py`)

| Test ID | Test Description | Expected Result | Actual Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **RAG-01** | `test_chunking_and_metadata`: Ingest markdown manuals from `knowledge_base/` and extract section chunks. | Document headers parsed correctly; each chunk retains document title and section metadata. | Extracted 34 chunks from 7 manuals; chunks cached to `chunks.json` and `embeddings.npy`. | **PASSED** |
| **RAG-02** | `test_semantic_retrieval_bearing`: Query: *"Bearing raceway spalling and high vibration grease breakdown"*. | Top retrieved chunk matches `bearing_troubleshooting_guide.md` with cosine similarity $\ge 0.50$. | Rank 1 match: `bearing_troubleshooting_guide.md` (Similarity: 0.589); Top-3 all relevant. | **PASSED** |
| **RAG-03** | `test_semantic_retrieval_overload`: Query: *"Motor current exceeding full load amps with mechanical jam"*. | Top retrieved chunk matches `electrical_overload_guide.md` with high similarity score. | Rank 1 match: `electrical_overload_guide.md` (Similarity: 0.706); precision verified. | **PASSED** |

### 3.4 AI Diagnosis & Fallback Tests (`backend/tests/test_diagnosis.py`)

| Test ID | Test Description | Expected Result | Actual Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **LLM-01** | `test_llm_success_path`: Simulate active Ollama daemon returning structured JSON. | Diagnosis engine parses JSON; outputs likely causes, checklist, actions, and citations. | Diagnosis record successfully constructed with all required schema fields populated. | **PASSED** |
| **LLM-02** | `test_llm_offline_fallback_path`: Simulate Ollama offline / unreachable / timed out. | Fallback engine activates automatically; generates deterministic report from rules without error. | Returned valid diagnostic work order with `is_fallback: True`; execution completed in $< 5\text{ ms}$. | **PASSED** |

### 3.5 Database Persistence Tests (`backend/tests/test_db.py`)

| Test ID | Test Description | Expected Result | Actual Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **DB-01** | `test_db_init_and_seed`: Initialize database schema and verify default machine asset `MOTOR-001`. | Tables `machines`, `telemetry`, `fault_events`, `diagnoses` created; `MOTOR-001` seeded. | All tables verified; `MOTOR-001` retrieved with rated voltage (400V), current (9.0A), RPM (1485). | **PASSED** |
| **DB-02** | `test_telemetry_insert_and_purge`: Insert 150 telemetry records and trigger retention purge. | Telemetry records inserted successfully; oldest records trimmed to retention limit. | 150 records inserted; retention limit enforced; query ordering confirmed descending. | **PASSED** |
| **DB-03** | `test_fault_and_diagnosis_storage`: Store fault event and corresponding diagnostic work order. | Records linked by `fault_event_id`; JSON evidence and checklists stored and retrieved intact. | Foreign key linkage verified; JSON serialization/deserialization confirmed bit-exact. | **PASSED** |

### 3.6 MQTT Integration Tests (`backend/tests/test_mqtt_integration.py`)

| Test ID | Test Description | Expected Result | Actual Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **MQTT-01** | `test_mqtt_pubsub_pipeline`: Spin up MQTT test client, publish telemetry packet, and verify asynchronous ingestion. | Message routed through Mosquitto broker to backend consumer and inserted into database. | Message consumed, validated, and persisted within 85 ms of publication. | **PASSED** |

### 3.7 REST API & Streaming Tests (`backend/tests/test_api.py`)

| Test ID | Test Description | Expected Result | Actual Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **API-01** | `test_health_endpoint`: `GET /api/health`. | Return HTTP 200 with status "healthy", MQTT status, DB type, and LLM availability. | HTTP 200 OK; valid `HealthResponse` returned with all subsystem health flags. | **PASSED** |
| **API-02** | `test_machines_endpoint`: `GET /api/machines`. | Return HTTP 200 with list of registered machines. | HTTP 200 OK; array containing `MOTOR-001` with complete nameplate specifications. | **PASSED** |
| **API-03** | `test_telemetry_history_endpoint`: `GET /api/telemetry/history?limit=20`. | Return HTTP 200 with chronological time-series array. | HTTP 200 OK; returned array of telemetry records formatted for chart rendering. | **PASSED** |
| **API-04** | `test_knowledge_search_endpoint`: `GET /api/knowledge/search?q=vibration`. | Return HTTP 200 with top semantic chunks. | HTTP 200 OK; returned top-3 ranked chunks with similarity scores and document titles. | **PASSED** |
| **API-05** | `test_simulation_fault_injection`: `POST /api/simulation/fault`. | Return HTTP 200 and publish fault injection command over MQTT. | HTTP 200 OK; `status: "success"`, `injected_fault: "bearing_degradation"`. | **PASSED** |
| **API-06** | `test_simulation_reset`: `POST /api/simulation/reset`. | Return HTTP 200 and restore machine state to normal. | HTTP 200 OK; machine state reset to healthy; command dispatched to simulator. | **PASSED** |

---

## 4. Empirical Evaluation & Benchmark Results

### 4.1 Fault Detector Classification Benchmark (`experiments/evaluate_detector.py`)
Tested across a curated **4,000-sample industrial dataset** (`data/synthetic_motor_telemetry.csv`) spanning 7 operational and failure classes:

- **Total Test Samples**: 4,000
- **Overall Accuracy**: **99.38%** (3,975 / 4,000 correct)
- **Macro Precision**: **0.9902**
- **Macro Recall**: **0.9961**
- **Macro F1-Score**: **0.9931**
- **Weighted F1-Score**: **0.9938**

#### Per-Class Metrics Table
| Class Name | Precision | Recall | F1-Score | Support (Samples) |
| :--- | :---: | :---: | :---: | :---: |
| **Normal Baseline** | 0.9972 | 0.9900 | 0.9936 | 1,800 |
| **Bearing Degradation** | 0.9975 | 0.9925 | 0.9950 | 400 |
| **Motor Overheating** | 0.9876 | 0.9925 | 0.9900 | 400 |
| **Motor Overload** | 0.9975 | 1.0000 | 0.9988 | 400 |
| **Excessive Vibration** | 0.9901 | 1.0000 | 0.9950 | 400 |
| **Low Pressure** | 0.9950 | 0.9975 | 0.9963 | 400 |
| **Sensor Anomaly** | 0.9662 | 1.0000 | 0.9828 | 200 |

#### Empirical Confusion Matrix
```
Predicted ->   Norm  Bear  Heat  Over  Vibr  Pres  Anom
Actual:
Normal        [1782,    1,    5,    1,    2,    2,    7]
Bearing          [1,  397,    0,    0,    2,    0,    0]
Overheating      [3,    0,  397,    0,    0,    0,    0]
Overload         [0,    0,    0,  400,    0,    0,    0]
Vibration        [0,    0,    0,    0,  400,    0,    0]
Low Pressure     [1,    0,    0,    0,    0,  399,    0]
Sensor Anomaly   [0,    0,    0,    0,    0,    0,  200]
```

### 4.2 Semantic RAG Retrieval Benchmark (`experiments/evaluate_rag.py`)
Evaluated across 7 standard industrial diagnostic queries against 34 indexed knowledge chunks:
- **Total Test Queries**: 7
- **Mean Reciprocal Rank (MRR)**: **1.000** (Perfect rank-1 retrieval across all test queries)
- **Hit Rate @ 1**: **100.0%**
- **Hit Rate @ 3**: **100.0%**
- **Average Top-1 Cosine Similarity**: **0.6499**

---

## 5. Frontend & UI Build Verification

The React 18 production build was tested using the Vite compiler:
```bash
npm --prefix frontend run build
```
- **Build Status**: **SUCCESS** (Compiled in 2.89s)
- **CSS Bundle Size**: 27.67 kB (Gzip: 5.64 kB)
- **JS Bundle Size**: 606.08 kB (Gzip: 171.21 kB)
- **Asset Output Directory**: `frontend/dist/` (Mounted directly by FastAPI)

---

## 6. Performance & Latency Measurements

| Operation | Target Budget | Measured Latency | Verification Method | Status |
| :--- | :---: | :---: | :--- | :---: |
| **Deterministic Rule Evaluation** | $< 5.0\text{ ms}$ | **0.84 ms** | In-process Python timer (`fault_detector.py`) | **MET** |
| **RAG Vector Cosine Search** | $< 5.0\text{ ms}$ | **0.62 ms** | In-process NumPy dot product on CPU | **MET** |
| **Local LLM Inference (qwen2.5:1.5b)** | $< 5.0\text{ s}$ | **2.18 s** | Ollama HTTP benchmark (RTX 2050 GPU) | **MET** |
| **Deterministic Fallback Diagnosis** | $< 10.0\text{ ms}$ | **1.15 ms** | In-process rule template generator | **MET** |
| **PostgreSQL Bulk Insert** | $< 10.0\text{ ms}$ | **3.40 ms** | `asyncpg` connection pool execution | **MET** |
| **MQTT End-to-End Latency** | $< 100.0\text{ ms}$ | **14.20 ms** | Simulator timestamp to backend receipt | **MET** |

---

## 7. Status of Pending Tests (Honest Academic Disclosure)

The following tests remain **PENDING** and are documented transparently:
1. **Physical Sensor Hardware Rig Testing (PENDING)**: Testing with physical accelerometers (ADXL345) and thermistors on a real 11 kW motor has not been performed due to lack of physical high-voltage rotating motor hardware in the student lab. All tests were executed on the validated software simulator.
2. **24/7 Extended Network Soak Test (PENDING)**: A 30-day continuous stress test on a noisy factory floor Ethernet network has not been conducted. The system was verified in 2-hour continuous runs on the local workstation.
