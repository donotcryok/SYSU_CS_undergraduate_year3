#!/usr/bin/env python3
"""
plot_benchmark.py — 读取 CSV 基准测试数据，生成专业学术风格图表

用法：
  python3 scripts/plot_benchmark.py [csv_path] [out_dir]

默认参数：
  csv_path = ../result/benchmark_results.csv
  out_dir  = ../img

输出（PNG）：
  - img/speedup_comparison.png      — 所有版本加速比对比
  - img/efficiency_comparison.png   — 所有版本并行效率对比
  - img/schedule_comparison.png     — parallel_for 三种调度策略对比
  - img/scalability.png             — 各版本随问题规模增长的 wall-clock 时间
"""

import csv
import sys
import os
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

# ── 样式配置（学术风格） ──────────────────────────────────
plt.rcParams.update({
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "legend.fontsize": 9,
    "lines.linewidth": 2.0,
    "lines.markersize": 7,
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "grid.alpha": 0.4,
})

THREADS_LIST = [1, 2, 4, 8, 16]

# ── 版本定义：version_key → (label, color, linestyle, marker) ──
VERSION_DEFS = [
    ("openmp",      "OpenMP",              "C0", "-",  "s"),
    ("pthread",     "Pthreads (native)",   "C1", "-",  "o"),
    ("pf_static",   "parallel_for static", "C2", "--", "^"),
    ("pf_cyclic",   "parallel_for cyclic", "C3", "-.", "D"),
    ("pf_dynamic",  "parallel_for dynamic","C4", ":",  "v"),
]


def load_csv(path):
    """加载 CSV，返回 {version_key: {size: {threads: [times]}}}"""
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(
            (row for row in f if not row.startswith("#")),
            fieldnames=None,
        )
        for row in reader:
            try:
                ver  = row["version"].strip()
                sz   = int(row["size"].strip())
                thr  = int(row["threads"].strip())
                t    = float(row["time_sec"].strip())
            except (ValueError, KeyError, TypeError):
                continue
            data[ver][sz][thr].append(t)

    # 取中位数
    def median_dict(d):
        out = {}
        for sz, thr_times in d.items():
            out[sz] = {}
            for thr, times in thr_times.items():
                out[sz][thr] = np.median(times)
        return out

    result = {}
    for ver, d in data.items():
        result[ver] = median_dict(d)
    return result


def compute_speedup(data):
    """加速比: T(1) / T(P)"""
    sp = {}
    for sz, thr_times in data.items():
        t1 = thr_times.get(1)
        if t1 is None or t1 == 0:
            continue
        sp[sz] = {thr: t1 / t for thr, t in thr_times.items()}
    return sp


def compute_efficiency(speedup):
    """并行效率: speedup / threads"""
    eff = {}
    for sz, thr_sp in speedup.items():
        eff[sz] = {thr: sp / thr for thr, sp in thr_sp.items()}
    return eff


def plot_speedup(all_data, sizes, out_dir):
    """各版本加速比对比（子图按 size 排列）"""
    n = len(sizes)
    ncols = min(n, 3)
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(6*ncols, 5*nrows), squeeze=False)
    axes = axes.flatten()

    for idx, sz in enumerate(sizes):
        ax = axes[idx]
        x = THREADS_LIST

        for vk, label, color, ls, mk in VERSION_DEFS:
            if vk not in all_data or sz not in all_data[vk]:
                continue
            y = [all_data[vk][sz].get(t, np.nan) for t in THREADS_LIST]
            ax.plot(x, y, marker=mk, color=color, linestyle=ls, label=label)

        # Ideal
        ax.plot(x, x, "k--", alpha=0.4, label="Ideal")

        ax.set_title(f"Grid {sz}×{sz}")
        ax.set_xlabel("Threads")
        ax.set_ylabel("Wall-clock Time (s)")
        ax.set_xticks(THREADS_LIST)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="upper left", fontsize=7)

    # 隐藏多余子图
    for idx in range(len(sizes), len(axes)):
        axes[idx].set_visible(False)

    fig.suptitle("Wall-clock Time Comparison Across Versions", fontsize=14, y=0.99)
    fig.tight_layout()
    fig.savefig(f"{out_dir}/speedup_comparison.png")
    plt.close(fig)
    print(f"  ✓ speedup_comparison saved to {out_dir}/")


