"""
P_311 Telemetry Dataset Generator
Generates a labeled, reproducible synthetic telemetry dataset based on the
11 kW induction motor physical simulator.
"""
import argparse
import csv
import json
import math
import os
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple


class TelemetryDatasetGenerator:
    """
    Deterministic telemetry generator for industrial induction motor fault diagnosis.
    Simulates:
      - 3-phase Squirrel-Cage Induction Motor (11 kW, 400V, 50Hz, 4-Pole)
      - Realistic electro-mechanical physics (slip curves, thermal lag, Gaussian noise)
      - Standard operating states and 6 distinct fault modes + normal baseline
    """

    FAULT_CLASSES = [
        "normal",
        "bearing_degradation",
        "motor_overheating",
        "motor_overload",
        "excessive_vibration",
        "low_pressure",
        "sensor_anomaly",
    ]

    def __init__(
        self,
        machine_id: str = "MOTOR-001",
        seed: int = 42,
        sampling_rate: float = 1.0,
        enable_dynamic_inertia: bool = True,
    ):
        self.machine_id = machine_id
        self.seed = seed
        self.sampling_rate = max(0.1, sampling_rate)
        self.dt = 1.0 / self.sampling_rate
        self.enable_dynamic_inertia = enable_dynamic_inertia

        # Set deterministic seeds
        random.seed(self.seed)

        # Baseline steady-state parameters
        self.temp_base = 51.5
        self.vib_base = 1.45
        self.curr_base = 8.8
        self.rpm_base = 1485.0
        self.volt_base = 230.0
        self.press_base = 4.2

        # State variables
        self.current_temp = self.temp_base
        self.current_vib = self.vib_base
        self.current_curr = self.curr_base
        self.current_rpm = self.rpm_base
        self.current_volt = self.volt_base
        self.current_press = self.press_base
        self.step_count = 0

    def reset_state(self):
        """Resets physical state back to initial baseline."""
        random.seed(self.seed)
        self.current_temp = self.temp_base
        self.current_vib = self.vib_base
        self.current_curr = self.curr_base
        self.current_rpm = self.rpm_base
        self.current_volt = self.volt_base
        self.current_press = self.press_base
        self.step_count = 0

    def generate_sample(
        self,
        fault_type: str,
        current_time: datetime,
    ) -> Dict[str, Any]:
        """Calculates a single telemetry sample given the active fault mode."""
        self.step_count += 1
        t = self.step_count * 0.1 * self.dt

        # Base physical noise
        noise_temp = random.gauss(0, 0.25)
        noise_vib = random.gauss(0, 0.08)
        noise_curr = random.gauss(0, 0.10)
        noise_rpm = random.gauss(0, 1.20)
        noise_volt = random.gauss(0, 0.80)
        noise_press = random.gauss(0, 0.03)

        # Nominal targets with continuous sinusoidal cycling
        target_temp = self.temp_base + 1.2 * math.sin(t * 0.2) + noise_temp
        target_vib = self.vib_base + 0.15 * math.sin(t * 0.5) + noise_vib
        target_curr = self.curr_base + 0.2 * math.sin(t * 0.15) + noise_curr
        target_rpm = self.rpm_base + 2.0 * math.sin(t * 0.1) + noise_rpm
        target_volt = self.volt_base + noise_volt
        target_press = self.press_base + noise_press
        operating_state = "running"
        severity = "normal"

        # Apply specific fault dynamics
        if fault_type == "normal":
            operating_state = "running"
            severity = "normal"

        elif fault_type == "bearing_degradation":
            # Vibration surges into Zone D, friction heats bearing progressively
            target_vib = 8.4 + random.gauss(0, 0.45)
            target_temp = 89.5 + random.gauss(0, 0.80)
            target_curr = 11.8 + random.gauss(0, 0.25)
            target_rpm = 1465.0 + random.gauss(0, 8.0)
            operating_state = "warning"
            severity = "critical" if target_vib >= 7.1 or target_temp >= 95.0 else "high"

        elif fault_type == "motor_overheating":
            # Severe thermal rise without high vibration
            target_temp = 104.2 + random.gauss(0, 1.10)
            target_vib = 2.1 + random.gauss(0, 0.10)
            target_curr = 9.3 + random.gauss(0, 0.15)
            target_rpm = 1478.0 + random.gauss(0, 1.5)
            operating_state = "alarm"
            severity = "critical" if target_temp >= 95.0 else "high"

        elif fault_type == "motor_overload":
            # Current surges over FLA, slip increases reducing RPM, thermal buildup
            target_curr = 15.8 + random.gauss(0, 0.50)
            target_rpm = 1395.0 + random.gauss(0, 4.0)
            target_temp = 88.0 + random.gauss(0, 0.70)
            target_vib = 3.6 + random.gauss(0, 0.20)
            operating_state = "alarm"
            severity = "critical" if target_curr >= 13.5 else "high"

        elif fault_type == "excessive_vibration":
            # Mechanical looseness / unbalance (high vibration without thermal buildup)
            target_vib = 11.2 + random.gauss(0, 0.70)
            target_curr = 10.1 + random.gauss(0, 0.20)
            target_temp = 62.0 + random.gauss(0, 0.40)
            operating_state = "warning"
            severity = "critical" if target_vib >= 7.1 else "high"

        elif fault_type == "low_pressure":
            # Auxiliary lubrication / cooling pressure drop
            target_press = 1.6 + random.gauss(0, 0.10)
            target_temp = 72.0 + random.gauss(0, 0.50)
            operating_state = "warning"
            severity = "critical" if target_press < 2.0 else "warning"

        elif fault_type == "sensor_anomaly":
            # Physical sensor failure / open circuit spike
            target_temp = 999.0
            operating_state = "sensor_error"
            severity = "warning"

        # Apply inertial smoothing or instantaneous response
        if self.enable_dynamic_inertia and fault_type != "sensor_anomaly":
            self.current_temp += 0.25 * (target_temp - self.current_temp)
            self.current_vib += 0.40 * (target_vib - self.current_vib)
            self.current_curr += 0.50 * (target_curr - self.current_curr)
            self.current_rpm += 0.50 * (target_rpm - self.current_rpm)
            self.current_volt += 0.60 * (target_volt - self.current_volt)
            self.current_press += 0.30 * (target_press - self.current_press)
        else:
            self.current_temp = target_temp
            self.current_vib = target_vib
            self.current_curr = target_curr
            self.current_rpm = target_rpm
            self.current_volt = target_volt
            self.current_press = target_press

        # Re-evaluate instantaneous severity if dynamic inertia is active
        if fault_type != "normal" and self.enable_dynamic_inertia:
            if fault_type == "bearing_degradation":
                severity = "critical" if (self.current_vib >= 7.1 or self.current_temp >= 95.0) else "high"
            elif fault_type == "motor_overheating":
                severity = "critical" if self.current_temp >= 95.0 else "high"
            elif fault_type == "motor_overload":
                severity = "critical" if self.current_curr >= 13.5 else "high"
            elif fault_type == "excessive_vibration":
                severity = "critical" if self.current_vib >= 7.1 else "high"
            elif fault_type == "low_pressure":
                severity = "critical" if self.current_press < 2.0 else "warning"

        return {
            "timestamp": current_time.isoformat(),
            "machine_id": self.machine_id,
            "temperature": round(self.current_temp, 2),
            "vibration": round(max(0.0, self.current_vib), 2),
            "current": round(max(0.0, self.current_curr), 2),
            "rpm": round(max(0.0, self.current_rpm), 1),
            "voltage": round(self.current_volt, 1),
            "pressure": round(max(0.0, self.current_press), 2),
            "operating_state": operating_state,
            "fault_label": fault_type,
            "severity": severity,
        }

    def generate_dataset(
        self,
        episode_plan: Optional[List[Tuple[str, int]]] = None,
        start_time: Optional[datetime] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generates a complete multi-episode labeled telemetry dataset.
        
        Default episode plan: 4,000 total samples (1.11 hours at 1 Hz).
        Includes normal baseline and repeated fault modes with normal recovery periods.
        """
        self.reset_state()
        if start_time is None:
            start_time = datetime(2026, 1, 15, 8, 0, 0, tzinfo=timezone.utc)

        if episode_plan is None:
            # Default balanced academic episode plan (4000 samples)
            episode_plan = [
                ("normal", 600),
                ("bearing_degradation", 400),
                ("normal", 200),
                ("motor_overheating", 400),
                ("normal", 200),
                ("motor_overload", 400),
                ("normal", 200),
                ("excessive_vibration", 400),
                ("normal", 200),
                ("low_pressure", 400),
                ("normal", 200),
                ("sensor_anomaly", 200),
                ("normal", 200),
            ]

        records: List[Dict[str, Any]] = []
        current_time = start_time
        episodes_meta = []
        class_counts: Dict[str, int] = {k: 0 for k in self.FAULT_CLASSES}
        severity_counts: Dict[str, int] = {"normal": 0, "warning": 0, "high": 0, "critical": 0}

        sample_idx = 0
        for ep_idx, (fault_mode, duration_samples) in enumerate(episode_plan, start=1):
            ep_start = sample_idx
            for _ in range(duration_samples):
                record = self.generate_sample(fault_mode, current_time)
                records.append(record)

                class_counts[record["fault_label"]] = class_counts.get(record["fault_label"], 0) + 1
                severity_counts[record["severity"]] = severity_counts.get(record["severity"], 0) + 1

                current_time += timedelta(seconds=self.dt)
                sample_idx += 1

            episodes_meta.append({
                "episode_index": ep_idx,
                "fault_label": fault_mode,
                "start_sample": ep_start,
                "end_sample": sample_idx - 1,
                "num_samples": duration_samples,
                "duration_seconds": round(duration_samples * self.dt, 2),
            })

        total_samples = len(records)
        class_distribution = {
            cls: {
                "count": count,
                "percentage": round((count / total_samples) * 100, 2)
            }
            for cls, count in class_counts.items()
        }

        severity_distribution = {
            sev: {
                "count": count,
                "percentage": round((count / total_samples) * 100, 2)
            }
            for sev, count in severity_counts.items()
        }

        metadata = {
            "dataset_name": "P_311 Synthetic Industrial Induction Motor Telemetry Dataset",
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "machine_id": self.machine_id,
            "random_seed": self.seed,
            "sampling_frequency_hz": self.sampling_rate,
            "time_step_seconds": self.dt,
            "total_samples": total_samples,
            "total_duration_seconds": round(total_samples * self.dt, 2),
            "fault_classes": self.FAULT_CLASSES,
            "class_distribution": class_distribution,
            "severity_distribution": severity_distribution,
            "simulation_parameters": {
                "motor_rating_kw": 11.0,
                "rated_voltage_v": 400.0,
                "rated_frequency_hz": 50.0,
                "poles": 4,
                "nominal_temperature_c": self.temp_base,
                "nominal_vibration_rms": self.vib_base,
                "nominal_current_a": self.curr_base,
                "nominal_rpm": self.rpm_base,
                "nominal_pressure_bar": self.press_base,
                "enable_dynamic_inertia": self.enable_dynamic_inertia,
                "noise_stdev": {
                    "temperature": 0.25,
                    "vibration": 0.08,
                    "current": 0.10,
                    "rpm": 1.20,
                    "voltage": 0.80,
                    "pressure": 0.03,
                }
            },
            "episodes": episodes_meta,
        }

        return records, metadata

    @staticmethod
    def export_csv(records: List[Dict[str, Any]], filepath: str) -> None:
        """Exports records to CSV format."""
        if not records:
            return
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        fieldnames = list(records[0].keys())
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

    @staticmethod
    def export_metadata(metadata: Dict[str, Any], filepath: str) -> None:
        """Exports metadata to JSON format."""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="P_311 Telemetry Dataset Generator")
    parser.add_argument("--output", "-o", default="data/synthetic_motor_telemetry.csv", help="Path to output CSV")
    parser.add_argument("--metadata", "-m", default="data/dataset_metadata.json", help="Path to output metadata JSON")
    parser.add_argument("--seed", "-s", type=int, default=42, help="Deterministic random seed")
    parser.add_argument("--sampling-rate", "-r", type=float, default=1.0, help="Sampling rate in Hz")
    parser.add_argument("--machine-id", default="MOTOR-001", help="Target machine identifier")
    parser.add_argument("--no-inertia", action="store_true", help="Disable physical EMA inertia (instantaneous steps)")
    args = parser.parse_args()

    generator = TelemetryDatasetGenerator(
        machine_id=args.machine_id,
        seed=args.seed,
        sampling_rate=args.sampling_rate,
        enable_dynamic_inertia=not args.no_inertia,
    )

    print(f"Generating telemetry dataset with seed={args.seed}, rate={args.sampling_rate} Hz...")
    records, metadata = generator.generate_dataset()

    generator.export_csv(records, args.output)
    generator.export_metadata(metadata, args.metadata)

    print(f"Dataset generated successfully:")
    print(f" - CSV Output:      {args.output} ({len(records)} rows)")
    print(f" - Metadata Output: {args.metadata}")
    print(f" - Fault Classes:   {', '.join(metadata['fault_classes'])}")
    for cls, info in metadata["class_distribution"].items():
        print(f"    * {cls:22s}: {info['count']:5d} ({info['percentage']:5.1f}%)")


if __name__ == "__main__":
    main()
