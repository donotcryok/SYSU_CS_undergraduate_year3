#!/usr/bin/env python3
"""plot_results.py – Generate execution-time and speedup charts for the lab report."""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULT_CSV = os.path.join(BASE_DIR, "result", "benchmark_metrics.csv")
IMG_DIR   = os.path.join(BASE_DIR, "img")

os.makedirs(IMG_DIR, exist_ok=True)

# Read data
df = pd.read_csv(RESULT_CSV)
df = df.dropna(subset=["time_sec"])

# Style
plt.rcParams.update({
    "figure.dpi": 150,
    "font.size": 13,
    "axes.titlesize": 15,
    "axes.labelsize": 14,
    "legend.fontsize": 12,
    "lines.linewidth": 2.2,
    "lines.markersize": 8,
})

COLOURS = {"omp": "#2196F3", "pth": "#F44336", "mpi": "#4CAF50"}
MARKERS = {"omp": "o", "pth": "s", "mpi": "D"}
LABELS  = {"omp": "OpenMP", "pth": "Pthreads", "mpi": "MPI"}


def plot_time(ds_tag, ds_label):
    """Execution time vs threads for a single dataset."""
    sub = df[df["dataset"] == ds_tag]
    fig, ax = plt.subplots(figsize=(9, 6))
    for fw in ["omp", "pth", "mpi"]:
        s = sub[sub["framework"] == fw].sort_values("threads")
        ax.plot(s["threads"], s["time_sec"],
                color=COLOURS[fw], marker=MARKERS[fw],
                label=LABELS[fw], linewidth=2.2, markersize=9)
    ax.set_xlabel("Number of Threads / Processes")
    ax.set_ylabel("Execution Time (s)")
    ax.set_title(f"Execution Time — {ds_label} Dataset")
    ax.set_xticks([1, 2, 4, 8, 12, 16])
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = os.path.join(IMG_DIR, f"time_{ds_tag}.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def plot_speedup(ds_tag, ds_label):
    """Speedup vs threads for a single dataset."""
    sub = df[df["dataset"] == ds_tag]
    fig, ax = plt.subplots(figsize=(9, 6))

    # Ideal linear speedup
    xs = np.array([1, 2, 4, 8, 12, 16])
    ax.plot(xs, xs, "--", color="gray", alpha=0.6, linewidth=1.5, label="$y=x$ (Ideal)")

    for fw in ["omp", "pth", "mpi"]:
        s = sub[sub["framework"] == fw].sort_values("threads")
        t1 = s[s["threads"] == 1]["time_sec"].values[0]
        speedups = t1 / s["time_sec"].values
        ax.plot(s["threads"], speedups,
                color=COLOURS[fw], marker=MARKERS[fw],
                label=LABELS[fw], linewidth=2.2, markersize=9)

    ax.set_xlabel("Number of Threads / Processes")
    ax.set_ylabel("Speedup $S = T_1 / T_P$")
    ax.set_title(f"Speedup — {ds_label} Dataset")
    ax.set_xticks([1, 2, 4, 8, 12, 16])
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    path = os.path.join(IMG_DIR, f"speedup_{ds_tag}.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved {path}")


def main():
    for ds_tag, ds_label in [("flower", "Flower (930 vertices)"), ("mouse", "Mouse (525 vertices)")]:
        plot_time(ds_tag, ds_label)
        plot_speedup(ds_tag, ds_label)
    print("\nAll charts generated.")


if __name__ == "__main__":
    main()
