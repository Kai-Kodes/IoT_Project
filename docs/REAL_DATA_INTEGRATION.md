# P_311: Real-World Data Integration & Telemetry Replay

## 1. Overview & Architectural Principle

In industrial IoT deployments, telemetry data originates from real physical sensors (vibration accelerometers, PT100 RTDs, current transformers, Hall-effect tachometers, pressure transmitters).

In academic evaluations or laboratory settings, access to a live industrial factory floor is often restricted. Project P_311 provides a dedicated **Real-Data Replay Adapter** (`scripts/replay_dataset.py`) to stream benchmark datasets or captured real-world machinery logs through the exact same ingestion pipeline.

> **CRITICAL ARCHITECTURAL RULE:**
> Real data and external datasets **NEVER** write directly to PostgreSQL or SQLite.
>
> Writing directly to a database bypasses:
> 1. Ingestion latency modeling
> 2. Network serialization and MQTT protocol overhead
> 3. Real-time deterministic fault detection
> 4. Dynamic triggering of RAG and Local LLM diagnosis
>
> Therefore, external datasets **MUST** stream through the Mosquitto MQTT broker (`p311/machine/<id>/telemetry`), exactly mimicking physical edge sensor hardware.

---

## 2. Replay Script Architecture

The replay adapter script is located at:
```
scripts/replay_dataset.py
```

### Key Capabilities:
- **Streaming over MQTT**: Publishes JSON packets matching the strict `TelemetryIn` contract to `p311/machine/<machine_id>/telemetry`.
- **Configurable Rate Multiplier (`--rate`)**:
  - `1.0`: Exact real-time replay (1 sample per second / 1 Hz).
  - `5.0` or `10.0`: Accelerated laboratory evaluation (processes datasets 5x or 10x faster).
- **Continuous Loop (`--loop`)**: Automatically loops back to the start when reaching the end of the file for 24/7 continuous SCADA monitoring testing.
- **Timestamp Modes**:
  - Default: Generates real-time current UTC timestamps (`datetime.now(timezone.utc)`), ensuring all Grafana panels immediately display live graphs in the `Last 5 minutes` window.
  - `--original-timestamps`: Preserves original CSV timestamps for historical audit replay.
- **Dry-Run Mode (`--dry-run`)**: Parses, validates, and prints the first 5 records without establishing an MQTT connection.

---

## 3. Usage Examples

### A. Quick Validation Dry-Run
```bash
.venv/bin/python scripts/replay_dataset.py --file data/synthetic_motor_telemetry.csv --dry-run
```

### B. Standard Real-Time Replay (1 Hz)
```bash
.venv/bin/python scripts/replay_dataset.py \
  --file data/synthetic_motor_telemetry.csv \
  --rate 1.0 \
  --loop
```

### C. Accelerated Experimentation (5x speed, first 500 records)
```bash
.venv/bin/python scripts/replay_dataset.py \
  --file data/synthetic_motor_telemetry.csv \
  --rate 5.0 \
  --max-records 500
```

### D. Replaying to a Custom Machine ID
```bash
.venv/bin/python scripts/replay_dataset.py \
  --file data/synthetic_motor_telemetry.csv \
  --machine-id PUMP-002 \
  --rate 2.0
```

---

## 4. Integrating Public Industrial Benchmark Datasets

You can integrate standard industrial prognostic datasets (e.g., NASA C-MAPSS, IMS Bearing Dataset, Case Western Reserve University (CWRU) Bearing Data, or SEU Drivetrain Data) into P_311 by formatting them into the P_311 standard CSV schema:

### Required CSV Columns:
```csv
timestamp,machine_id,temperature,vibration,current,rpm,voltage,pressure,operating_state,fault_label,severity
```

### Example Transformation Script Pattern:
```python
import pandas as pd
from datetime import datetime, timezone

# Load raw benchmark file (e.g. CWRU or IMS)
raw_df = pd.read_csv("raw_cwru_bearing_data.csv")

# Map raw vibration columns to P_311 schema
p311_df = pd.DataFrame()
p311_df["timestamp"] = [datetime.now(timezone.utc).isoformat() for _ in range(len(raw_df))]
p311_df["machine_id"] = "MOTOR-001"
p311_df["temperature"] = raw_df["DE_temp"].fillna(52.0)
p311_df["vibration"] = raw_df["DE_time_rms"]  # Drive end vibration velocity RMS in mm/s
p311_df["current"] = raw_df["motor_current"].fillna(9.0)
p311_df["rpm"] = raw_df["shaft_speed"].fillna(1485.0)
p311_df["voltage"] = 230.0
p311_df["pressure"] = 4.2
p311_df["operating_state"] = "running"
p311_df["fault_label"] = raw_df["fault_class"]  # e.g., bearing_degradation
p311_df["severity"] = raw_df["severity"]        # e.g., high

p311_df.to_csv("data/cwru_transformed.csv", index=False)
```

Once converted, execute the replay script:
```bash
.venv/bin/python scripts/replay_dataset.py --file data/cwru_transformed.csv --rate 1.0
```

The system will ingest the data, trigger the deterministic detector on physical limit breaches, invoke RAG and the Local LLM, store records in PostgreSQL, and render live time-series in Grafana.
