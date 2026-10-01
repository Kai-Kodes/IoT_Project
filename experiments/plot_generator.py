"""
P_311 Experiment Plot Generator
Generates academic visualizations:
1. Multi-sensor time series with annotated fault episodes
2. Sensor value distributions across normal vs fault classes
3. Labeled fault-class dataset distribution
4. Annotated confusion matrix heatmap for deterministic detector
"""
import argparse
import json
import os
import sys
from typing import Dict, List
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Matplotlib styling for clean academic publications
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 14,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


def plot_sensor_time_series(df: pd.DataFrame, metadata: Dict, output_path: str):
    """Plots multi-panel sensor telemetry over time with shaded fault episodes."""
    fig, axes = plt.subplots(4, 1, figsize=(14, 10), sharex=True)

    time_seconds = np.arange(len(df))

    # Color palette for fault episodes
    fault_colors = {
        "normal": "#10b981",              # Emerald green
        "bearing_degradation": "#ef4444",  # Red
        "motor_overheating": "#f97316",    # Orange
        "motor_overload": "#8b5cf6",       # Purple
        "excessive_vibration": "#ec4899",  # Pink
        "low_pressure": "#06b6d4",         # Cyan
        "sensor_anomaly": "#eab308",       # Yellow
    }

    # Panel 1: Temperature
    axes[0].plot(time_seconds, df["temperature"], color="#dc2626", lw=1.2, label="Temperature (°C)")
    axes[0].axhline(75.0, color="#f59e0b", linestyle="--", alpha=0.7, label="Warning (75°C)")
    axes[0].axhline(95.0, color="#b91c1c", linestyle="--", alpha=0.7, label="Critical (95°C)")
    axes[0].set_ylabel("Temp (°C)")
    axes[0].set_ylim(40, 115)
    axes[0].grid(True, linestyle=":", alpha=0.6)
    axes[0].legend(loc="upper right", framealpha=0.9)

    # Panel 2: Vibration
    axes[1].plot(time_seconds, df["vibration"], color="#2563eb", lw=1.2, label="Vibration (mm/s RMS)")
    axes[1].axhline(4.5, color="#f59e0b", linestyle="--", alpha=0.7, label="ISO Zone C Alarm (4.5 mm/s)")
    axes[1].axhline(7.1, color="#b91c1c", linestyle="--", alpha=0.7, label="ISO Zone D Trip (7.1 mm/s)")
    axes[1].set_ylabel("Vib (mm/s)")
    axes[1].set_ylim(0, 14)
    axes[1].grid(True, linestyle=":", alpha=0.6)
    axes[1].legend(loc="upper right", framealpha=0.9)

    # Panel 3: Current & Speed
    axes[2].plot(time_seconds, df["current"], color="#7c3aed", lw=1.2, label="Stator Current (A)")
    axes[2].axhline(9.0, color="#10b981", linestyle=":", alpha=0.7, label="Rated FLA (9.0 A)")
    axes[2].axhline(11.5, color="#f59e0b", linestyle="--", alpha=0.7, label="Warning (11.5 A)")
    axes[2].axhline(13.5, color="#b91c1c", linestyle="--", alpha=0.7, label="Alarm Trip (13.5 A)")
    axes[2].set_ylabel("Current (A)")
    axes[2].set_ylim(6, 18)
    axes[2].grid(True, linestyle=":", alpha=0.6)
    axes[2].legend(loc="upper right", framealpha=0.9)

    # Panel 4: Lubrication Pressure
    axes[3].plot(time_seconds, df["pressure"], color="#0891b2", lw=1.2, label="Aux Pressure (bar)")
    axes[3].axhline(3.0, color="#f59e0b", linestyle="--", alpha=0.7, label="Warning Low (3.0 bar)")
    axes[3].axhline(2.0, color="#b91c1c", linestyle="--", alpha=0.7, label="Critical Low (2.0 bar)")
    axes[3].set_ylabel("Pressure (bar)")
    axes[3].set_xlabel("Time (seconds)")
    axes[3].set_ylim(1.0, 5.0)
    axes[3].grid(True, linestyle=":", alpha=0.6)
    axes[3].legend(loc="upper right", framealpha=0.9)

    # Shade and annotate episodes across all panels
    episodes = metadata.get("episodes", [])
    for ep in episodes:
        label = ep["fault_label"]
        start = ep["start_sample"]
        end = ep["end_sample"]
        if label != "normal":
            color = fault_colors.get(label, "#94a3b8")
            for ax in axes:
                ax.axvspan(start, end, color=color, alpha=0.15)
            # Label on top panel
            mid = (start + end) / 2
            axes[0].text(
                mid, 107, label.replace("_", "\n"),
                fontsize=7, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.2", facecolor=color, alpha=0.3, edgecolor=color)
            )

    fig.suptitle("P_311 Multi-Sensor Telemetry Time Series Across Fault Episodes", fontsize=13, y=0.99)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f" [✓] Saved: {output_path}")


