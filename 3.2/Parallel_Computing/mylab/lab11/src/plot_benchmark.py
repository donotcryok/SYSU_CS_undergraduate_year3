#!/usr/bin/env python3
"""
plot_benchmark.py — Lab 11 卷积性能对比图生成脚本
读取 benchmark_results.csv 并使用 matplotlib 生成:
  1. fig1_execution_time.png   — 执行时间随输入尺寸变化 (分 Stride 子图)
  2. fig2_throughput.png       — 有效吞吐量 (GFLOPS) 对比
  3. fig3_speedup.png          — 以 Direct Conv 为基线的加速比
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import csv
import os

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Micro Hei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

CSV_PATH = os.path.join(os.path.dirname(__file__), 'benchmark_results.csv')
IMG_DIR  = os.path.join(os.path.dirname(__file__), '..', 'img')


def load_data(csv_path):
    """加载 CSV 数据并按 Stride 分组"""
    data = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            stride = int(row['stride'])
            H = int(row['H'])
            if stride not in data:
                data[stride] = {'H': [], 'direct': [], 'im2col': [], 'cudnn': []}
            data[stride]['H'].append(H)
            data[stride]['direct'].append(float(row['t_direct_ms']))
            data[stride]['im2col'].append(float(row['t_im2col_ms']))
            data[stride]['cudnn'].append(float(row['t_cudnn_ms']))
    # 按 H 排序
    for s in data:
        idx = np.argsort(data[s]['H'])
        for key in ['H', 'direct', 'im2col', 'cudnn']:
            data[s][key] = np.array(data[s][key])[idx]
    return data


def plot_execution_time(data, output_path):
    """图 1: 执行时间对比 (对数纵轴, 分 Stride 子图)"""
    strides = sorted(data.keys())
    fig, axes = plt.subplots(1, len(strides), figsize=(5*len(strides), 4.5), sharey=True)
    if len(strides) == 1:
        axes = [axes]

    colors = {'direct': '#2196F3', 'im2col': '#FF9800', 'cudnn': '#4CAF50'}
    labels = {'direct': 'Direct Conv', 'im2col': 'im2col+GEMM', 'cudnn': 'cuDNN'}
    markers = {'direct': 'o-', 'im2col': 's--', 'cudnn': '^:'}

    for ax, s in zip(axes, strides):
        d = data[s]
        H_vals = d['H']
        ax.plot(H_vals, d['direct'], markers['direct'], color=colors['direct'],
                label=labels['direct'], markersize=6, linewidth=1.5)
        ax.plot(H_vals, d['im2col'], markers['im2col'], color=colors['im2col'],
                label=labels['im2col'], markersize=6, linewidth=1.5)
        ax.plot(H_vals, d['cudnn'], markers['cudnn'], color=colors['cudnn'],
                label=labels['cudnn'], markersize=6, linewidth=1.5)
        ax.set_title(f'Stride = {s}', fontsize=12, fontweight='bold')
        ax.set_xlabel('Input Size (H=W)', fontsize=10)
        ax.set_xscale('log', base=2)
        ax.set_yscale('log')
        ax.grid(True, alpha=0.3)
        ax.set_xticks(H_vals)
        ax.set_xticklabels([str(int(h)) for h in H_vals], rotation=45, fontsize=8)

    axes[0].set_ylabel('Execution Time (ms)', fontsize=10)
    handles, labels_legend = axes[-1].get_legend_handles_labels()
    fig.legend(handles, labels_legend, loc='upper center', ncol=3,
               bbox_to_anchor=(0.5, 1.02), fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def plot_speedup(data, output_path):
    """图 2: 加速比 (以 Direct Conv 为基线)"""
    strides = sorted(data.keys())
    fig, axes = plt.subplots(1, len(strides), figsize=(5*len(strides), 4.5), sharey=True)
    if len(strides) == 1:
        axes = [axes]

    colors = {'im2col': '#FF9800', 'cudnn': '#4CAF50'}
    labels = {'im2col': 'im2col+GEMM', 'cudnn': 'cuDNN'}
    hatch = {'im2col': '//', 'cudnn': '\\\\'}

    for ax, s in zip(axes, strides):
        d = data[s]
        H_vals = d['H']
        x = np.arange(len(H_vals))
        width = 0.35

        speedup_im2col = d['direct'] / d['im2col']
        speedup_cudnn  = d['direct'] / d['cudnn']

        bars1 = ax.bar(x - width/2, speedup_im2col, width, color=colors['im2col'],
                       label=labels['im2col'], edgecolor='black', linewidth=0.5)
        bars2 = ax.bar(x + width/2, speedup_cudnn, width, color=colors['cudnn'],
                       label=labels['cudnn'], edgecolor='black', linewidth=0.5)

        # 数值标注
        for bar, val in zip(bars1, speedup_im2col):
            va = 'bottom' if val >= 1 else 'top'
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.2f}x', ha='center', va=va, fontsize=7, rotation=90)
        for bar, val in zip(bars2, speedup_cudnn):
            va = 'bottom' if val >= 1 else 'top'
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                    f'{val:.2f}x', ha='center', va=va, fontsize=7, rotation=90)

        ax.axhline(y=1.0, color='red', linestyle='--', linewidth=1, alpha=0.6, label='Baseline')
        ax.set_title(f'Stride = {s}', fontsize=12, fontweight='bold')
        ax.set_xlabel('Input Size (H=W)', fontsize=10)
        ax.set_ylabel('Speedup vs Direct Conv', fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels([str(int(h)) for h in H_vals], rotation=45, fontsize=8)
        ax.grid(True, alpha=0.3, axis='y')

    handles, labels_legend = axes[-1].get_legend_handles_labels()
    fig.legend(handles, labels_legend, loc='upper center', ncol=3,
               bbox_to_anchor=(0.5, 1.02), fontsize=9)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def plot_stride_comparison(data, output_path):
    """图 3: 各 Stride 下性能对比 (分组柱状图, 按方法分色)"""
    strides = sorted(data.keys())

    # 收集所有 H 值
    all_H = set()
    for s in strides:
        all_H.update(data[s]['H'])
    all_H = sorted(all_H)

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
    methods = ['direct', 'im2col', 'cudnn']
    titles = ['Direct Convolution', 'im2col + GEMM', 'cuDNN']
    colors_stride = {1: '#2196F3', 2: '#FF9800', 3: '#4CAF50'}

    for ax, method, title in zip(axes, methods, titles):
        valid_H = []
        for h in all_H:
            has_all = all(h in data[s]['H'] and data[s]['direct'][list(data[s]['H']).index(h)] > 0
                          for s in strides)
            if has_all:
                valid_H.append(h)

        x = np.arange(len(valid_H))
        n_strides = len(strides)
        width = 0.8 / n_strides

        for i, s in enumerate(strides):
            d = data[s]
            values = []
            for h in valid_H:
                idx = list(d['H']).index(h)
                values.append(d[method][idx])
            offset = (i - (n_strides - 1) / 2) * width
            bars = ax.bar(x + offset, values, width, color=colors_stride[s],
                          label=f'Stride={s}', edgecolor='black', linewidth=0.5)
            for bar, val in zip(bars, values):
                if val >= 0.01:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                            f'{val:.3f}', ha='center', va='bottom', fontsize=6, rotation=90)

        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel('Input Size (H=W)', fontsize=10)
        ax.set_ylabel('Time (ms)', fontsize=10)
        ax.set_xticks(x)
        ax.set_xticklabels([str(h) for h in valid_H], rotation=45, fontsize=8)
        ax.grid(True, alpha=0.3, axis='y')
        ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_path}")


def main():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found. Run benchmark first.")
        return

    os.makedirs(IMG_DIR, exist_ok=True)

    data = load_data(CSV_PATH)
    print(f"Loaded data: strides={sorted(data.keys())}, "
          f"sizes={sorted(set(int(h) for s in data for h in data[s]['H']))}")

    plot_execution_time(data, os.path.join(IMG_DIR, 'fig1_execution_time.png'))
    plot_speedup(data, os.path.join(IMG_DIR, 'fig2_speedup.png'))
    plot_stride_comparison(data, os.path.join(IMG_DIR, 'fig3_stride_comparison.png'))

    print("\nAll plots generated successfully.")


if __name__ == '__main__':
    main()
