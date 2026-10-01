"""
Integration Tests: MQTT End-to-End Publish and Ingestion Loop
"""
import asyncio
import json
import time
import pytest
import paho.mqtt.client as mqtt

from backend.app.core.config import settings
from backend.app.db.database import db_manager
from backend.app.mqtt.consumer import mqtt_service


@pytest.mark.asyncio
async def test_mqtt_pubsub_pipeline():
    await db_manager.init_db()

    # Ensure backend MQTT service is connected and listening to the current event loop
    loop = asyncio.get_running_loop()
    mqtt_service.set_event_loop(loop)
    mqtt_service.start()
    await asyncio.sleep(0.3)

    # Create test publisher
    pub_client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id=f"test_pub_{int(time.time())}"
    )
    pub_client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT)
    pub_client.loop_start()

    test_timestamp = f"2026-09-30T11:59:{int(time.time() * 1000) % 1000:03d}Z"
    test_telemetry = {
        "machine_id": "MOTOR-001",
        "timestamp": test_timestamp,
        "temperature": 53.1,
        "vibration": 1.5,
        "current": 8.9,
        "rpm": 1484.0,
        "voltage": 230.1,
        "pressure": 4.22,
        "state": "running"
    }

    try:
        topic = f"p311/machine/MOTOR-001/telemetry"
        info = pub_client.publish(topic, json.dumps(test_telemetry), qos=1)
        info.wait_for_publish(timeout=2.0)

        # Allow network broker delivery & backend DB insertion
        await asyncio.sleep(0.8)

        # Check that database contains the record
        recent = await db_manager.get_recent_telemetry("MOTOR-001", limit=10)
        matched = any(r["timestamp"] == test_timestamp for r in recent)
        assert matched, f"Published telemetry with timestamp {test_timestamp} was not found in SQLite"
    finally:
        pub_client.loop_stop()
        pub_client.disconnect()
        mqtt_service.stop()
