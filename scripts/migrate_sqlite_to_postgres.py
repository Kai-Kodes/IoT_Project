"""
P_311 SQLite to PostgreSQL Migration Script
Migrates historical telemetry, fault events, diagnoses, and machine profiles from SQLite to PostgreSQL.
"""
import argparse
import asyncio
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import asyncpg

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [MIGRATION] %(message)s")
logger = logging.getLogger("migration")


async def migrate_data(sqlite_path: str):
    if not os.path.exists(sqlite_path):
        logger.warning("SQLite database not found at %s. Nothing to migrate.", sqlite_path)
        return

    logger.info("Opening SQLite database: %s", sqlite_path)
    sq_conn = sqlite3.connect(sqlite_path)
    sq_conn.row_factory = sqlite3.Row
    cursor = sq_conn.cursor()

    logger.info(
        "Connecting to PostgreSQL at %s:%d/%s (user: %s)...",
        settings.POSTGRES_HOST,
        settings.POSTGRES_PORT,
        settings.POSTGRES_DB,
        settings.POSTGRES_USER,
    )
    pg_conn = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        database=settings.POSTGRES_DB,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
    )

    try:
        # 1. Migrate Machines
        cursor.execute("SELECT * FROM machines")
        machines = cursor.fetchall()
        for m in machines:
            await pg_conn.execute("""
                INSERT INTO machines (id, name, type, rated_voltage, rated_current, rated_rpm, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE SET
                    status = EXCLUDED.status,
                    rated_voltage = EXCLUDED.rated_voltage,
                    rated_current = EXCLUDED.rated_current,
                    rated_rpm = EXCLUDED.rated_rpm;
            """, m["id"], m["name"], m["type"], float(m["rated_voltage"]), float(m["rated_current"]), float(m["rated_rpm"]), m["status"])
        logger.info(" [✓] Migrated %d machine profiles", len(machines))

        # 2. Migrate Telemetry
        cursor.execute("SELECT * FROM telemetry ORDER BY id ASC")
        telemetry_rows = cursor.fetchall()
        telemetry_records = []
        for r in telemetry_rows:
            ts_str = r["timestamp"]
            try:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)

            telemetry_records.append((
                r["machine_id"],
                dt,
                float(r["temperature"]),
                float(r["vibration"]),
                float(r["current"]),
                float(r["rpm"]),
                float(r["voltage"]),
                float(r["pressure"]),
                r["operating_state"]
            ))

        if telemetry_records:
            await pg_conn.executemany("""
                INSERT INTO telemetry (machine_id, timestamp, temperature, vibration, current, rpm, voltage, pressure, operating_state)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);
            """, telemetry_records)
        logger.info(" [✓] Migrated %d telemetry records", len(telemetry_records))

        # 3. Migrate Fault Events
        cursor.execute("SELECT * FROM fault_events ORDER BY timestamp ASC")
        fault_rows = cursor.fetchall()
        for f in fault_rows:
            ts_str = f["timestamp"]
            try:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)

            res_dt = None
            if f["resolved_at"]:
                try:
                    res_dt = datetime.fromisoformat(f["resolved_at"].replace("Z", "+00:00"))
                except Exception:
                    pass

            evidence = json.loads(f["sensor_evidence_json"]) if f["sensor_evidence_json"] else {}
            rules = json.loads(f["triggered_rules_json"]) if f["triggered_rules_json"] else []

            await pg_conn.execute("""
                INSERT INTO fault_events (id, machine_id, timestamp, fault_type, severity, confidence, sensor_evidence, triggered_rules, resolved_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO NOTHING;
            """, f["id"], f["machine_id"], dt, f["fault_type"], f["severity"], float(f["confidence"]), json.dumps(evidence), json.dumps(rules), res_dt)
        logger.info(" [✓] Migrated %d fault events", len(fault_rows))

        # 4. Migrate Diagnoses
        cursor.execute("SELECT * FROM diagnoses ORDER BY timestamp ASC")
        diag_rows = cursor.fetchall()
        for d in diag_rows:
            ts_str = d["timestamp"]
            try:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)

            await pg_conn.execute("""
                INSERT INTO diagnoses (
                    id, fault_event_id, machine_id, timestamp, fault_title, severity,
                    sensor_evidence, likely_causes, recommended_checks, corrective_actions,
                    confidence, uncertainty, knowledge_sources, raw_llm_response,
                    execution_time_ms, is_fallback
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                ON CONFLICT (id) DO NOTHING;
            """,
                d["id"],
                d["fault_event_id"],
                d["machine_id"],
                dt,
                d["fault_title"],
                d["severity"],
                d["sensor_evidence_json"],
                d["likely_causes_json"],
                d["recommended_checks_json"],
                d["corrective_actions_json"],
                float(d["confidence"]),
                d["uncertainty"],
                d["knowledge_sources_json"],
                d["raw_llm_response"],
                int(d["execution_time_ms"]),
                bool(d["is_fallback"])
            )
        logger.info(" [✓] Migrated %d diagnosis records", len(diag_rows))

        logger.info("MIGRATION COMPLETED SUCCESSFULLY!")

    finally:
        sq_conn.close()
        await pg_conn.close()


def main():
    parser = argparse.ArgumentParser(description="P_311 SQLite to PostgreSQL Migration")
    parser.add_argument("--sqlite-path", default=settings.DATABASE_PATH, help="Path to SQLite database")
    args = parser.parse_args()

    asyncio.run(migrate_data(args.sqlite_path))


if __name__ == "__main__":
    main()
