#!/usr/bin/env python3
"""
plot_benchmark.py — Lab 10: CUDA 并行矩阵乘法 自动化基准测试与可视化

功能:
  1. 循环调用编译好的 matrixmul_b{N} 可执行文件, 收集全组合测试数据
  2. 生成三张专业图表:
     - fig1_execution_time.png  : 执行时间对比折线图 (对数纵轴)
     - fig2_throughput.png      : 有效吞吐量柱状图 (GFLOPS)
     - fig3_speedup.png         : 以 Naive 2D 为基线的加速比柱状图

用法:
  cd /root/ParallelComputingLab/lab10
  venv/bin/python src/plot_benchmark.py

依赖:
  Python 3.x, matplotlib, numpy
"""

import subprocess
import sys
import os
import re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# ================================================================
# 配置
# ================================================================

SRC_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR   = os.path.dirname(SRC_DIR)
IMG_DIR    = os.path.join(ROOT_DIR, "img")
CSV_FILE   = os.path.join(SRC_DIR, "benchmark_results.csv")

# 参数扫描范围
MATRIX_SIZES  = [128, 256, 512, 1024, 2048]
BLOCK_SIZES   = [8, 16, 32]
KERNEL_TYPES  = {0: "naive_2d", 1: "naive_1d", 2: "shared_tiled"}

WARMUP = 3
REPEAT = 10

# 图表颜色方案
COLORS = {
    0: "#E74C3C",  # naive_2d   — 红色
    1: "#3498DB",  # naive_1d   — 蓝色
    2: "#2ECC71",  # shared_tiled — 绿色
}

KERNEL_LABELS = {
    0: "Naive 2D",
    1: "Naive 1D",
    2: "Shared Tiled",
}

# ================================================================
# 步骤 1: 运行所有测试组合, 收集数据
# ================================================================

def run_benchmarks():
    """调用 make run-csv 或逐个执行, 收集数据到 CSV"""
    print("=" * 64)
    print("  Lab 10: CUDA Matrix Multiplication — Auto Benchmark")
    print("=" * 64)

    # 先确保可执行文件存在 (调用 make all)
    print("\n[1/4] Compiling CUDA sources...")
    result = subprocess.run(
        ["make", "all"],
        cwd=SRC_DIR,
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"[ERROR] Compilation failed:\n{result.stderr}")
        sys.exit(1)
    print("       Compilation OK.")

    # 逐配置运行
    print("\n[2/4] Running benchmarks...")
    rows = []
    header = "m,n,k,kernel_name,block_size,time_ms,verified"

    total_configs = len(MATRIX_SIZES) * len(BLOCK_SIZES) * len(KERNEL_TYPES)
    current = 0

    for sz in MATRIX_SIZES:
        for bs in BLOCK_SIZES:
            exe = os.path.join(SRC_DIR, f"matrixmul_b{bs}")
            for kt, kt_name in KERNEL_TYPES.items():
                current += 1
                cmd = [exe, str(sz), str(sz), str(sz), str(kt),
                       str(WARMUP), str(REPEAT)]
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True, text=True, timeout=120
                    )
                    if result.returncode != 0:
                        print(f"  [{current:3d}/{total_configs}] "
                              f"FAIL: sz={sz} bs={bs} {kt_name}")
                        print(f"         stderr: {result.stderr.strip()}")
                        # 插入一条失败记录
                        rows.append(f"{sz},{sz},{sz},{kt_name},{bs},N/A,0")
                    else:
                        line = result.stdout.strip().split("\n")[-1]
                        rows.append(line)
                        parts = line.split(",")
                        verified = parts[-1]
                        time_ms = parts[-2]
                        status = "✓" if verified == "1" else "✗"
                        print(f"  [{current:3d}/{total_configs}] "
                              f"sz={sz:4d} bs={bs:2d} {kt_name:12s} "
                              f"t={time_ms:>10s}ms {status}")
                except subprocess.TimeoutExpired:
                    print(f"  [{current:3d}/{total_configs}] "
                          f"TIMEOUT: sz={sz} bs={bs} {kt_name}")
                    rows.append(f"{sz},{sz},{sz},{kt_name},{bs},N/A,0")

    # 保存 CSV
    print(f"\n[3/4] Saving results to {CSV_FILE}...")
    os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
    with open(CSV_FILE, "w") as f:
        f.write(header + "\n")
        for row in rows:
            f.write(row + "\n")
    print(f"       {len(rows)} data rows written.")

    return rows, header


# ================================================================
# 步骤 2: 解析数据
# ================================================================

def parse_data(rows):
    """将 CSV 行解析为结构化字典"""
    data = {}  # key: (size, block_size, kernel) -> time_ms

    for row in rows:
        parts = row.strip().split(",")
        if len(parts) != 7:
            continue
        m, n, k, kt_name, bs_str, time_str, verified_str = parts
        if time_str == "N/A" or verified_str != "1":
            continue
        try:
            time_ms = float(time_str)
        except ValueError:
            continue
        sz   = int(m)
        bs   = int(bs_str)
        # 根据 kernel_name 反查 kernel_type
        kt = None
        for k, v in KERNEL_TYPES.items():
            if v == kt_name:
                kt = k
                break
        if kt is None:
            continue
        data[(sz, bs, kt)] = time_ms

    return data


