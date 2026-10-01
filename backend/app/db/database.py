"""
P_311 PostgreSQL Primary Database Layer
Enterprise-grade async connection pooling using asyncpg for PostgreSQL,
with optional graceful SQLite fallback.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiosqlite
import asyncpg

from backend.app.core.config import settings

logger = logging.getLogger("db")


class PostgresDatabaseManager:
    """Primary PostgreSQL Database Manager using asyncpg connection pool."""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.host = settings.POSTGRES_HOST
        self.port = settings.POSTGRES_PORT
        self.database = settings.POSTGRES_DB
        self.user = settings.POSTGRES_USER
        self.password = settings.POSTGRES_PASSWORD
        self.min_size = settings.POSTGRES_POOL_MIN
        self.max_size = settings.POSTGRES_POOL_MAX

    async def _init_connection(self, conn: asyncpg.Connection):
        """Registers JSONB codec so dict/list map directly to JSONB columns."""
        await conn.set_type_codec(
            "jsonb",
            encoder=json.dumps,
            decoder=json.loads,
            schema="pg_catalog",
        )

    async def init_db(self):
        """Initializes connection pool and ensures schema exists."""
        logger.info(
            "Initializing PostgreSQL connection pool at %s:%d/%s (user: %s)...",
            self.host,
            self.port,
            self.database,
            self.user,
        )
        self.pool = await asyncpg.create_pool(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            min_size=self.min_size,
            max_size=self.max_size,
            init=self._init_connection,
        )

        async with self.pool.acquire() as conn:
            # 1. Machines
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS machines (
                    id VARCHAR(64) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    type VARCHAR(255) NOT NULL,
                    rated_voltage DOUBLE PRECISION NOT NULL,
                    rated_current DOUBLE PRECISION NOT NULL,
                    rated_rpm DOUBLE PRECISION NOT NULL,
                    status VARCHAR(32) NOT NULL DEFAULT 'healthy',
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Telemetry
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
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
            """)

            # 3. Fault Events
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fault_events (
                    id VARCHAR(64) PRIMARY KEY,
                    machine_id VARCHAR(64) NOT NULL REFERENCES machines(id),
                    timestamp TIMESTAMPTZ NOT NULL,
                    fault_type VARCHAR(64) NOT NULL,
                    severity VARCHAR(32) NOT NULL,
                    confidence DOUBLE PRECISION NOT NULL,
                    sensor_evidence JSONB NOT NULL,
                    triggered_rules JSONB NOT NULL,
                    resolved_at TIMESTAMPTZ
                );
            """)

            # 4. Diagnoses
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS diagnoses (
                    id VARCHAR(64) PRIMARY KEY,
                    fault_event_id VARCHAR(64) NOT NULL REFERENCES fault_events(id),
                    machine_id VARCHAR(64) NOT NULL REFERENCES machines(id),
                    timestamp TIMESTAMPTZ NOT NULL,
                    fault_title VARCHAR(255) NOT NULL,
                    severity VARCHAR(32) NOT NULL,
                    sensor_evidence JSONB NOT NULL,
                    likely_causes JSONB NOT NULL,
                    recommended_checks JSONB NOT NULL,
                    corrective_actions JSONB NOT NULL,
                    confidence DOUBLE PRECISION NOT NULL,
                    uncertainty TEXT NOT NULL,
                    knowledge_sources JSONB NOT NULL,
                    raw_llm_response TEXT,
                    execution_time_ms INTEGER NOT NULL,
                    is_fallback BOOLEAN NOT NULL DEFAULT FALSE
                );
            """)

            # 5. Knowledge Documents Meta
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_documents (
                    id VARCHAR(64) PRIMARY KEY,
                    filename VARCHAR(255) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    category VARCHAR(128) NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Indexes for high-speed time-series retrieval & Grafana queries
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_time ON telemetry(timestamp DESC);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_machine_time ON telemetry(machine_id, timestamp DESC);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_faults_time ON fault_events(timestamp DESC);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_faults_machine_time ON fault_events(machine_id, timestamp DESC);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_diagnoses_machine_time ON diagnoses(machine_id, timestamp DESC);")

            # Seed default machine
            await conn.execute("""
                INSERT INTO machines (id, name, type, rated_voltage, rated_current, rated_rpm, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO NOTHING;
            """, settings.DEFAULT_MACHINE_ID, "Main Extruder Induction Motor", "3-Phase Squirrel Cage Induction Motor (11 kW)", 400.0, 9.0, 1485.0, "healthy")

        logger.info("PostgreSQL Database connected & schema verified (%s:%d/%s)", self.host, self.port, self.database)

    async def check_health(self) -> bool:
        """Returns True if database pool is healthy and accepting queries."""
        try:
            if not self.pool:
                return False
            async with self.pool.acquire() as conn:
                val = await conn.fetchval("SELECT 1;")
                return val == 1
        except Exception as e:
            logger.warning("PostgreSQL health check failed: %s", e)
            return False

    async def close(self):
        """Closes the asyncpg connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None
            logger.info("PostgreSQL connection pool closed.")

    async def insert_telemetry(self, t: Dict[str, Any]):
        """Inserts real-time or historical telemetry."""
        ts = t["timestamp"]
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)
        else:
            dt = ts

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO telemetry (machine_id, timestamp, temperature, vibration, current, rpm, voltage, pressure, operating_state)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);
            """,
                t["machine_id"],
                dt,
                float(t["temperature"]),
                float(t["vibration"]),
                float(t["current"]),
                float(t["rpm"]),
                float(t["voltage"]),
                float(t["pressure"]),
                t.get("state", "running")
            )

    async def purge_old_telemetry(self, keep_latest: int = settings.TELEMETRY_RETENTION_LIMIT):
        """Keeps only the most recent N telemetry rows to prevent unbounded disk growth."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                DELETE FROM telemetry
                WHERE id NOT IN (
                    SELECT id FROM telemetry ORDER BY id DESC LIMIT $1
                );
            """, keep_latest)

    async def get_recent_telemetry(self, machine_id: str, limit: int = 60) -> List[Dict[str, Any]]:
        """Returns the most recent N telemetry points in chronological order."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM telemetry
                WHERE machine_id = $1
                ORDER BY timestamp DESC
                LIMIT $2;
            """, machine_id, limit)

            results = []
            for r in reversed(rows):
                item = dict(r)
                item["timestamp"] = item["timestamp"].isoformat()
                item["state"] = item.get("operating_state", "running")
                results.append(item)
            return results

    async def get_latest_telemetry(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Returns the single latest telemetry sample."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM telemetry
                WHERE machine_id = $1
                ORDER BY timestamp DESC
                LIMIT 1;
            """, machine_id)
            if not row:
                return None
            item = dict(row)
            item["timestamp"] = item["timestamp"].isoformat()
            item["state"] = item.get("operating_state", "running")
            return item

    async def insert_fault_event(self, fault: Dict[str, Any]):
        """Persists a detected fault event and updates the machine status."""
        ts = fault["timestamp"]
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if isinstance(ts, str) else ts

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO fault_events (id, machine_id, timestamp, fault_type, severity, confidence, sensor_evidence, triggered_rules)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (id) DO UPDATE SET
                    severity = EXCLUDED.severity,
                    confidence = EXCLUDED.confidence,
                    sensor_evidence = EXCLUDED.sensor_evidence,
                    triggered_rules = EXCLUDED.triggered_rules;
            """,
                fault["id"],
                fault["machine_id"],
                dt,
                fault["fault_type"],
                fault["severity"],
                float(fault["confidence"]),
                fault["sensor_evidence"],
                fault["triggered_rules"]
            )
            # Update machine health status
            await conn.execute("UPDATE machines SET status = $1 WHERE id = $2;", fault["severity"], fault["machine_id"])

    async def get_fault_events(self, machine_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns historical fault events in reverse chronological order."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM fault_events
                WHERE machine_id = $1
                ORDER BY timestamp DESC
                LIMIT $2;
            """, machine_id, limit)

            results = []
            for r in rows:
                item = dict(r)
                item["timestamp"] = item["timestamp"].isoformat()
                if item["resolved_at"]:
                    item["resolved_at"] = item["resolved_at"].isoformat()
                results.append(item)
            return results

    async def get_fault_event_by_id(self, fault_id: str) -> Optional[Dict[str, Any]]:
        """Returns single fault event by primary key."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM fault_events WHERE id = $1;", fault_id)
            if not row:
                return None
            item = dict(row)
            item["timestamp"] = item["timestamp"].isoformat()
            if item["resolved_at"]:
                item["resolved_at"] = item["resolved_at"].isoformat()
            return item

    async def resolve_fault_event(self, fault_id: str, resolved_at: str):
        """Marks a fault event as resolved."""
        dt = datetime.fromisoformat(resolved_at.replace("Z", "+00:00")) if isinstance(resolved_at, str) else resolved_at
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE fault_events SET resolved_at = $1 WHERE id = $2;", dt, fault_id)

    async def insert_diagnosis(self, diag: Dict[str, Any]):
        """Persists AI-generated or fallback root-cause diagnosis."""
        ts = diag["timestamp"]
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00")) if isinstance(ts, str) else ts

        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO diagnoses (
                    id, fault_event_id, machine_id, timestamp, fault_title, severity,
                    sensor_evidence, likely_causes, recommended_checks, corrective_actions,
                    confidence, uncertainty, knowledge_sources, raw_llm_response,
                    execution_time_ms, is_fallback
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                ON CONFLICT (id) DO NOTHING;
            """,
                diag["id"],
                diag["fault_event_id"],
                diag["machine_id"],
                dt,
                diag["fault_title"],
                diag["severity"],
                diag["sensor_evidence"],
                diag["likely_causes"],
                diag["recommended_checks"],
                diag["corrective_actions"],
                float(diag["confidence"]),
                diag["uncertainty"],
                diag["knowledge_sources"],
                diag.get("raw_llm_response", ""),
                int(diag["execution_time_ms"]),
                bool(diag.get("is_fallback", False))
            )

    async def get_latest_diagnosis(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Returns the most recent diagnosis."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM diagnoses
                WHERE machine_id = $1
                ORDER BY timestamp DESC
                LIMIT 1;
            """, machine_id)
            if not row:
                return None
            return self._format_diag_row(row)

    async def get_diagnosis_by_id(self, diagnosis_id: str) -> Optional[Dict[str, Any]]:
        """Returns diagnosis by ID."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM diagnoses WHERE id = $1;", diagnosis_id)
            if not row:
                return None
            return self._format_diag_row(row)

    def _format_diag_row(self, row: asyncpg.Record) -> Dict[str, Any]:
        item = dict(row)
        item["timestamp"] = item["timestamp"].isoformat()
        item["is_fallback"] = bool(item["is_fallback"])
        return item

    async def get_machines(self) -> List[Dict[str, Any]]:
        """Lists all registered machines."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM machines ORDER BY id ASC;")
            results = []
            for r in rows:
                item = dict(r)
                if item["created_at"]:
                    item["created_at"] = item["created_at"].isoformat()
                results.append(item)
            return results

    async def get_machine(self, machine_id: str) -> Optional[Dict[str, Any]]:
        """Returns machine profile."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM machines WHERE id = $1;", machine_id)
            if not row:
                return None
            item = dict(row)
            if item["created_at"]:
                item["created_at"] = item["created_at"].isoformat()
            return item

    async def update_machine_status(self, machine_id: str, status: str):
        """Updates health status (healthy, warning, critical, alarm)."""
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE machines SET status = $1 WHERE id = $2;", status, machine_id)

    async def close(self):
        """Closes connection pool."""
        if self.pool:
            await self.pool.close()
            self.pool = None


class DatabaseManager:
    """
    Unified Database Manager router.
    Routes queries to PostgreSQL (primary) with automatic fallback to SQLite
    when explicitly configured or when PostgreSQL is unreachable.
    """

    def __init__(self, db_path: Optional[str] = None, use_postgres: Optional[bool] = None):
        self.pg = PostgresDatabaseManager()
        self.sqlite_path = db_path or settings.DATABASE_PATH
        if use_postgres is not None:
            self.use_postgres = use_postgres
        elif db_path is not None:
            self.use_postgres = False
        else:
            self.use_postgres = settings.USE_POSTGRES

    async def close(self):
        """Closes active database resources."""
        if self.use_postgres:
            await self.pg.close()

    async def init_db(self):
        if self.use_postgres:
            try:
                await self.pg.init_db()
                logger.info("Using PostgreSQL as primary database.")
                return
            except Exception as e:
                logger.error("Failed to connect to PostgreSQL: %s. Falling back to SQLite.", e)
                self.use_postgres = False

        # SQLite fallback setup
        Path(self.sqlite_path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.sqlite_path) as db:
            await db.execute("PRAGMA journal_mode = WAL;")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS machines (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    rated_voltage REAL NOT NULL,
                    rated_current REAL NOT NULL,
                    rated_rpm REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'healthy',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    machine_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    temperature REAL NOT NULL,
                    vibration REAL NOT NULL,
                    current REAL NOT NULL,
                    rpm REAL NOT NULL,
                    voltage REAL NOT NULL,
                    pressure REAL NOT NULL,
                    operating_state TEXT NOT NULL,
                    FOREIGN KEY(machine_id) REFERENCES machines(id)
                );
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS fault_events (
                    id TEXT PRIMARY KEY,
                    machine_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    fault_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    sensor_evidence_json TEXT NOT NULL,
                    triggered_rules_json TEXT NOT NULL,
                    resolved_at TIMESTAMP,
                    FOREIGN KEY(machine_id) REFERENCES machines(id)
                );
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS diagnoses (
                    id TEXT PRIMARY KEY,
                    fault_event_id TEXT NOT NULL,
                    machine_id TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    fault_title TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    sensor_evidence_json TEXT NOT NULL,
                    likely_causes_json TEXT NOT NULL,
                    recommended_checks_json TEXT NOT NULL,
                    corrective_actions_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    uncertainty TEXT NOT NULL,
                    knowledge_sources_json TEXT NOT NULL,
                    raw_llm_response TEXT,
                    execution_time_ms INTEGER NOT NULL,
                    is_fallback BOOLEAN NOT NULL DEFAULT 0,
                    FOREIGN KEY(fault_event_id) REFERENCES fault_events(id),
                    FOREIGN KEY(machine_id) REFERENCES machines(id)
                );
            """)
            await db.execute("""
                INSERT OR IGNORE INTO machines (id, name, type, rated_voltage, rated_current, rated_rpm, status)
                VALUES ('MOTOR-001', 'Main Extruder Induction Motor', '3-Phase Squirrel Cage Induction Motor (11 kW)', 400.0, 9.0, 1485.0, 'healthy');
            """)
            await db.commit()
            logger.info("Using SQLite fallback database at %s", self.sqlite_path)

    async def check_health(self) -> bool:
        if self.use_postgres:
            return await self.pg.check_health()
        return True

    async def insert_telemetry(self, t: Dict[str, Any]):
        if self.use_postgres:
            await self.pg.insert_telemetry(t)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("""
                    INSERT INTO telemetry (machine_id, timestamp, temperature, vibration, current, rpm, voltage, pressure, operating_state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (t["machine_id"], t["timestamp"], t["temperature"], t["vibration"], t["current"], t["rpm"], t["voltage"], t["pressure"], t.get("state", "running")))
                await db.commit()

    async def purge_old_telemetry(self, keep_latest: int = settings.TELEMETRY_RETENTION_LIMIT):
        if self.use_postgres:
            await self.pg.purge_old_telemetry(keep_latest)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("DELETE FROM telemetry WHERE id NOT IN (SELECT id FROM telemetry ORDER BY id DESC LIMIT ?)", (keep_latest,))
                await db.commit()

    async def get_recent_telemetry(self, machine_id: str, limit: int = 60) -> List[Dict[str, Any]]:
        if self.use_postgres:
            return await self.pg.get_recent_telemetry(machine_id, limit)
        async with aiosqlite.connect(self.sqlite_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM telemetry WHERE machine_id = ? ORDER BY id DESC LIMIT ?", (machine_id, limit))
            rows = await cursor.fetchall()
            results = []
            for r in reversed(rows):
                item = dict(r)
                item["state"] = item.get("operating_state", "running")
                results.append(item)
            return results

    async def get_latest_telemetry(self, machine_id: str) -> Optional[Dict[str, Any]]:
        if self.use_postgres:
            return await self.pg.get_latest_telemetry(machine_id)
        async with aiosqlite.connect(self.sqlite_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM telemetry WHERE machine_id = ? ORDER BY id DESC LIMIT 1", (machine_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            item = dict(row)
            item["state"] = item.get("operating_state", "running")
            return item

    async def insert_fault_event(self, fault: Dict[str, Any]):
        if self.use_postgres:
            await self.pg.insert_fault_event(fault)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("""
                    INSERT INTO fault_events (id, machine_id, timestamp, fault_type, severity, confidence, sensor_evidence_json, triggered_rules_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fault["id"], fault["machine_id"], fault["timestamp"], fault["fault_type"], fault["severity"],
                    fault["confidence"], json.dumps(fault["sensor_evidence"]), json.dumps(fault["triggered_rules"])
                ))
                await db.execute("UPDATE machines SET status = ? WHERE id = ?", (fault["severity"], fault["machine_id"]))
                await db.commit()

    async def get_fault_events(self, machine_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        if self.use_postgres:
            return await self.pg.get_fault_events(machine_id, limit)
        async with aiosqlite.connect(self.sqlite_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM fault_events WHERE machine_id = ? ORDER BY timestamp DESC LIMIT ?", (machine_id, limit))
            rows = await cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["sensor_evidence"] = json.loads(item["sensor_evidence_json"])
                item["triggered_rules"] = json.loads(item["triggered_rules_json"])
                results.append(item)
            return results

    async def get_fault_event_by_id(self, fault_id: str) -> Optional[Dict[str, Any]]:
        if self.use_postgres:
            return await self.pg.get_fault_event_by_id(fault_id)
        async with aiosqlite.connect(self.sqlite_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM fault_events WHERE id = ?", (fault_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            item = dict(row)
            item["sensor_evidence"] = json.loads(item["sensor_evidence_json"])
            item["triggered_rules"] = json.loads(item["triggered_rules_json"])
            return item

    async def resolve_fault_event(self, fault_id: str, resolved_at: str):
        if self.use_postgres:
            await self.pg.resolve_fault_event(fault_id, resolved_at)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("UPDATE fault_events SET resolved_at = ? WHERE id = ?", (resolved_at, fault_id))
                await db.commit()

    async def insert_diagnosis(self, diag: Dict[str, Any]):
        if self.use_postgres:
            await self.pg.insert_diagnosis(diag)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("""
                    INSERT INTO diagnoses (
                        id, fault_event_id, machine_id, timestamp, fault_title, severity,
                        sensor_evidence_json, likely_causes_json, recommended_checks_json,
                        corrective_actions_json, confidence, uncertainty, knowledge_sources_json,
                        raw_llm_response, execution_time_ms, is_fallback
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    diag["id"], diag["fault_event_id"], diag["machine_id"], diag["timestamp"], diag["fault_title"],
                    diag["severity"], json.dumps(diag["sensor_evidence"]), json.dumps(diag["likely_causes"]),
                    json.dumps(diag["recommended_checks"]), json.dumps(diag["corrective_actions"]),
                    diag["confidence"], diag["uncertainty"], json.dumps(diag["knowledge_sources"]),
                    diag.get("raw_llm_response", ""), diag["execution_time_ms"], 1 if diag.get("is_fallback") else 0
                ))
                await db.commit()

    async def get_latest_diagnosis(self, machine_id: str) -> Optional[Dict[str, Any]]:
        if self.use_postgres:
            return await self.pg.get_latest_diagnosis(machine_id)
        async with aiosqlite.connect(self.sqlite_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM diagnoses WHERE machine_id = ? ORDER BY timestamp DESC LIMIT 1", (machine_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            item = dict(row)
            item["sensor_evidence"] = json.loads(item["sensor_evidence_json"])
            item["likely_causes"] = json.loads(item["likely_causes_json"])
            item["recommended_checks"] = json.loads(item["recommended_checks_json"])
            item["corrective_actions"] = json.loads(item["corrective_actions_json"])
            item["knowledge_sources"] = json.loads(item["knowledge_sources_json"])
            item["is_fallback"] = bool(item["is_fallback"])
            return item

    async def get_diagnosis_by_id(self, diagnosis_id: str) -> Optional[Dict[str, Any]]:
        if self.use_postgres:
            return await self.pg.get_diagnosis_by_id(diagnosis_id)
        async with aiosqlite.connect(self.sqlite_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM diagnoses WHERE id = ?", (diagnosis_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            item = dict(row)
            item["sensor_evidence"] = json.loads(item["sensor_evidence_json"])
            item["likely_causes"] = json.loads(item["likely_causes_json"])
            item["recommended_checks"] = json.loads(item["recommended_checks_json"])
            item["corrective_actions"] = json.loads(item["corrective_actions_json"])
            item["knowledge_sources"] = json.loads(item["knowledge_sources_json"])
            item["is_fallback"] = bool(item["is_fallback"])
            return item

    async def get_machines(self) -> List[Dict[str, Any]]:
        if self.use_postgres:
            return await self.pg.get_machines()
        async with aiosqlite.connect(self.sqlite_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM machines")
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_machine(self, machine_id: str) -> Optional[Dict[str, Any]]:
        if self.use_postgres:
            return await self.pg.get_machine(machine_id)
        async with aiosqlite.connect(self.sqlite_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM machines WHERE id = ?", (machine_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_machine_status(self, machine_id: str, status: str):
        if self.use_postgres:
            await self.pg.update_machine_status(machine_id, status)
        else:
            async with aiosqlite.connect(self.sqlite_path) as db:
                await db.execute("UPDATE machines SET status = ? WHERE id = ?", (status, machine_id))
                await db.commit()


db_manager = DatabaseManager()
