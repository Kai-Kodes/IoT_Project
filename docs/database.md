# Database Architecture & Storage Policy

## 1. Why SQLite?
1. **Zero Daemon Overhead**: Unlike PostgreSQL or MySQL, SQLite runs entirely in-process, consuming zero background RAM and zero extra CPU threads when idle.
2. **Single-File Portability**: All telemetry, faults, diagnoses, and machine profiles reside in a single portable file (`data/p311.db`).
3. **Edge IoT Alignment**: Industrial edge gateways (such as Siemens IOT2050 or Advantech boxes) use embedded SQLite to buffer telemetry locally before edge processing.

## 2. Concurrency with Write-Ahead Logging (WAL)
On every connection initialization, we execute:
```sql
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;
```
- In default rollback journal mode, writing locks the entire database, blocking concurrent reads.
- In **WAL mode**, readers never block writers, and writers never block readers. This guarantees that high-frequency 1 Hz telemetry writes from the MQTT consumer do not interrupt dashboard historical queries.

## 3. Storage Schema
- `machines`: Master registry of monitored equipment (ratings, status).
- `telemetry`: High-frequency sensor samples (`temperature`, `vibration`, `current`, `rpm`, `voltage`, `pressure`). Indexed on `(machine_id, timestamp DESC)`.
- `fault_events`: Detected anomalies, severity levels, and triggered rule lists.
- `diagnoses`: Generated diagnostic reports, likely causes, maintenance checklists, confidence scores, and knowledge sources.
- `knowledge_documents`: Registry of technical manuals loaded into the RAG vector index.

## 4. Telemetry Retention & Bounded Growth Policy
To prevent unbounded SSD disk growth during prolonged operation:
- The database manager implements an automated retention pruning mechanism (`purge_old_telemetry()`).
- High-frequency telemetry is capped at the latest `TELEMETRY_RETENTION_LIMIT` (default: 5,000 records, approximately 1.5 hours of continuous 1 Hz operation per machine).
- Fault events and diagnostic reports are persisted indefinitely as permanent maintenance audit records.
