"""
P_311 Real Data Adapter & Telemetry Replay Script
Publishes historical CSV telemetry datasets through the Mosquitto MQTT broker into FastAPI and PostgreSQL.
Preserves the strict decoupled IoT architecture:
CSV/Real Data -> Replay Adapter -> MQTT -> Mosquitto -> FastAPI -> PostgreSQL -> Grafana.
"""
import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import paho.mqtt.client as mqtt

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [REPLAY] %(message)s")
logger = logging.getLogger("replay_adapter")

REQUIRED_CSV_FIELDS = [
    "timestamp",
    "machine_id",
    "temperature",
    "vibration",
    "current",
    "rpm",
    "voltage",
    "pressure",
    "operating_state",
]


def validate_csv_schema(filepath: str) -> List[str]:
    """Validates that the CSV contains all required industrial telemetry columns."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header:
            raise ValueError(f"CSV file is empty: {filepath}")

        missing = [field for field in REQUIRED_CSV_FIELDS if field not in header]
        if missing:
            raise ValueError(f"CSV schema validation failed! Missing required fields: {missing}")

    return header


def load_dataset(filepath: str) -> List[Dict[str, Any]]:
    """Loads CSV records into typed dictionaries."""
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append({
                "timestamp": row["timestamp"],
                "machine_id": row["machine_id"],
                "temperature": float(row["temperature"]),
                "vibration": float(row["vibration"]),
                "current": float(row["current"]),
                "rpm": float(row["rpm"]),
                "voltage": float(row["voltage"]),
                "pressure": float(row["pressure"]),
                "state": row.get("operating_state") or row.get("state", "running"),
                "fault_label": row.get("fault_label", "normal"),
                "severity": row.get("severity", "normal"),
            })
    return records


class TelemetryReplayer:
    def __init__(
        self,
        broker_host: str = settings.MQTT_BROKER_HOST,
        broker_port: int = settings.MQTT_BROKER_PORT,
        dry_run: bool = False,
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.dry_run = dry_run
        self.client: Optional[mqtt.Client] = None

        if not self.dry_run:
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=f"p311_replay_{int(time.time())}"
            )

    def connect(self):
        if not self.dry_run and self.client:
            logger.info("Connecting to MQTT broker at %s:%d...", self.broker_host, self.broker_port)
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()
            logger.info(" [✓] MQTT Replay Client connected")

    def disconnect(self):
        if not self.dry_run and self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info(" [✓] MQTT Replay Client disconnected")

    def publish_telemetry(self, machine_id: str, payload: Dict[str, Any]):
        topic = f"p311/machine/{machine_id}/telemetry"
        payload_str = json.dumps(payload)

        if self.dry_run:
            logger.info("[DRY-RUN] Would publish to %s: %s", topic, payload_str)
        else:
            self.client.publish(topic, payload_str, qos=0)
            logger.debug("Published to %s: %s", topic, payload_str)


def run_replay(
    csv_file: str,
    machine_id_override: Optional[str] = None,
    rate_multiplier: float = 1.0,
    loop: bool = False,
    realtime_timestamps: bool = True,
    dry_run: bool = False,
    max_records: Optional[int] = None,
):
    """Executes the dataset replay stream over MQTT."""
    logger.info("=" * 78)
    logger.info(" P_311 REAL DATA ADAPTER: TELEMETRY REPLAY STREAM")
    logger.info("=" * 78)
    logger.info("Input Dataset CSV   : %s", csv_file)
    logger.info("Rate Multiplier     : %sx (1.0 = 1 Hz real-time)", rate_multiplier)
    logger.info("Loop Continuous     : %s", loop)
    logger.info("Realtime Timestamps : %s", realtime_timestamps)
    logger.info("Dry Run Mode        : %s", dry_run)
    logger.info("=" * 78)

    validate_csv_schema(csv_file)
    records = load_dataset(csv_file)
    if max_records and max_records < len(records):
        records = records[:max_records]

    total_records = len(records)
    logger.info("Loaded %d validated telemetry records from %s", total_records, csv_file)

    replayer = TelemetryReplayer(dry_run=dry_run)
    replayer.connect()

    delay = 1.0 / rate_multiplier if rate_multiplier > 0 else 0.0

    try:
        iteration = 1
        while True:
            logger.info("Starting replay pass %d (%d records)...", iteration, total_records)
            for idx, rec in enumerate(records, start=1):
                target_machine = machine_id_override or rec["machine_id"]

                # Optionally rewrite timestamp to current UTC time for live Grafana tracking
                if realtime_timestamps:
                    rec["timestamp"] = datetime.now(timezone.utc).isoformat()

                payload = {
                    "machine_id": target_machine,
                    "timestamp": rec["timestamp"],
                    "temperature": rec["temperature"],
                    "vibration": rec["vibration"],
                    "current": rec["current"],
                    "rpm": rec["rpm"],
                    "voltage": rec["voltage"],
                    "pressure": rec["pressure"],
                    "state": rec["state"],
                }

                replayer.publish_telemetry(target_machine, payload)

                if idx % 50 == 0 or idx == total_records:
                    logger.info(
                        "Progress: [%5d/%5d] | Temp: %5.1f°C | Vib: %4.2f mm/s | Current: %4.1f A | State: %s",
                        idx, total_records, rec["temperature"], rec["vibration"], rec["current"], rec["state"]
                    )

                if delay > 0:
                    time.sleep(delay)

            logger.info("Pass %d completed.", iteration)
            if not loop:
                break
            iteration += 1

    except KeyboardInterrupt:
        logger.info("Replay interrupted by user.")
    finally:
        replayer.disconnect()
        logger.info("Replay stream completed successfully.")


def main():
    parser = argparse.ArgumentParser(description="P_311 Real Data Adapter / Telemetry Replay Script")
    parser.add_argument("--file", "-f", default="data/synthetic_motor_telemetry.csv", help="Path to input CSV dataset")
    parser.add_argument("--machine-id", "-m", default=None, help="Override machine identifier")
    parser.add_argument("--rate", "-r", type=float, default=1.0, help="Replay speed multiplier (e.g. 1.0 = real-time, 10.0 = 10x speed, 0.0 = max speed)")
    parser.add_argument("--loop", "-l", action="store_true", help="Continuously loop through the dataset")
    parser.add_argument("--dry-run", action="store_true", help="Print payloads without publishing to MQTT")
    parser.add_argument("--original-timestamps", action="store_true", help="Preserve original CSV timestamps instead of updating to current UTC")
    parser.add_argument("--max-records", "-n", type=int, default=None, help="Maximum number of records to replay")
    args = parser.parse_args()

    run_replay(
        csv_file=args.file,
        machine_id_override=args.machine_id,
        rate_multiplier=args.rate,
        loop=args.loop,
        realtime_timestamps=not args.original_timestamps,
        dry_run=args.dry_run,
        max_records=args.max_records,
    )


if __name__ == "__main__":
    main()
