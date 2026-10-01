"""
P_311 Asynchronous MQTT Consumer & Event Dispatcher
Consumes real-time telemetry from Mosquitto, validates schemas, evaluates faults,
triggers RAG-LLM diagnosis, and broadcasts to live SSE streams.
"""
import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional, Set
import paho.mqtt.client as mqtt

from backend.app.core.config import settings
from backend.app.db.database import db_manager
from backend.app.detection.fault_detector import fault_detector
from backend.app.diagnosis.diagnosis_engine import diagnosis_engine
from backend.app.models.schemas import TelemetryIn

logger = logging.getLogger("mqtt_consumer")


class MQTTService:
    def __init__(self):
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"backend_consumer_{int(time.time())}"
        )
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self.is_connected = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # SSE Subscriber queues for real-time telemetry streaming
        self.sse_queues: Set[asyncio.Queue] = set()

        # Telemetry counter for retention trimming
        self.msg_count = 0

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.is_connected = True
            logger.info("Backend connected to Mosquitto MQTT Broker (%s:%d)", settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT)
            client.subscribe(settings.MQTT_TELEMETRY_TOPIC_SUB, qos=1)
            logger.info("Subscribed to telemetry topic pattern: %s", settings.MQTT_TELEMETRY_TOPIC_SUB)
        else:
            self.is_connected = False
            logger.error("Failed to connect to MQTT broker, return code: %d", rc)

    def _on_disconnect(self, client, userdata, disconnect_flags, rc, properties=None):
        self.is_connected = False
        logger.warning("Disconnected from MQTT broker (rc: %s)", rc)

    def _on_message(self, client, userdata, msg):
        """Thread callback from paho-mqtt client loop."""
        try:
            payload_str = msg.payload.decode("utf-8")
            data = json.loads(payload_str)

            # Schedule async processing in FastAPI's main event loop
            if self.loop and self.loop.is_running():
                asyncio.run_coroutine_threadsafe(self.process_telemetry_message(data), self.loop)
        except Exception as e:
            logger.error("Error decoding or queuing MQTT message: %s", e)

    async def process_telemetry_message(self, raw_data: Dict[str, Any]):
        """Validates telemetry, detects faults, persists data, and broadcasts SSE."""
        try:
            # Pydantic schema validation
            telemetry_obj = TelemetryIn(**raw_data)
            telemetry = telemetry_obj.model_dump()
        except Exception as ve:
            logger.warning("Rejected invalid telemetry payload: %s | Error: %s", raw_data, ve)
            return

        # 1. Insert into SQLite
        try:
            await db_manager.insert_telemetry(telemetry)
            self.msg_count += 1
            if self.msg_count % 100 == 0:
                await db_manager.purge_old_telemetry()
        except Exception as dbe:
            logger.error("DB insert error: %s", dbe)

        # 2. Evaluate Fault Rules
        fault_event, is_new_event = fault_detector.evaluate_telemetry(telemetry)

        # 3. If a new fault emerged or changed severity, trigger Diagnosis Engine
        diagnosis = None
        if fault_event and is_new_event:
            logger.info("--> FAULT DETECTED: %s [%s] on %s", fault_event["fault_type"], fault_event["severity"], fault_event["machine_id"])
            await db_manager.insert_fault_event(fault_event)

            # Run diagnosis in background task to avoid blocking telemetry flow
            asyncio.create_task(self._run_async_diagnosis(fault_event))

        elif fault_event is None and is_new_event:
            # Fault was resolved back to normal
            logger.info("--> MACHINE RETURNED TO NORMAL: %s", telemetry["machine_id"])
            await db_manager.update_machine_status(telemetry["machine_id"], "healthy")

        # 4. Broadcast live telemetry and active status to SSE queues
        event_packet = {
            "type": "telemetry",
            "data": telemetry,
            "active_fault": fault_event,
            "status": "fault" if fault_event else "healthy"
        }
        await self.broadcast_sse(event_packet)

    async def _run_async_diagnosis(self, fault_event: Dict[str, Any]):
        try:
            diag = await diagnosis_engine.diagnose(fault_event)
            # Broadcast diagnosis notification over SSE
            await self.broadcast_sse({
                "type": "diagnosis",
                "data": diag
            })
        except Exception as e:
            logger.error("Error in background diagnosis generation: %s", e)

    async def broadcast_sse(self, packet: Dict[str, Any]):
        """Dispatches an event payload to all connected SSE clients."""
        if not self.sse_queues:
            return
        payload = json.dumps(packet)
        dead_queues = set()
        for q in self.sse_queues:
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                dead_queues.add(q)
            except Exception:
                dead_queues.add(q)
        for dq in dead_queues:
            self.sse_queues.discard(dq)

    def publish_command(self, machine_id: str, command_dict: Dict[str, Any]) -> bool:
        """Sends remote control commands to simulator via MQTT."""
        topic = f"{settings.MQTT_COMMAND_TOPIC_PREFIX}/{machine_id}/command"
        try:
            payload = json.dumps(command_dict)
            info = self.client.publish(topic, payload, qos=1)
            info.wait_for_publish(timeout=2.0)
            logger.info("Published command to %s: %s", topic, payload)
            return True
        except Exception as e:
            logger.error("Failed to publish command to MQTT: %s", e)
            return False

    def start(self):
        try:
            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, keepalive=settings.MQTT_KEEPALIVE)
            self.client.loop_start()
            logger.info("MQTT Client loop started in background thread.")
        except Exception as e:
            logger.warning("Could not connect to Mosquitto on startup: %s. Will retry automatically.", e)

    def stop(self):
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT Client stopped cleanly.")
        except Exception as e:
            logger.error("Error stopping MQTT client: %s", e)


mqtt_service = MQTTService()