def plot_sensor_distributions(df: pd.DataFrame, output_path: str):
    """Plots sensor value distributions across normal vs fault conditions."""
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))

    # Filter out extreme sensor anomaly outlier (999°C) for clean visual distribution of physical modes
    df_filtered = df[df["fault_label"] != "sensor_anomaly"]
    classes = [
        "normal",
        "bearing_degradation",
        "motor_overheating",
        "motor_overload",
        "excessive_vibration",
        "low_pressure",
    ]
    labels_clean = [c.replace("_", "\n") for c in classes]

    # 1. Temperature Distribution
    data_temp = [df_filtered[df_filtered["fault_label"] == c]["temperature"] for c in classes]
    bp1 = axes[0, 0].boxplot(data_temp, patch_artist=True, tick_labels=labels_clean, showfliers=False)
    for patch in bp1["boxes"]:
        patch.set_facecolor("#fee2e2")
        patch.set_edgecolor("#dc2626")
    axes[0, 0].axhline(75.0, color="#f59e0b", linestyle="--", label="Warning (75°C)")
    axes[0, 0].set_title("Stator Surface Temperature by Condition")
    axes[0, 0].set_ylabel("Temperature (°C)")
    axes[0, 0].grid(True, linestyle=":", alpha=0.6)
    axes[0, 0].legend(loc="upper left")

    # 2. Vibration Distribution
    data_vib = [df_filtered[df_filtered["fault_label"] == c]["vibration"] for c in classes]
    bp2 = axes[0, 1].boxplot(data_vib, patch_artist=True, tick_labels=labels_clean, showfliers=False)
    for patch in bp2["boxes"]:
        patch.set_facecolor("#dbeafe")
        patch.set_edgecolor("#2563eb")
    axes[0, 1].axhline(4.5, color="#f59e0b", linestyle="--", label="ISO Zone C (4.5)")
    axes[0, 1].axhline(7.1, color="#b91c1c", linestyle="--", label="ISO Zone D (7.1)")
    axes[0, 1].set_title("Vibration Velocity RMS by Condition")
    axes[0, 1].set_ylabel("Vibration (mm/s RMS)")
    axes[0, 1].grid(True, linestyle=":", alpha=0.6)
    axes[0, 1].legend(loc="upper left")

    # 3. Current Distribution
    data_curr = [df_filtered[df_filtered["fault_label"] == c]["current"] for c in classes]
    bp3 = axes[1, 0].boxplot(data_curr, patch_artist=True, tick_labels=labels_clean, showfliers=False)
    for patch in bp3["boxes"]:
        patch.set_facecolor("#f3e8ff")
        patch.set_edgecolor("#7c3aed")
    axes[1, 0].axhline(11.5, color="#f59e0b", linestyle="--", label="Warning FLA (11.5A)")
    axes[1, 0].set_title("Motor Line Current by Condition")
    axes[1, 0].set_ylabel("Current (A)")
    axes[1, 0].grid(True, linestyle=":", alpha=0.6)
    axes[1, 0].legend(loc="upper left")

    # 4. Pressure Distribution
    data_press = [df_filtered[df_filtered["fault_label"] == c]["pressure"] for c in classes]
    bp4 = axes[1, 1].boxplot(data_press, patch_artist=True, tick_labels=labels_clean, showfliers=False)
    for patch in bp4["boxes"]:
        patch.set_facecolor("#cffafe")
        patch.set_edgecolor("#0891b2")
    axes[1, 1].axhline(3.0, color="#f59e0b", linestyle="--", label="Warning Low (3.0 bar)")
    axes[1, 1].set_title("Lubrication / Cooling Pressure by Condition")
    axes[1, 1].set_ylabel("Pressure (bar)")
    axes[1, 1].grid(True, linestyle=":", alpha=0.6)
    axes[1, 1].legend(loc="upper right")

    fig.suptitle("P_311 Sensor Distributions: Normal vs Fault Operating Modes", fontsize=13, y=0.99)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f" [✓] Saved: {output_path}")


