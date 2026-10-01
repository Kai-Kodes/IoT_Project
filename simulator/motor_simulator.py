"""
P_311 Industrial Motor Telemetry Simulator
Simulates a 3-phase induction motor with realistic physical state transitions,
Gaussian sensor noise, and deterministic fault modes.
"""
import json
import logging
import math
import random
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import paho.mqtt.client as mqtt

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [SIMULATOR] %(message)s")
logger = logging.getLogger("motor_simulator")


class MotorSimulator:
    def __init__(
        self,
        machine_id: str = "MOTOR-001",
        broker_host: str = "localhost",
        broker_port: int = 1883,
        publish_interval: float = 1.0,
    ):
        self.machine_id = machine_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.publish_interval = publish_interval

        # Telemetry topic
        self.telemetry_topic = f"p311/machine/{self.machine_id}/telemetry"
        self.status_topic = f"p311/machine/{self.machine_id}/status"
        self.command_topic = f"p311/machine/{self.machine_id}/command"

        # Operational state
        self.running = True
        self.active_fault: Optional[str] = None
        self.fault_start_time: Optional[float] = None
        self.step_count = 0

        # Physical state variables (smoothed transition targets)
        self.temp_base = 51.5
        self.vib_base = 1.45
        self.curr_base = 8.8
        self.rpm_base = 1485.0
        self.volt_base = 230.0
        self.press_base = 4.2

        # Current actual values (lagged thermal / mechanical dynamics)
        self.current_temp = self.temp_base
        self.current_vib = self.vib_base
        self.current_curr = self.curr_base
        self.current_rpm = self.rpm_base
        self.current_volt = self.volt_base
        self.current_press = self.press_base

        # Setup MQTT client
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"sim_{self.machine_id}_{int(time.time())}"
        )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        # Set Last Will and Testament (LWT)
        lwt_payload = json.dumps({"machine_id": self.machine_id, "state": "offline", "reason": "abrupt_disconnect"})
        self.client.will_set(self.status_topic, lwt_payload, qos=1, retain=True)

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            logger.info("Connected to MQTT Broker %s:%d", self.broker_host, self.broker_port)
            client.subscribe(self.command_topic, qos=1)
            logger.info("Subscribed to command topic: %s", self.command_topic)
            self.publish_status("running")
        else:
            logger.error("Failed to connect to MQTT broker, rc=%d", rc)

    def _on_disconnect(self, client, userdata, disconnect_flags, rc, properties=None):
        logger.warning("Disconnected from MQTT broker, rc=%d", rc)

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            logger.info("Received command on %s: %s", msg.topic, payload)
            cmd = payload.get("command") or payload.get("action")

            if cmd == "inject_fault":
                fault_type = payload.get("fault_type", "bearing_degradation")
                self.inject_fault(fault_type)
            elif cmd in ("reset", "clear_fault"):
                self.reset_fault()
            elif cmd == "stop":
                self.running = False
                self.publish_status("stopped")
            elif cmd == "start":
                self.running = True
                self.publish_status("running")
            else:
                logger.warning("Unrecognized command: %s", cmd)
        except Exception as e:
            logger.error("Error processing MQTT command: %s", e)

    def publish_status(self, state: str):
        payload = {
            "machine_id": self.machine_id,
            "state": state,
            "active_fault": self.active_fault,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.client.publish(self.status_topic, json.dumps(payload), qos=1, retain=True)

    def inject_fault(self, fault_type: str):
        logger.info("--> INJECTING FAULT: %s", fault_type)
        self.active_fault = fault_type
        self.fault_start_time = time.time()
        self.publish_status(f"fault_{fault_type}")

    def reset_fault(self):
        logger.info("--> RESETTING MACHINE TO NORMAL MODE")
        self.active_fault = None
        self.fault_start_time = None
        self.publish_status("running")

    def _calculate_next_telemetry(self) -> Dict[str, Any]:
        self.step_count += 1
        t = self.step_count * 0.1

        # Base noise
        noise_temp = random.gauss(0, 0.25)
        noise_vib = random.gauss(0, 0.08)
        noise_curr = random.gauss(0, 0.1)
        noise_rpm = random.gauss(0, 1.2)
        noise_volt = random.gauss(0, 0.8)
        noise_press = random.gauss(0, 0.03)

        target_temp = self.temp_base + 1.2 * math.sin(t * 0.2) + noise_temp
        target_vib = self.vib_base + 0.15 * math.sin(t * 0.5) + noise_vib
        target_curr = self.curr_base + 0.2 * math.sin(t * 0.15) + noise_curr
        target_rpm = self.rpm_base + 2.0 * math.sin(t * 0.1) + noise_rpm
        target_volt = self.volt_base + noise_volt
        target_press = self.press_base + noise_press
        operating_state = "running"

        # Apply Fault Dynamics
        if self.active_fault == "bearing_degradation":
            # Vibration surges rapidly, friction heats bearing progressively, current rises slightly
            target_vib = 8.4 + random.gauss(0, 0.45)
            target_temp = 89.5 + random.gauss(0, 0.8)
            target_curr = 11.8 + random.gauss(0, 0.25)
            target_rpm = 1465.0 + random.gauss(0, 8.0) # RPM flutter
            operating_state = "warning"

        elif self.active_fault == "motor_overheating":
            # Thermal runaway without major vibration change
            target_temp = 104.2 + random.gauss(0, 1.1)
            target_vib = 2.1 + random.gauss(0, 0.1)
            target_curr = 9.3 + random.gauss(0, 0.15)
            target_rpm = 1478.0 + random.gauss(0, 1.5)
            operating_state = "alarm"

        elif self.active_fault == "motor_overload":
            # Current surges over FLA, slip increases reducing RPM, temperature climbs
            target_curr = 15.8 + random.gauss(0, 0.5)
            target_rpm = 1395.0 + random.gauss(0, 4.0)
            target_temp = 88.0 + random.gauss(0, 0.7)
            target_vib = 3.6 + random.gauss(0, 0.2)
            operating_state = "alarm"

        elif self.active_fault == "excessive_vibration":
            # Mechanical looseness / severe unbalance
            target_vib = 11.2 + random.gauss(0, 0.7)
            target_curr = 10.1 + random.gauss(0, 0.2)
            target_temp = 62.0 + random.gauss(0, 0.4)
            operating_state = "warning"

        elif self.active_fault == "low_pressure":
            # Hydraulic cooling / lubrication drop
            target_press = 1.6 + random.gauss(0, 0.1)
            target_temp = 72.0 + random.gauss(0, 0.5)
            operating_state = "warning"

        elif self.active_fault == "sensor_anomaly":
            # Implausible sensor spike / open circuit
            target_temp = 999.0
            operating_state = "sensor_error"

        # Smooth exponential moving average for realistic thermal and mechanical inertia
        # (except instantaneous sensor anomaly)
        if self.active_fault == "sensor_anomaly":
            self.current_temp = target_temp
        else:
            self.current_temp += 0.25 * (target_temp - self.current_temp)

        self.current_vib += 0.4 * (target_vib - self.current_vib)
        self.current_curr += 0.5 * (target_curr - self.current_curr)
        self.current_rpm += 0.5 * (target_rpm - self.current_rpm)
        self.current_volt += 0.6 * (target_volt - self.current_volt)
        self.current_press += 0.3 * (target_press - self.current_press)

        return {
            "machine_id": self.machine_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": round(self.current_temp, 2),
            "vibration": round(max(0.0, self.current_vib), 2),
            "current": round(max(0.0, self.current_curr), 2),
            "rpm": round(max(0.0, self.current_rpm), 1),
            "voltage": round(self.current_volt, 1),
            "pressure": round(max(0.0, self.current_press), 2),
            "state": operating_state,
        }

    def start(self):
        logger.info("Starting Motor Simulator for %s", self.machine_id)
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            logger.error("Could not connect to MQTT broker at %s:%d: %s", self.broker_host, self.broker_port, e)
            logger.warning("Ensure Mosquitto is running.")
            return

        try:
            while True:
                if self.running:
                    telemetry = self._calculate_next_telemetry()
                    payload = json.dumps(telemetry)
                    self.client.publish(self.telemetry_topic, payload, qos=0)
                    logger.debug("Published: %s", payload)
                time.sleep(self.publish_interval)
        except KeyboardInterrupt:
            logger.info("Stopping simulator gracefully...")
        finally:
            self.publish_status("stopped")
            self.client.loop_stop()
            self.client.disconnect()


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    sim = MotorSimulator(broker_host=host)
    sim.start()
