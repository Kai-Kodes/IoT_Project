# P_311: Grafana to PostgreSQL Data Pipeline Guide

## 1. Overview & Architectural Principle

Project P_311 uses a decoupled industrial IoT data pipeline:

```
[Edge Simulator / Replay Adapter]
             ↓  MQTT QoS 1 (JSON over TCP port 1883)
     [Mosquitto Broker]
             ↓  Subscription: p311/machine/+/telemetry
      [FastAPI Core]
             ↓  Bulk Asyncpg Insert & Deterministic Evaluation
     [PostgreSQL 16] (Port 5433 host / 5432 internal)
             ↓  Direct SQL Time-Series Queries
      [Grafana OSS] (Port 3000)
             ↓
[Industrial SCADA Dashboards]
```

### The 4 Stages of the Telemetry Pipeline:
1. **MQTT Transports the Data**: Telemetry packets travel from edge sensors or the motor simulator across TCP port 1883 using lightweight publish-subscribe messaging.
2. **FastAPI Inserts the Data**: The backend validates the incoming telemetry against Pydantic schemas, runs deterministic ISO 10816 rules, and inserts the data into PostgreSQL using an async connection pool.
3. **PostgreSQL Stores the Data**: Persistent relational time-series storage with `TIMESTAMPTZ` and composite indexes (`machine_id`, `timestamp DESC`).
4. **Grafana Reads the Data**: Grafana queries PostgreSQL directly over SQL using the provisioned `p311-postgres-ds` datasource, rendering real-time graphs and tables without calling FastAPI.

---

## 2. Infrastructure & Networking Topology

| Component | Execution Environment | Service Name | Network Location | External Host Port |
| :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL** | Docker Container | `postgres` (`p311-postgres`) | `postgres:5432` on `proj_default` | `5433` (`5433:5432`) |
| **Grafana** | Docker Container | `grafana` (`p311-grafana`) | `grafana:3000` on `proj_default` | `3000` (`3000:3000`) |
| **Mosquitto** | Host Linux Service / Docker | `p311-mosquitto` | `localhost:1883` | `1883` |
| **FastAPI** | Host Python Virtualenv | Native process | `localhost:8000` | `8000` |
| **Simulator** | Host Python Virtualenv | Native process | `localhost` | — |

### How Grafana Reaches PostgreSQL:
- Grafana and PostgreSQL are both services defined in `docker-compose.yml` and share the Docker bridge network `proj_default`.
- Grafana connects to PostgreSQL using the internal service hostname **`postgres`** on port **`5432`** (`postgres:5432`), **NOT** `localhost`.
- Host processes (like FastAPI and migration scripts) connect to PostgreSQL using **`localhost:5433`**.

---

## 3. Database Schema & Data Models

### Database Name: `p311_iot`
**User:** `p311_admin`  
**Password:** Configured via `.env` (`POSTGRES_PASSWORD`)

### Telemetry Table: `telemetry`
```sql
CREATE TABLE telemetry (
    id BIGSERIAL PRIMARY KEY,
    machine_id VARCHAR(64) NOT NULL REFERENCES machines(id),
    timestamp TIMESTAMPTZ NOT NULL,
    temperature DOUBLE PRECISION NOT NULL,
    vibration DOUBLE PRECISION NOT NULL,
    current DOUBLE PRECISION NOT NULL,
    rpm DOUBLE PRECISION NOT NULL,
    voltage DOUBLE PRECISION NOT NULL,
    pressure DOUBLE PRECISION NOT NULL,
    operating_state VARCHAR(32) NOT NULL
);

CREATE INDEX idx_telemetry_machine_time ON telemetry (machine_id, timestamp DESC);
```

### Key Columns for Grafana:
- `timestamp`: Stored as `TIMESTAMPTZ` in UTC. Mapped to `"time"` in Grafana queries.
- `temperature`: Stator/bearing surface temperature in °C.
- `vibration`: Overall vibration velocity RMS in mm/s (evaluated against ISO 10816-3).
- `current`: Stator line current in Amperes (FLA rated at 9.0 A).
- `rpm`: Shaft rotational speed in RPM (rated at 1485 RPM).
- `pressure`: Auxiliary lubrication/cooling circuit pressure in bar.
- `voltage`: Supply voltage in Volts (nominal 230 V / 400 V).