def plot_class_distribution(metadata: Dict, output_path: str):
    """Plots bar chart of dataset class balance and percentages."""
    class_dist = metadata.get("class_distribution", {})
    classes = list(class_dist.keys())
    counts = [info["count"] for info in class_dist.values()]
    percentages = [info["percentage"] for info in class_dist.values()]

    colors = [
        "#10b981",  # normal
        "#ef4444",  # bearing
        "#f97316",  # overheating
        "#8b5cf6",  # overload
        "#ec4899",  # vibration
        "#06b6d4",  # pressure
        "#eab308",  # sensor
    ]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.bar([c.replace("_", "\n") for c in classes], counts, color=colors, edgecolor="#334155", width=0.6)

    # Annotate counts and percentages on top of each bar
    for bar, count, pct in zip(bars, counts, percentages):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height + 35,
            f"{count:,}\n({pct:.1f}%)",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
        )

    ax.set_title("P_311 Labeled Telemetry Dataset Class Distribution", fontsize=12, pad=15)
    ax.set_ylabel("Sample Count")
    ax.set_ylim(0, max(counts) * 1.22)
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    total_samples = metadata.get("total_samples", sum(counts))
    duration_s = metadata.get("total_duration_seconds", total_samples)
    ax.text(
        0.98, 0.93,
        f"Total Samples: {total_samples:,}\nSampling Rate: {metadata.get('sampling_frequency_hz', 1.0)} Hz\nDuration: {duration_s/60:.1f} minutes",
        transform=ax.transAxes,
        ha="right", va="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8fafc", edgecolor="#cbd5e1")
    )

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f" [✓] Saved: {output_path}")


def plot_confusion_matrix(metrics: Dict, output_path: str):
    """Plots annotated confusion matrix heatmap."""
    cm = np.array(metrics.get("confusion_matrix", []))
    classes = metrics.get("classes", [])
    labels_clean = [c.replace("_", "\n") for c in classes]

    fig, ax = plt.subplots(figsize=(9, 8))

    # Log-scale or normalized color mapping for clear visibility across large vs small classes
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel("Sample Count", rotation=-90, va="bottom")

    ax.set(
        xticks=np.arange(cm.shape[1]),
        yticks=np.arange(cm.shape[0]),
        xticklabels=labels_clean,
        yticklabels=labels_clean,
        title="P_311 Deterministic Fault Detector Confusion Matrix",
        ylabel="True Ground-Truth Class",
        xlabel="Detector Predicted Class",
    )

    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Annotate each cell with count and percentage
    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        row_total = cm[i].sum()
        for j in range(cm.shape[1]):
            val = cm[i, j]
            pct = (val / row_total) * 100 if row_total > 0 else 0
            text_color = "white" if val > thresh else "black"
            text = f"{val}\n({pct:.1f}%)" if val > 0 else "0"
            ax.text(
                j, i, text,
                ha="center", va="center",
                color=text_color,
                fontsize=8,
                fontweight="bold" if i == j else "normal"
            )

    accuracy = metrics.get("overall_accuracy", 0.0) * 100
    macro_f1 = metrics.get("macro_metrics", {}).get("f1_score", 0.0) * 100
    ax.text(
        0.5, -0.22,
        f"Overall Accuracy: {accuracy:.2f}%  |  Macro F1-Score: {macro_f1:.2f}%  |  Total Samples: {cm.sum():,}",
        transform=ax.transAxes,
        ha="center", fontsize=10, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#f1f5f9", edgecolor="#cbd5e1")
    )

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f" [✓] Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate P_311 Experiment Plots")
    parser.add_argument("--dataset", "-d", default="data/synthetic_motor_telemetry.csv", help="Dataset CSV path")
    parser.add_argument("--metadata", "-m", default="data/dataset_metadata.json", help="Dataset metadata JSON path")
    parser.add_argument("--metrics", "-e", default="experiments/detector_metrics.json", help="Detector metrics JSON path")
    parser.add_argument("--plots-dir", "-p", default="experiments/plots", help="Output plots directory")
    args = parser.parse_args()

    os.makedirs(args.plots_dir, exist_ok=True)

    print("Loading experiment artifacts...")
    df = pd.read_csv(args.dataset)
    with open(args.metadata, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    with open(args.metrics, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    print("Generating academic plots in experiments/plots/...")
    plot_sensor_time_series(df, metadata, os.path.join(args.plots_dir, "sensor_time_series.png"))
    plot_sensor_distributions(df, os.path.join(args.plots_dir, "normal_vs_fault_distributions.png"))
    plot_class_distribution(metadata, os.path.join(args.plots_dir, "class_distribution.png"))
    plot_confusion_matrix(metrics, os.path.join(args.plots_dir, "confusion_matrix.png"))

    print("All 4 experiment plots generated successfully!")


if __name__ == "__main__":
    main()
