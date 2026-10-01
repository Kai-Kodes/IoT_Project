"""
P_311 Fault Detector Evaluation Script
Evaluates the deterministic rule-based fault detection engine against the labeled telemetry dataset.
Computes accuracy, precision, recall, F1-score, and confusion matrix.
"""
import argparse
import csv
import json
import os
import sys
from typing import Any, Dict, List, Tuple
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.detection.fault_detector import FaultDetector


FAULT_CLASSES = [
    "normal",
    "bearing_degradation",
    "motor_overheating",
    "motor_overload",
    "excessive_vibration",
    "low_pressure",
    "sensor_anomaly",
]


def evaluate_dataset(csv_path: str) -> Dict[str, Any]:
    """Runs the deterministic fault detector over the labeled dataset."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset file not found: {csv_path}")

    detector = FaultDetector()

    y_true: List[str] = []
    y_pred: List[str] = []
    rows: List[Dict[str, Any]] = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
            telemetry = {
                "machine_id": row["machine_id"],
                "timestamp": row["timestamp"],
                "temperature": float(row["temperature"]),
                "vibration": float(row["vibration"]),
                "current": float(row["current"]),
                "rpm": float(row["rpm"]),
                "pressure": float(row["pressure"]),
                "voltage": float(row["voltage"]),
            }
            fault_event, _ = detector.evaluate_telemetry(telemetry)

            predicted_label = fault_event["fault_type"] if fault_event else "normal"
            y_true.append(row["fault_label"])
            y_pred.append(predicted_label)

    # Calculate metrics
    accuracy = float(accuracy_score(y_true, y_pred))

    macro_p, macro_r, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=FAULT_CLASSES, average="macro", zero_division=0
    )
    weighted_p, weighted_r, weighted_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=FAULT_CLASSES, average="weighted", zero_division=0
    )

    per_class_p, per_class_r, per_class_f1, per_class_sup = precision_recall_fscore_support(
        y_true, y_pred, labels=FAULT_CLASSES, average=None, zero_division=0
    )

    cm = confusion_matrix(y_true, y_pred, labels=FAULT_CLASSES)

    per_class_metrics = {}
    for i, cls in enumerate(FAULT_CLASSES):
        per_class_metrics[cls] = {
            "precision": round(float(per_class_p[i]), 4),
            "recall": round(float(per_class_r[i]), 4),
            "f1_score": round(float(per_class_f1[i]), 4),
            "support": int(per_class_sup[i]),
        }

    results = {
        "dataset_path": csv_path,
        "total_samples": len(y_true),
        "overall_accuracy": round(accuracy, 4),
        "macro_metrics": {
            "precision": round(float(macro_p), 4),
            "recall": round(float(macro_r), 4),
            "f1_score": round(float(macro_f1), 4),
        },
        "weighted_metrics": {
            "precision": round(float(weighted_p), 4),
            "recall": round(float(weighted_r), 4),
            "f1_score": round(float(weighted_f1), 4),
        },
        "per_class_metrics": per_class_metrics,
        "confusion_matrix": cm.tolist(),
        "classes": FAULT_CLASSES,
    }

    return results, y_true, y_pred


def print_evaluation_summary(results: Dict[str, Any]) -> None:
    """Prints a structured academic summary table."""
    print("=" * 78)
    print(" P_311 DETERMINISTIC FAULT DETECTOR EVALUATION REPORT")
    print("=" * 78)
    print(f"Total Evaluated Samples : {results['total_samples']}")
    print(f"Overall Accuracy        : {results['overall_accuracy'] * 100:.2f}%")
    print(f"Macro F1-Score          : {results['macro_metrics']['f1_score'] * 100:.2f}%")
    print(f"Weighted F1-Score       : {results['weighted_metrics']['f1_score'] * 100:.2f}%")
    print("-" * 78)
    print(f"{'Class Name':<24} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<10}")
    print("-" * 78)
    for cls, m in results["per_class_metrics"].items():
        print(
            f"{cls:<24} "
            f"{m['precision'] * 100:6.2f}%     "
            f"{m['recall'] * 100:6.2f}%     "
            f"{m['f1_score'] * 100:6.2f}%     "
            f"{m['support']:<10}"
        )
    print("-" * 78)
    print("Confusion Matrix (Rows: Ground Truth, Cols: Predicted):")
    cm = np.array(results["confusion_matrix"])
    header = "          " + " ".join(f"{c[:7]:>8}" for c in results["classes"])
    print(header)
    for i, row in enumerate(cm):
        row_str = f"{results['classes'][i][:9]:<10}" + " ".join(f"{val:8d}" for val in row)
        print(row_str)
    print("=" * 78)


def main():
    parser = argparse.ArgumentParser(description="Evaluate Deterministic Fault Detector")
    parser.add_argument("--dataset", "-d", default="data/synthetic_motor_telemetry.csv", help="Path to input CSV")
    parser.add_argument("--output", "-o", default="experiments/detector_metrics.json", help="Path to output JSON")
    args = parser.parse_args()

    results, _, _ = evaluate_dataset(args.dataset)
    print_evaluation_summary(results)

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Metrics saved to: {args.output}")


if __name__ == "__main__":
    main()