---

## 4. Grafana Datasource Configuration

The datasource is provisioned declaratively via:
`docker/grafana/provisioning/datasources/postgres.yml`

```yaml
apiVersion: 1

datasources:
  - name: PostgreSQL-P311
    type: postgres
    uid: p311-postgres-ds
    access: proxy
    url: postgres:5432
    user: $__env{POSTGRES_USER}
    isDefault: true
    jsonData:
      database: $__env{POSTGRES_DB}
      sslmode: disable
      maxOpenConns: 10
      maxIdleConns: 5
      connMaxLifetime: 14400
      postgresVersion: 1600
      timescaledb: false
    secureJsonData:
      password: $__env{POSTGRES_PASSWORD}
    editable: true
```

*Note: Environment variables `$__env{POSTGRES_USER}`, `$__env{POSTGRES_DB}`, and `$__env{POSTGRES_PASSWORD}` are injected directly from `docker-compose.yml`.*

---

## 5. Dashboard Configuration & Queries

**Dashboard File:** `docker/grafana/dashboards/p311_industrial_telemetry.json`  
**Provisioning File:** `docker/grafana/provisioning/dashboards/dashboards.yml`  
**Dashboard UID:** `p311-telemetry-dash`  
**Access URL:** [http://localhost:3000/d/p311-telemetry-dash](http://localhost:3000/d/p311-telemetry-dash)

### Query Pattern:
In Grafana 11, SQL targets must specify `"format": "table"` and `"rawQuery": true` to prevent parser format panics.

#### A. Continuous Telemetry Time-Series:
```sql
SELECT 
    timestamp AS "time", 
    temperature AS "Temperature (°C)" 
FROM telemetry 
WHERE $__timeFilter(timestamp) 
ORDER BY timestamp ASC;
```

#### B. Live Telemetry Stream Buffer (Table View):
```sql
SELECT 
    timestamp AS "Time",
    machine_id AS "Machine",
    temperature AS "Temp (°C)",
    vibration AS "Vib (mm/s)",
    current AS "Current (A)",
    rpm AS "RPM",
    voltage AS "Volt (V)",
    pressure AS "Press (bar)",
    operating_state AS "Operating State"
FROM telemetry
ORDER BY timestamp DESC
LIMIT 50;
```

#### C. Recent Fault Events Audit Table:
```sql
SELECT 
    timestamp AS "Time", 
    machine_id AS "Machine", 
    fault_type AS "Fault Type", 
    severity AS "Severity", 
    confidence AS "Confidence", 
    triggered_rules::text AS "Triggered Rules" 
FROM fault_events 
ORDER BY timestamp DESC 
LIMIT 50;
```

---

## 6. Verification Commands

### 1. Verify PostgreSQL Container & Row Counts:
```bash
.venv/bin/python -c "
import asyncio, asyncpg
async def check():
    conn = await asyncpg.connect('postgresql://p311_admin:p311_industrial_secret@localhost:5433/p311_iot')
    count = await conn.fetchval('SELECT count(*) FROM telemetry;')
    latest = await conn.fetchrow('SELECT id, timestamp, temperature, vibration FROM telemetry ORDER BY id DESC LIMIT 1;')
    print(f'Total Telemetry Rows: {count}')
    print(f'Latest Record: {dict(latest)}')
    await conn.close()
asyncio.run(check())
"
```

### 2. Verify Grafana Datasource Health:
```bash
curl -s http://admin:admin@localhost:3000/api/datasources/uid/p311-postgres-ds/health
# Expected: {"message":"Database Connection OK","status":"OK"}
```

### 3. Verify Live Query Results via Grafana API:
```bash
curl -s -X POST http://admin:admin@localhost:3000/api/ds/query \
  -H "Content-Type: application/json" \
  -d '{
    "from": "now-15m",
    "to": "now",
    "queries": [
      {
        "refId": "A",
        "datasource": { "type": "postgres", "uid": "p311-postgres-ds" },
        "format": "table",
        "rawSql": "SELECT timestamp AS \"Time\", temperature, vibration FROM telemetry ORDER BY timestamp DESC LIMIT 3;"
      }
    ]
  }' | jq '.results.A.frames[0].data.values'
```
