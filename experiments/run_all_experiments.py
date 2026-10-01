"""
P_311 Master Experiment Runner
Executes the complete reproducible dataset generation and academic evaluation pipeline:
1. Generates labeled synthetic motor telemetry dataset (CSV + Metadata JSON)
2. Evaluates deterministic fault detector (Accuracy, Precision, Recall, F1, Confusion Matrix)
3. Evaluates vector RAG retrieval relevance (Hit@1, Hit@3, MRR, Similarity)
4. Generates publication-ready figures in experiments/plots/
"""
import argparse
import os
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from simulator.dataset_generator import TelemetryDatasetGenerator
from experiments.evaluate_detector import evaluate_dataset, print_evaluation_summary
from experiments.evaluate_rag import evaluate_rag, print_rag_summary
from experiments.plot_generator import (
    plot_sensor_time_series,
    plot_sensor_distributions,
    plot_class_distribution,
    plot_confusion_matrix,
)
import json
import pandas as pd


def run_pipeline(
    seed: int = 42,
    sampling_rate: float = 1.0,
    output_csv: str = "data/synthetic_motor_telemetry.csv",
    output_meta: str = "data/dataset_metadata.json",
    detector_metrics_file: str = "experiments/detector_metrics.json",
    rag_metrics_file: str = "experiments/rag_metrics.json",
    plots_dir: str = "experiments/plots",
):
    start_total = time.time()
    print("=" * 80)
    print(" P_311 REPRODUCIBLE DATASET GENERATION & EVALUATION PIPELINE")
    print("=" * 80)
    print(f"Random Seed        : {seed}")
    print(f"Sampling Frequency : {sampling_rate} Hz (dt = {1.0/sampling_rate:.2f}s)")
    print(f"Target Machine ID  : MOTOR-001 (11 kW Induction Motor)")
    print(f"Dataset Output     : {output_csv}")
    print(f"Metadata Output    : {output_meta}")
    print(f"Plots Directory    : {plots_dir}")
    print("=" * 80)

    # 1. Dataset Generation
    print("\n[STEP 1/4] Generating Labeled Telemetry Dataset from Motor Simulator...")
    t0 = time.time()
    generator = TelemetryDatasetGenerator(
        machine_id="MOTOR-001",
        seed=seed,
        sampling_rate=sampling_rate,
        enable_dynamic_inertia=True,
    )
    records, metadata = generator.generate_dataset()
    generator.export_csv(records, output_csv)
    generator.export_metadata(metadata, output_meta)
    print(f" [✓] Generated {len(records):,} samples across 7 fault classes in {time.time() - t0:.2f}s")

    # 2. Deterministic Detector Evaluation
    print("\n[STEP 2/4] Evaluating Deterministic Fault Detection Engine...")
    t0 = time.time()
    detector_results, _, _ = evaluate_dataset(output_csv)
    os.makedirs(os.path.dirname(os.path.abspath(detector_metrics_file)), exist_ok=True)
    with open(detector_metrics_file, "w", encoding="utf-8") as f:
        json.dump(detector_results, f, indent=2)
    print_evaluation_summary(detector_results)
    print(f" [✓] Detector evaluation completed in {time.time() - t0:.2f}s")

    # 3. RAG Retrieval Evaluation
    print("\n[STEP 3/4] Evaluating Local RAG Semantic Retrieval Relevance...")
    t0 = time.time()
    rag_results = evaluate_rag(top_k=3)
    os.makedirs(os.path.dirname(os.path.abspath(rag_metrics_file)), exist_ok=True)
    with open(rag_metrics_file, "w", encoding="utf-8") as f:
        json.dump(rag_results, f, indent=2)
    print_rag_summary(rag_results)
    print(f" [✓] RAG evaluation completed in {time.time() - t0:.2f}s")

    # 4. Generate Visualization Plots
    print("\n[STEP 4/4] Generating Academic Visualizations (300 DPI)...")
    t0 = time.time()
    os.makedirs(plots_dir, exist_ok=True)
    df = pd.read_csv(output_csv)
    plot_sensor_time_series(df, metadata, os.path.join(plots_dir, "sensor_time_series.png"))
    plot_sensor_distributions(df, os.path.join(plots_dir, "normal_vs_fault_distributions.png"))
    plot_class_distribution(metadata, os.path.join(plots_dir, "class_distribution.png"))
    plot_confusion_matrix(detector_results, os.path.join(plots_dir, "confusion_matrix.png"))
    print(f" [✓] All 4 plots generated in {time.time() - t0:.2f}s")

    elapsed = time.time() - start_total
    print("\n" + "=" * 80)
    print(f" EXPERIMENT PIPELINE COMPLETE ({elapsed:.2f}s total)")
    print("=" * 80)
    print(f"Key Findings to report to Mentors / Examiners:")
    print(f" 1. Dataset Size        : {len(records):,} records (4,000 seconds / ~66.7 minutes of 1 Hz data)")
    print(f" 2. Fault Classes       : 7 classes (1 normal + 6 mechanical/electrical/instrumentation faults)")
    print(f" 3. Detector Accuracy   : {detector_results['overall_accuracy'] * 100:.2f}%")
    print(f" 4. Detector Macro F1   : {detector_results['macro_metrics']['f1_score'] * 100:.2f}%")
    print(f" 5. RAG Retrieval Hit@1 : {rag_results['hit_rate_at_1_pct']:.2f}% (MRR: {rag_results['mean_reciprocal_rank']:.4f})")
    print(f" 6. Generated Figures   : {plots_dir}/")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="P_311 Master Experiment Runner")
    parser.add_argument("--seed", "-s", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--rate", "-r", type=float, default=1.0, help="Sampling rate in Hz")
    parser.add_argument("--csv", default="data/synthetic_motor_telemetry.csv", help="Output CSV path")
    parser.add_argument("--meta", default="data/dataset_metadata.json", help="Output metadata JSON path")
    parser.add_argument("--plots", default="experiments/plots", help="Plots output directory")
    args = parser.parse_args()

    run_pipeline(
        seed=args.seed,
        sampling_rate=args.rate,
        output_csv=args.csv,
        output_meta=args.meta,
        plots_dir=args.plots,
    )


if __name__ == "__main__":
    main()
