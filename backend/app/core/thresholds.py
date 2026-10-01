"""
P_311 Centralized Fault Detection Thresholds
Conforms to ISO 10816-3 standards and industrial induction motor specifications.
"""
from pydantic import BaseModel


class DetectionThresholds(BaseModel):
    # Vibration (Velocity RMS mm/s) - ISO 10816-3 Class II
    VIBRATION_ZONE_B_MAX: float = 2.8   # Normal limit
    VIBRATION_ZONE_C_ALARM: float = 4.5 # Warning threshold
    VIBRATION_ZONE_D_TRIP: float = 7.1  # Dangerous threshold

    # Stator / Bearing Surface Temperature (°C)
    TEMPERATURE_WARNING: float = 75.0
    TEMPERATURE_ALARM: float = 85.0
    TEMPERATURE_CRITICAL: float = 95.0

    # Motor Line Current (Amperes) - Rated: 9.0 A
    CURRENT_RATED: float = 9.0
    CURRENT_WARNING: float = 11.5       # ~128% Full Load Amps
    CURRENT_ALARM: float = 13.5         # 150% Full Load Amps

    # Motor Shaft Speed (RPM) - Rated: 1485 RPM
    RPM_RATED: float = 1485.0
    RPM_MIN_OPERATIONAL: float = 1450.0
    RPM_OVERLOAD_SLIP: float = 1420.0

    # Auxiliary Cooling & Lubrication Pressure (bar)
    PRESSURE_NOMINAL_MIN: float = 3.8
    PRESSURE_NOMINAL_MAX: float = 4.5
    PRESSURE_WARNING_LOW: float = 3.0
    PRESSURE_CRITICAL_LOW: float = 2.0

    # Sensor Plausibility / Physical Anomaly Limits
    TEMP_PHYSICAL_MIN: float = -20.0
    TEMP_PHYSICAL_MAX: float = 160.0
    VIBRATION_PHYSICAL_MIN: float = 0.0
    VIBRATION_PHYSICAL_MAX: float = 40.0
    CURRENT_PHYSICAL_MIN: float = 0.0
    CURRENT_PHYSICAL_MAX: float = 45.0
    PRESSURE_PHYSICAL_MIN: float = 0.0
    PRESSURE_PHYSICAL_MAX: float = 12.0
    VOLTAGE_PHYSICAL_MIN: float = 100.0
    VOLTAGE_PHYSICAL_MAX: float = 500.0


thresholds = DetectionThresholds()