# ================================================================
# 步骤 3: 绘图
# ================================================================

def plot_execution_time(data):
    """
    fig1_execution_time.png
    折线图 — 每个 Block Size 一张子图, 横轴=矩阵规模, 纵轴=执行时间 (对数)
    """
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
    fig.suptitle("CUDA Matrix Multiplication — Execution Time Comparison",
                 fontsize=15, fontweight="bold", y=1.01)

    for idx, bs in enumerate(BLOCK_SIZES):
        ax = axes[idx]
        for kt, label in KERNEL_LABELS.items():
            times = []
            valid_sizes = []
            for sz in MATRIX_SIZES:
                key = (sz, bs, kt)
                if key in data:
                    times.append(data[key])
                    valid_sizes.append(sz)
            ax.plot(valid_sizes, times, marker="o", linewidth=2,
                    markersize=7, color=COLORS[kt], label=label)

        ax.set_title(f"Block Size = {bs}×{bs}", fontsize=12, fontweight="bold")
        ax.set_xlabel("Matrix Dimension (m = n = k)")
        ax.set_ylabel("Execution Time (ms)")
        ax.set_yscale("log")
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.legend(fontsize=9)
        ax.set_xticks(MATRIX_SIZES)

    plt.tight_layout()
    path = os.path.join(IMG_DIR, "fig1_execution_time.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"       Saved: {path}")


def plot_throughput(data):
    """
    fig2_throughput.png
    分组柱状图 — 横轴=矩阵规模, 每组柱=3种Kernel, 纵轴=GFLOPS
    GFLOPS = 2 * m * n * k / (time_ms * 1e6)   (每个MAC算2次浮点操作)
    每个 Block Size 一张子图
    """
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
    fig.suptitle("CUDA Matrix Multiplication — Effective Throughput (GFLOPS)",
                 fontsize=15, fontweight="bold", y=1.01)

    x = np.arange(len(MATRIX_SIZES))
    width = 0.25

    for idx, bs in enumerate(BLOCK_SIZES):
        ax = axes[idx]
        for kt_idx, (kt, label) in enumerate(KERNEL_LABELS.items()):
            gflops = []
            for sz in MATRIX_SIZES:
                key = (sz, bs, kt)
                if key in data and data[key] > 0:
                    flops = 2.0 * sz * sz * sz  # m=n=k=sz
                    gflops.append(flops / (data[key] * 1e6))
                else:
                    gflops.append(0)
            bars = ax.bar(x + (kt_idx - 1) * width, gflops, width,
                          color=COLORS[kt], label=label, edgecolor="white",
                          linewidth=0.5)
            # 在小柱子上标注数值
            for bar, val in zip(bars, gflops):
                if val > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2.,
                            bar.get_height() + max(gflops) * 0.02,
                            f"{val:.1f}", ha="center", va="bottom",
                            fontsize=7, rotation=90)

        ax.set_title(f"Block Size = {bs}×{bs}", fontsize=12, fontweight="bold")
        ax.set_xlabel("Matrix Dimension (m = n = k)")
        ax.set_ylabel("GFLOPS")
        ax.set_xticks(x)
        ax.set_xticklabels(MATRIX_SIZES)
        ax.grid(True, alpha=0.3, axis="y", linestyle="--")
        ax.legend(fontsize=8)

    plt.tight_layout()
    path = os.path.join(IMG_DIR, "fig2_throughput.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"       Saved: {path}")


def plot_speedup(data):
    """
    fig3_speedup.png
    分组柱状图 — 以 naive_2d 为基准 (speedup=1.0), 对比其他 kernel 的加速比
    每个 Block Size 一张子图
    """
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
    fig.suptitle("CUDA Matrix Multiplication — Speedup (Baseline: Naive 2D)",
                 fontsize=15, fontweight="bold", y=1.01)

    x = np.arange(len(MATRIX_SIZES))
    width = 0.25

    # 仅绘制 naive_1d 和 shared_tiled (naive_2d 作为基线恒为 1)
    kt_to_plot = [1, 2]  # naive_1d=1, shared_tiled=2

    for idx, bs in enumerate(BLOCK_SIZES):
        ax = axes[idx]
        # 基线参考线
        ax.axhline(y=1.0, color=COLORS[0], linewidth=1.5,
                   linestyle="--", alpha=0.6, label="Naive 2D (baseline)")

        for bar_idx, kt in enumerate(kt_to_plot):
            speedups = []
            for sz in MATRIX_SIZES:
                key_this = (sz, bs, kt)
                key_base = (sz, bs, 0)  # naive_2d
                if key_this in data and key_base in data and data[key_base] > 0:
                    speedups.append(data[key_base] / data[key_this])
                else:
                    speedups.append(0)
            bars = ax.bar(x + (bar_idx - 0.5) * width, speedups, width,
                          color=COLORS[kt], label=KERNEL_LABELS[kt],
                          edgecolor="white", linewidth=0.5)
            for bar, val in zip(bars, speedups):
                if val > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2.,
                            bar.get_height() + 0.05,
                            f"{val:.2f}×", ha="center", va="bottom",
                            fontsize=7)

        ax.set_title(f"Block Size = {bs}×{bs}", fontsize=12, fontweight="bold")
        ax.set_xlabel("Matrix Dimension (m = n = k)")
        ax.set_ylabel("Speedup (vs. Naive 2D)")
        ax.set_xticks(x)
        ax.set_xticklabels(MATRIX_SIZES)
        ax.grid(True, alpha=0.3, axis="y", linestyle="--")
        ax.legend(fontsize=8)

    plt.tight_layout()
    path = os.path.join(IMG_DIR, "fig3_speedup.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"       Saved: {path}")


# ================================================================
# 步骤 4: 生成 LaTeX 表格数据
# ================================================================

def print_latex_table(data):
    """打印 LaTeX 三线表格式的性能汇总表"""
    print("\n" + "=" * 64)
    print("  LaTeX Table: Performance Summary")
    print("=" * 64)
    print()
    print(r"\begin{table}[H]")
    print(r"    \centering")
    print(r"    \caption{矩阵乘法性能基准测试全量数据}")
    print(r"    \label{tab:benchmark_full}")
    print(r"    \begin{tabular}{cc|ccc|cc}")
    print(r"        \toprule")
    print(r"        \multirow{2}{*}{$n$} & \multirow{2}{*}{Tile} & "
          r"\multicolumn{3}{c|}{执行时间 $t$ (ms)} & "
          r"\multicolumn{2}{c}{加速比 (vs. Naive 2D)} \\")
    print(r"        \cmidrule(lr){3-5} \cmidrule(lr){6-7}")
    print(r"        & & Naive 2D & Naive 1D & Shared Tiled & "
          r"Naive 1D & Shared Tiled \\")
    print(r"        \midrule")

    for sz in MATRIX_SIZES:
        first_sz = True
        for bs in BLOCK_SIZES:
            t_naive2d  = data.get((sz, bs, 0), None)
            t_naive1d  = data.get((sz, bs, 1), None)
            t_shared   = data.get((sz, bs, 2), None)

            if t_naive2d is None:
                continue

            t_n2_str = f"{t_naive2d:.6f}" if t_naive2d else "N/A"
            t_n1_str = f"{t_naive1d:.6f}" if t_naive1d else "N/A"
            t_sh_str = f"{t_shared:.6f}" if t_shared else "N/A"

            su_1d = t_naive2d / t_naive1d if (t_naive2d and t_naive1d and t_naive1d > 0) else 0
            su_sh = t_naive2d / t_shared  if (t_naive2d and t_shared and t_shared > 0) else 0

            su_1d_str = f"{su_1d:.2f}$\\times$" if su_1d > 0 else "N/A"
            su_sh_str = f"{su_sh:.2f}$\\times$" if su_sh > 0 else "N/A"

            # Bold the best
            if su_sh > su_1d and su_sh > 1.0:
                su_sh_str = f"\\textbf{{{su_sh_str}}}"

            if first_sz:
                size_str = f"\\multirow{{{len(BLOCK_SIZES)}}}{{*}}{{{sz}}}"
                first_sz = False
            else:
                size_str = ""

            print(f"        {size_str} & ${bs}\\times{bs}$ & "
                  f"{t_n2_str} & {t_n1_str} & {t_sh_str} & "
                  f"{su_1d_str} & {su_sh_str} \\\\")
            if not first_sz and bs != BLOCK_SIZES[-1]:
                pass  # No special handling needed
        if sz != MATRIX_SIZES[-1]:
            print(r"        \midrule")

    print(r"        \bottomrule")
    print(r"    \end{tabular}")
    print(r"\end{table}")


# ================================================================
# 主入口
# ================================================================

def main():
    os.makedirs(IMG_DIR, exist_ok=True)

    # 运行测试
    rows, header = run_benchmarks()

    # 解析数据
    data = parse_data(rows)
    print(f"\n       Parsed {len(data)} valid data points.")

    if len(data) == 0:
        print("[ERROR] No valid data points collected. Aborting plots.")
        sys.exit(1)

    # 绘图
    print("\n[4/4] Generating plots...")
    plot_execution_time(data)
    plot_throughput(data)
    plot_speedup(data)

    # 输出 LaTeX 表格
    print_latex_table(data)

    print("\n" + "=" * 64)
    print("  Done! All plots saved to img/ directory.")
    print("=" * 64)


if __name__ == "__main__":
    main()
