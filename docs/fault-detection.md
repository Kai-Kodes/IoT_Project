# Deterministic Fault Detection Specification

## 1. Detection Philosophy: Why Rules First?
In critical industrial engineering, safety systems are governed by international standards (such as **ISO 10816-3** for vibration severity and **IEC 60034-1** for electrical machine ratings). 

We explicitly do **not** use the LLM as the primary anomaly detector because:
1. **Determinism**: Rules execute with 100% mathematical consistency every time.
2. **Speed**: Rule evaluation takes under 0.05 milliseconds; LLM inference takes seconds.
3. **Auditing**: Safety engineers can trace every trip directly to a numerical physical threshold.
4. **Resilience**: The system can detect faults and trigger emergency procedures even if the LLM is powered down.

## 2. Threshold Matrix (`backend/app/core/thresholds.py`)

| Parameter | Normal Range | Warning / Alert | Critical / Trip | Standard Reference |
| :--- | :--- | :--- | :--- | :--- |
| **Vibration (RMS)** | 0.8 – 2.2 mm/s | > 2.8 mm/s (Zone C) | > 4.5 mm/s (Zone D), > 7.1 mm/s | **ISO 10816-3 Class II** |
| **Surface Temp** | 45 – 65 °C | > 75 °C | > 95 °C | **IEC Class F Insulation** |
| **Stator Current** | 8.5 – 9.2 A | > 11.5 A (~128% FLA) | > 13.5 A (150% FLA) | **Nameplate Rating (9.0 A)** |
| **Rotor Speed** | 1475 – 1490 RPM | < 1450 RPM | < 1420 RPM | **Nominal Slip Curves** |
| **Lube Pressure** | 3.8 – 4.5 bar | < 3.0 bar | < 2.0 bar | **Hydraulic Circuit Spec** |

## 3. Supported Fault Modes & Multi-Sensor Signatures

### 1. Bearing Degradation (`bearing_degradation`)
- **Physics**: Micro-pitting and raceway fluting induce high-frequency mechanical shock pulses, generating excessive vibration. Mechanical friction converts rotational kinetic energy into heat at the bearing cap.
- **Rule Signature**: `VIBRATION > 4.5 mm/s` AND `TEMPERATURE > 75.0 °C`.

### 2. Motor Thermal Overheating (`motor_overheating`)
- **Physics**: Cooling fan impeller damage or cowl fin blockage prevents forced convective heat transfer. Stator copper losses accumulate, causing rapid thermal climb while mechanical vibration remains nominal.
- **Rule Signature**: `TEMPERATURE > 85.0 °C` AND `VIBRATION <= 4.5 mm/s`.

### 3. Electrical Overload (`motor_overload`)
- **Physics**: Heavy mechanical process resistance forces the motor to produce higher torque. In an induction motor, higher torque demands greater rotor current, pulling stator current far above Full Load Amps (FLA) and increasing slip, which drags shaft RPM down.
- **Rule Signature**: `CURRENT > 11.5 A` AND `RPM < 1450 RPM`.

### 4. Excessive Vibration (`excessive_vibration`)
- **Physics**: Dynamic unbalance (debris on cooling fan) or mechanical base looseness ("soft foot") generates large cyclic centrifugal forces at 1X or 2X rotational speed without initial thermal friction.
- **Rule Signature**: `VIBRATION > 4.5 mm/s` AND `TEMPERATURE <= 75.0 °C`.

### 5. Low Lubrication / Cooling Pressure (`low_pressure`)
- **Physics**: Filter clogging, pump failure, or manifold leakage causes pressure drop across the forced oil lubrication jacket.
- **Rule Signature**: `PRESSURE < 3.0 bar`.

### 6. Sensor Anomaly (`sensor_anomaly`)
- **Physics**: Electrical thermocouple break (open circuit) or transmitter failure causes an instantaneous jump to physically impossible values (e.g., 999°C).
- **Rule Signature**: Sensor reading outside physical envelope (`TEMP < -20°C` or `TEMP > 160°C`).
