"""
P_311 Deterministic Fault Detection Engine
Evaluates incoming telemetry against standardized industrial thresholds without ML opacity.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from backend.app.core.thresholds import thresholds


class FaultDetector:
    def __init__(self):
        # Keeps track of the currently active fault type per machine for stateful debouncing
        self.active_faults: Dict[str, Optional[Dict[str, Any]]] = {}

    def evaluate_telemetry(self, telemetry: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Evaluates a telemetry sample.
        Returns:
            (fault_event, is_new_event)
            - If no fault: (None, False)
            - If ongoing unchanged fault: (fault_event, False)
            - If new fault or severity escalation: (fault_event, True)
        """
        machine_id = telemetry["machine_id"]
        temp = float(telemetry["temperature"])
        vib = float(telemetry["vibration"])
        curr = float(telemetry["current"])
        rpm = float(telemetry["rpm"])
        press = float(telemetry["pressure"])
        volt = float(telemetry["voltage"])

        sensor_evidence: Dict[str, float] = {
            "temperature": temp,
            "vibration": vib,
            "current": curr,
            "rpm": rpm,
            "pressure": press,
            "voltage": volt
        }
        triggered_rules: List[str] = []
        fault_type: Optional[str] = None
        severity: str = "normal"
        confidence: float = 0.0

        # Rule 1: Sensor Plausibility / Physical Anomaly Check
        if (
            temp < thresholds.TEMP_PHYSICAL_MIN or temp > thresholds.TEMP_PHYSICAL_MAX or
            vib < thresholds.VIBRATION_PHYSICAL_MIN or vib > thresholds.VIBRATION_PHYSICAL_MAX or
            curr < thresholds.CURRENT_PHYSICAL_MIN or curr > thresholds.CURRENT_PHYSICAL_MAX or
            press < thresholds.PRESSURE_PHYSICAL_MIN or press > thresholds.PRESSURE_PHYSICAL_MAX or
            volt < thresholds.VOLTAGE_PHYSICAL_MIN or volt > thresholds.VOLTAGE_PHYSICAL_MAX
        ):
            fault_type = "sensor_anomaly"
            severity = "warning"
            confidence = 0.98
            triggered_rules.append("SENSOR_OUT_OF_PHYSICAL_RANGE")
            if temp > thresholds.TEMP_PHYSICAL_MAX or temp < thresholds.TEMP_PHYSICAL_MIN:
                triggered_rules.append("TEMPERATURE_SENSOR_DISCONNECTED_OR_FAILED")
            if press < thresholds.PRESSURE_PHYSICAL_MIN or press > thresholds.PRESSURE_PHYSICAL_MAX:
                triggered_rules.append("PRESSURE_TRANSMITTER_SIGNAL_FAULT")

        # Rule 2: Bearing Degradation (High vibration coupled with thermal friction rise)
        elif vib > thresholds.VIBRATION_ZONE_C_ALARM and temp > thresholds.TEMPERATURE_WARNING:
            fault_type = "bearing_degradation"
            severity = "critical" if (vib >= thresholds.VIBRATION_ZONE_D_TRIP or temp >= thresholds.TEMPERATURE_CRITICAL) else "high"
            confidence = 0.92
            triggered_rules.append(f"HIGH_VIBRATION_{'ZONE_D_TRIP' if vib >= thresholds.VIBRATION_ZONE_D_TRIP else 'ZONE_C_ALARM'}")
            triggered_rules.append("HIGH_TEMPERATURE_FRICTION")
            if curr > thresholds.CURRENT_WARNING:
                triggered_rules.append("ELEVATED_STATOR_CURRENT")

        # Rule 3: Electrical Overload (Current exceeding FLA + rotor slip drop)
        elif curr > thresholds.CURRENT_WARNING and rpm < thresholds.RPM_MIN_OPERATIONAL:
            fault_type = "motor_overload"
            severity = "critical" if curr >= thresholds.CURRENT_ALARM else "high"
            confidence = 0.94
            triggered_rules.append("EXCESSIVE_STATOR_CURRENT_OVER_FLA")
            triggered_rules.append("ROTOR_SPEED_DROP_HIGH_SLIP")
            if temp > thresholds.TEMPERATURE_ALARM:
                triggered_rules.append("SECONDARY_OVERLOAD_THERMAL_RISE")

        # Rule 4: Motor Overheating (Thermal rise without high vibration or high overload current)
        elif temp > thresholds.TEMPERATURE_ALARM and vib <= thresholds.VIBRATION_ZONE_C_ALARM:
            fault_type = "motor_overheating"
            severity = "critical" if temp >= thresholds.TEMPERATURE_CRITICAL else "high"
            confidence = 0.89
            triggered_rules.append(f"{'CRITICAL_TEMPERATURE_HOTSPOT' if temp >= thresholds.TEMPERATURE_CRITICAL else 'HIGH_STATOR_TEMPERATURE'}")
            triggered_rules.append("COOLING_OR_VENTILATION_INADEQUACY")

        # Rule 5: Excessive Vibration / Mechanical Looseness (High vibration without thermal buildup)
        elif vib > thresholds.VIBRATION_ZONE_C_ALARM:
            fault_type = "excessive_vibration"
            severity = "critical" if vib >= thresholds.VIBRATION_ZONE_D_TRIP else "high"
            confidence = 0.87
            triggered_rules.append(f"HIGH_VIBRATION_{'ZONE_D_DANGER' if vib >= thresholds.VIBRATION_ZONE_D_TRIP else 'ZONE_C_ALARM'}")
            triggered_rules.append("MECHANICAL_UNBALANCE_OR_LOOSENESS")

        # Rule 6: Low Lubrication / Cooling Pressure
        elif press < thresholds.PRESSURE_WARNING_LOW:
            fault_type = "low_pressure"
            severity = "critical" if press < thresholds.PRESSURE_CRITICAL_LOW else "warning"
            confidence = 0.91
            triggered_rules.append("AUXILIARY_LUBRICATION_PRESSURE_LOW")

        # State transition analysis:
        prev_fault = self.active_faults.get(machine_id)

        if not fault_type:
            # Everything is normal
            if prev_fault is not None:
                # Fault was resolved!
                self.active_faults[machine_id] = None
                return None, True  # Indicates resolution transition
            return None, False

        # If a fault condition exists
        fault_id = f"FAULT-{uuid.uuid4().hex[:8].upper()}"
        fault_event = {
            "id": fault_id,
            "machine_id": machine_id,
            "timestamp": telemetry["timestamp"],
            "fault_type": fault_type,
            "severity": severity,
            "confidence": confidence,
            "sensor_evidence": sensor_evidence,
            "triggered_rules": triggered_rules
        }

        if prev_fault is None:
            # New fault emerged!
            self.active_faults[machine_id] = fault_event
            return fault_event, True
        elif prev_fault["fault_type"] != fault_type or prev_fault["severity"] != severity:
            # Fault type or severity changed/escalated
            self.active_faults[machine_id] = fault_event
            return fault_event, True
        else:
            # Ongoing fault without state change: reuse original fault_id
            fault_event["id"] = prev_fault["id"]
            return fault_event, False


fault_detector = FaultDetector()