def plot_efficiency(all_data, sizes, out_dir):
    """各版本并行效率对比"""
    eff_data = {}
    for vk in all_data:
        sp = compute_speedup(all_data[vk])
        eff_data[vk] = compute_efficiency(sp)

    n = len(sizes)
    ncols = min(n, 3)
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(6*ncols, 5*nrows), squeeze=False)
    axes = axes.flatten()

    for idx, sz in enumerate(sizes):
        ax = axes[idx]
        x = THREADS_LIST

        for vk, label, color, ls, mk in VERSION_DEFS:
            if vk not in eff_data or sz not in eff_data[vk]:
                continue
            y = [eff_data[vk][sz].get(t, np.nan) for t in THREADS_LIST]
            ax.plot(x, y, marker=mk, color=color, linestyle=ls, label=label)

        ax.axhline(y=1.0, color="gray", linestyle="--", alpha=0.4, label="Ideal")

        ax.set_title(f"Grid {sz}×{sz}")
        ax.set_xlabel("Threads")
        ax.set_ylabel("Parallel Efficiency")
        ax.set_xticks(THREADS_LIST)
        ax.set_ylim(bottom=0)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="upper right", fontsize=7)

    for idx in range(len(sizes), len(axes)):
        axes[idx].set_visible(False)

    fig.suptitle("Parallel Efficiency Comparison Across Versions", fontsize=14, y=0.99)
    fig.tight_layout()
    fig.savefig(f"{out_dir}/efficiency_comparison.png")
    plt.close(fig)
    print(f"  ✓ efficiency_comparison saved to {out_dir}/")


def plot_schedule_comparison(all_data, sizes, out_dir):
    """仅 parallel_for 三种调度策略的加速比对比"""
    pf_versions = [
        ("pf_static",  "parallel_for static",  "C2", "-",  "^"),
        ("pf_cyclic",  "parallel_for cyclic",  "C3", "-.", "D"),
        ("pf_dynamic", "parallel_for dynamic", "C4", ":",  "v"),
    ]

    n = len(sizes)
    ncols = min(n, 3)
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(6*ncols, 5*nrows), squeeze=False)
    axes = axes.flatten()

    for idx, sz in enumerate(sizes):
        ax = axes[idx]
        x = THREADS_LIST

        for vk, label, color, ls, mk in pf_versions:
            if vk not in all_data or sz not in all_data[vk]:
                continue
            sp = compute_speedup(all_data[vk])
            if sz not in sp:
                continue
            y = [sp[sz].get(t, np.nan) for t in THREADS_LIST]
            ax.plot(x, y, marker=mk, color=color, linestyle=ls, label=label)

        ax.plot(x, x, "k--", alpha=0.4, label="Ideal")
        ax.set_title(f"Grid {sz}×{sz}")
        ax.set_xlabel("Threads")
        ax.set_ylabel("Speedup")
        ax.set_xticks(THREADS_LIST)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="upper left", fontsize=8)

    for idx in range(len(sizes), len(axes)):
        axes[idx].set_visible(False)

    fig.suptitle("Schedule Strategy Comparison (parallel_for only)", fontsize=14, y=0.99)
    fig.tight_layout()
    fig.savefig(f"{out_dir}/schedule_comparison.png")
    plt.close(fig)
    print(f"  ✓ schedule_comparison saved to {out_dir}/")


def plot_scalability(all_data, sizes, out_dir):
    """各版本 Wall-clock 时间随问题规模的变化（固定线程数=4）"""
    fig, ax = plt.subplots(1, 1, figsize=(8, 5))

    ref_thr = 4  # 使用 4 线程展示规模扩展性
    x_pos = np.arange(len(sizes))

    for i, (vk, label, color, ls, mk) in enumerate(VERSION_DEFS):
        if vk not in all_data:
            continue
        y = []
        for sz in sizes:
            t = all_data[vk].get(sz, {}).get(ref_thr, np.nan)
            y.append(t)
        offset = (i - 2) * 0.12
        ax.bar(x_pos + offset, y, 0.12, color=color, label=label, alpha=0.85)

    ax.set_xticks(x_pos)
    ax.set_xticklabels([f"{sz}×{sz}" for sz in sizes])
    ax.set_xlabel("Problem Size")
    ax.set_ylabel(f"Wall-clock Time (s) with {ref_thr} threads")
    ax.set_title("Strong Scalability: Time vs Problem Size")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    fig.tight_layout()
    fig.savefig(f"{out_dir}/scalability.png")
    plt.close(fig)
    print(f"  ✓ scalability saved to {out_dir}/")


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "../result/benchmark_results.csv"
    out_dir  = sys.argv[2] if len(sys.argv) > 2 else "../img"

    print(f"Loading: {csv_path}")
    all_data = load_csv(csv_path)

    all_sizes = set()
    for vk, vd in all_data.items():
        all_sizes.update(vd.keys())
    sizes = sorted(all_sizes)

    if not sizes:
        print("ERROR: No data found!", file=sys.stderr)
        sys.exit(1)

    print(f"  Versions found: {list(all_data.keys())}")
    print(f"  Sizes: {sizes}")

    # 输出每个版本各规模的 wall-clock 时间摘要
    for vk in sorted(all_data.keys()):
        print(f"  [{vk}]")
        for sz in sorted(all_data[vk].keys()):
            ts = {t: f"{v:.4f}s" for t, v in all_data[vk][sz].items()}
            print(f"    sz={sz}: {ts}")

    plot_speedup(all_data, sizes, out_dir)
    plot_efficiency(all_data, sizes, out_dir)
    plot_schedule_comparison(all_data, sizes, out_dir)
    plot_scalability(all_data, sizes, out_dir)

    print("Done.")


if __name__ == "__main__":
    main()
