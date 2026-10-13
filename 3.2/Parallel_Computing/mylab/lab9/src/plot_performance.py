#!/usr/bin/env python3
"""
plot_performance.py — 读取 benchmark_results.csv，绘制科学出版级质量图表

图1：不同矩阵规模下，三种算法的执行时间对比折线图（横轴为矩阵规模，纵轴为时间）
图2：不同 Block 大小下，吞吐量或加速比的对比柱状图

输出保存至 img/ 目录。
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import sys
import os

# 样式设置：仿学术出版
plt.rcParams.update({
    'font.size': 12,
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'legend.fontsize': 12,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'font.family': 'sans-serif',
})

def main():
    csv_path = os.path.join(os.path.dirname(__file__), 'benchmark_results.csv')
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found! Run transpose benchmark first.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(csv_path)

    # 列: n, tile_dim, algorithm, time_ms
    print("Loaded benchmark data:")
    print(df.to_string())
    print()

    img_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'img')
    os.makedirs(img_dir, exist_ok=True)

    # ==========================================================
    # 图1：不同矩阵规模下，三种算法的执行时间对比折线图
    # 分 tile_dim=16 和 tile_dim=32 两幅子图
    # ==========================================================
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    algorithms = ['naive_global', 'shared_naive', 'shared_padded']
    algo_labels = {
        'naive_global': 'Naive Global',
        'shared_naive': 'Shared (Bank Conflict)',
        'shared_padded': 'Shared (Padding, Conflict-Free)'
    }
    algo_colors = {
        'naive_global': '#E74C3C',
        'shared_naive': '#F39C12',
        'shared_padded': '#27AE60'
    }
    algo_markers = {
        'naive_global': 's',
        'shared_naive': '^',
        'shared_padded': 'o'
    }

    for idx, tile_dim in enumerate([16, 32]):
        ax = axes[idx]
        sub = df[df['tile_dim'] == tile_dim]

        for algo in algorithms:
            algo_data = sub[sub['algorithm'] == algo].sort_values('n')
            if len(algo_data) == 0:
                continue
            ax.plot(algo_data['n'], algo_data['time_ms'],
                    marker=algo_markers[algo],
                    color=algo_colors[algo],
                    label=algo_labels[algo],
                    linewidth=2,
                    markersize=8)

        ax.set_xlabel('Matrix Size (n)')
        ax.set_ylabel('Execution Time (ms)')
        ax.set_title(f'Tile Dim = {tile_dim}×{tile_dim}')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.set_xticks([512, 1024, 2048])

    fig.suptitle('Matrix Transpose Performance: Execution Time vs Matrix Size',
                 fontweight='bold', fontsize=16)
    fig.tight_layout()
    fig.savefig(os.path.join(img_dir, 'fig1_execution_time.png'))
    plt.close(fig)
    print(f"Saved fig1_execution_time.png")

    # ==========================================================
    # 图2：不同 Block 大小下，吞吐量对比柱状图
    # 吞吐量 = n^2 * sizeof(float) / time_ms  → GB/s
    # ==========================================================
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    for idx, n in enumerate([512, 1024, 2048]):
        ax = axes[idx]
        sub = df[df['n'] == n].copy()
        # 计算吞吐量 (GB/s)
        bytes_per_matrix = n * n * 4  # float = 4 bytes
        sub['throughput_gbps'] = bytes_per_matrix / (sub['time_ms'] / 1000.0) / 1e9

        x = np.arange(len(algorithms))
        bar_width = 0.35

        for ti, tile_dim in enumerate([16, 32]):
            tile_data = sub[sub['tile_dim'] == tile_dim].sort_values('algorithm')
            if len(tile_data) == 0:
                continue
            vals = []
            for algo in algorithms:
                match = tile_data[tile_data['algorithm'] == algo]
                vals.append(match['throughput_gbps'].values[0] if len(match) > 0 else 0)
            offset = (ti - 0.5) * bar_width
            ax.bar(x + offset, vals, bar_width,
                   label=f'Tile {tile_dim}×{tile_dim}',
                   color=['#3498DB', '#9B59B6'][ti],
                   alpha=0.85,
                   edgecolor='black',
                   linewidth=0.8)

        ax.set_xlabel('Algorithm')
        ax.set_ylabel('Throughput (GB/s)')
        ax.set_title(f'Matrix Size n = {n}')
        ax.set_xticks(x)
        ax.set_xticklabels(['Naive\nGlobal', 'Shared\n(Bank Conf.)', 'Shared\n(Padded)'], fontsize=9)
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.4, axis='y')

    fig.suptitle('Matrix Transpose Throughput: Algorithm vs Block Size',
                 fontweight='bold', fontsize=16)
    fig.tight_layout()
    fig.savefig(os.path.join(img_dir, 'fig2_throughput.png'))
    plt.close(fig)
    print(f"Saved fig2_throughput.png")

    # ==========================================================
    # 图3（额外）：加速比对比柱状图（以 Naive Global 为基准）
    # ==========================================================
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    for idx, n in enumerate([512, 1024, 2048]):
        ax = axes[idx]
        sub = df[df['n'] == n].copy()

        x = np.arange(2)  # tile 16, tile 32
        bar_width = 0.25

        for ai, algo in enumerate(['naive_global', 'shared_naive', 'shared_padded']):
            vals = []
            for tile_dim in [16, 32]:
                # 找到 naive_global 的 baseline time for this tile_dim
                baseline = sub[(sub['tile_dim'] == tile_dim) &
                               (sub['algorithm'] == 'naive_global')]['time_ms'].values
                baseline = baseline[0] if len(baseline) > 0 else 1.0
                target = sub[(sub['tile_dim'] == tile_dim) &
                             (sub['algorithm'] == algo)]['time_ms'].values
                target = target[0] if len(target) > 0 else baseline
                speedup = baseline / target
                vals.append(speedup)

            offset = (ai - 1.0) * bar_width
            ax.bar(x + offset, vals, bar_width,
                   label=algo_labels[algo],
                   color=algo_colors[algo],
                   alpha=0.85,
                   edgecolor='black',
                   linewidth=0.8)

        ax.axhline(y=1.0, color='black', linestyle='--', linewidth=1, alpha=0.7)
        ax.set_xlabel('Tile Dimension')
        ax.set_ylabel('Speedup (vs. Naive Global)')
        ax.set_title(f'Matrix Size n = {n}')
        ax.set_xticks(x)
        ax.set_xticklabels(['16×16', '32×32'])
        ax.legend(fontsize=9)
        ax.grid(True, linestyle='--', alpha=0.4, axis='y')

    fig.suptitle('Speedup Relative to Naive Global Memory',
                 fontweight='bold', fontsize=16)
    fig.tight_layout()
    fig.savefig(os.path.join(img_dir, 'fig3_speedup.png'))
    plt.close(fig)
    print(f"Saved fig3_speedup.png")

    print("\nAll figures generated successfully!")

if __name__ == '__main__':
    main()
