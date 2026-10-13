#!/usr/bin/env python3
"""
OpenMP 矩阵乘法自动化基准测试脚本
"""

import subprocess
import json
import os
import sys
from pathlib import Path

# 实验参数配置
SIZES = [128, 256, 512, 1024, 2048]
THREADS = [1, 2, 4, 8, 16]
SCHEDULES = ['static', 'dynamic', 'guided']

# 输出路径
BASE_DIR = Path(__file__).parent.parent
CODE_DIR = BASE_DIR / 'code'
IMG_DIR = BASE_DIR / 'img'
RESULTS_FILE = BASE_DIR / 'memory.md'

EXE = CODE_DIR / 'gemm_omp'


def run_gemm(threads, size, schedule, verify=False, blocked=False):
    """运行一次矩阵乘法测试"""
    cmd = [
        str(EXE),
        str(threads),
        str(size),
        schedule,
        '1' if verify else '0',
        '1' if blocked else '0'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return None

        # 解析输出
        for line in result.stdout.split('\n'):
            if '计算时间:' in line:
                time_ms = float(line.split(':')[1].strip().split()[0])
            elif '性能:' in line:
                gflops = float(line.split(':')[1].strip().split()[0])

        return {
            'threads': threads,
            'size': size,
            'schedule': schedule,
            'time_ms': time_ms,
            'gflops': gflops
        }
    except subprocess.TimeoutExpired:
        print(f"Timeout: threads={threads}, size={size}")
        return None
    except Exception as e:
        print(f"Error running test: {e}")
        return None


def run_benchmark():
    """运行完整基准测试"""
    results = []

    print("=== 开始基准测试 ===")
    print(f"矩阵规模: {SIZES}")
    print(f"线程数: {THREADS}")
    print(f"调度模式: {SCHEDULES}")
    print()

    # 遍历所有参数组合
    for size in SIZES:
        print(f"\n--- 测试规模: {size}x{size} ---")
        for schedule in SCHEDULES:
            for threads in THREADS:
                print(f"  线程={threads:2d}, 调度={schedule:8s} ... ", end='', flush=True)

                result = run_gemm(threads, size, schedule)
                if result:
                    results.append(result)
                    print(f"{result['time_ms']:.1f}ms, {result['gflops']:.1f} GFLOPS")
                else:
                    print("失败")

    return results


def calculate_metrics(results):
    """计算加速比和效率"""
    # 按规模和调度分组
    groups = {}
    for r in results:
        key = (r['size'], r['schedule'])
        if key not in groups:
            groups[key] = {}
        groups[key][r['threads']] = r

    metrics = []

    for (size, schedule), group in groups.items():
        baseline = group.get(1)
        if not baseline:
            continue

        baseline_time = baseline['time_ms']

        for threads, result in group.items():
            speedup = baseline_time / result['time_ms']
            efficiency = speedup / threads

            metrics.append({
                'size': size,
                'schedule': schedule,
                'threads': threads,
                'time_ms': result['time_ms'],
                'gflops': result['gflops'],
                'speedup': speedup,
                'efficiency': efficiency
            })

    return metrics


def generate_plots(metrics):
    """生成性能图表"""
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("错误: 需要 matplotlib 和 numpy")
        print("运行: pip install matplotlib numpy")
        return

    # 使用英文标签，LaTeX 报告中用 \caption 提供中文说明
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False

    IMG_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 加速比图
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    schedules = ['static', 'dynamic', 'guided']

    for idx, schedule in enumerate(schedules):
        ax = axes[idx]
        for size in SIZES:
            data = [m for m in metrics if m['schedule'] == schedule and m['size'] == size]
            if not data:
                continue

            threads = [m['threads'] for m in data]
            speedups = [m['speedup'] for m in data]

            ax.plot(threads, speedups, marker='o', label=f'N={size}')

        # 理想加速比
        ax.plot(THREADS, THREADS, 'k--', alpha=0.5, label='理想加速比')

        ax.set_xlabel('线程数')
        ax.set_ylabel('加速比')
        ax.set_title(f'{schedule.capitalize()} 调度')
        ax.grid(True, alpha=0.3)
        ax.legend()

    plt.tight_layout()
    plt.savefig(IMG_DIR / 'speedup_comparison.pdf', bbox_inches='tight')
    plt.savefig(IMG_DIR / 'speedup_comparison.png', dpi=300)
    print(f"保存: speedup_comparison.pdf/png")

    # 2. 效率图
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    for idx, schedule in enumerate(schedules):
        ax = axes[idx]
        for size in SIZES:
            data = [m for m in metrics if m['schedule'] == schedule and m['size'] == size]
            if not data:
                continue

            threads = [m['threads'] for m in data]
            efficiencies = [m['efficiency'] for m in data]

            ax.plot(threads, efficiencies, marker='o', label=f'N={size}')

        ax.axhline(y=1.0, color='k', linestyle='--', alpha=0.5)
        ax.set_xlabel('线程数')
        ax.set_ylabel('效率 (E = S/P)')
        ax.set_ylim([0, 1.2])
        ax.set_title(f'{schedule.capitalize()} 调度')
        ax.grid(True, alpha=0.3)
        ax.legend()

    plt.tight_layout()
    plt.savefig(IMG_DIR / 'efficiency_comparison.pdf', bbox_inches='tight')
    plt.savefig(IMG_DIR / 'efficiency_comparison.png', dpi=300)
    print(f"保存: efficiency_comparison.pdf/png")

    # 3. 调度模式对比 (单线程)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # GFLOPS 对比
    ax = axes[0]
    for size in [512, 1024, 2048]:
        data = [m for m in metrics if m['size'] == size and m['threads'] == 8]
        if not data:
            continue

        schedules = [m['schedule'] for m in data]
        gflops = [m['gflops'] for m in data]

        x = np.arange(len(schedules))
        width = 0.25
        offset = (SIZES.index(size) - 1) * width

        ax.bar(x + offset, gflops, width, label=f'N={size}')

    ax.set_xlabel('调度模式')
    ax.set_ylabel('GFLOPS')
    ax.set_title('调度模式性能对比 (8线程)')
    ax.set_xticks(np.arange(len(SCHEDULES)))
    ax.set_xticklabels(SCHEDULES)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # 时间对比
    ax = axes[1]
    for size in [512, 1024, 2048]:
        data = [m for m in metrics if m['size'] == size and m['threads'] == 8]
        if not data:
            continue

        schedules = [m['schedule'] for m in data]
        times = [m['time_ms'] for m in data]

        x = np.arange(len(schedules))
        width = 0.25
        offset = (SIZES.index(size) - 1) * width

        ax.bar(x + offset, times, width, label=f'N={size}')

    ax.set_xlabel('调度模式')
    ax.set_ylabel('时间 (ms)')
    ax.set_title('调度模式时间对比 (8线程)')
    ax.set_xticks(np.arange(len(SCHEDULES)))
    ax.set_xticklabels(SCHEDULES)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(IMG_DIR / 'schedule_comparison.pdf', bbox_inches='tight')
    plt.savefig(IMG_DIR / 'schedule_comparison.png', dpi=300)
    print(f"保存: schedule_comparison.pdf/png")

    # 4. 线程扩展性
    fig, ax = plt.subplots(figsize=(8, 5))

    for schedule in SCHEDULES:
        data = [m for m in metrics if m['schedule'] == schedule and m['size'] == 1024]
        if not data:
            continue

        threads = [m['threads'] for m in data]
        gflops = [m['gflops'] for m in data]

        ax.plot(threads, gflops, marker='o', label=schedule)

    ax.set_xlabel('线程数')
    ax.set_ylabel('性能 (GFLOPS)')
    ax.set_title('线程扩展性 (N=1024)')
    ax.grid(True, alpha=0.3)
    ax.legend()

    plt.tight_layout()
    plt.savefig(IMG_DIR / 'scalability.pdf', bbox_inches='tight')
    plt.savefig(IMG_DIR / 'scalability.png', dpi=300)
    print(f"保存: scalability.pdf/png")


def save_results(metrics):
    """保存实验结果到 memory.md"""
    with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
        f.write("# OpenMP 矩阵乘法实验数据\n\n")

        # 写入 JSON 格式原始数据
        f.write("## 原始数据 (JSON)\n\n")
        f.write("```json\n")
        f.write(json.dumps(metrics, indent=2, ensure_ascii=False))
        f.write("\n```\n\n")

        # 写入表格数据
        f.write("## 性能表格\n\n")

        for schedule in SCHEDULES:
            f.write(f"### {schedule.upper()} 调度\n\n")
            f.write("| 规模 | 线程 | 时间(ms) | GFLOPS | 加速比 | 效率 |\n")
            f.write("|------|------|----------|--------|--------|------|\n")

            for size in SIZES:
                for threads in THREADS:
                    m = next((x for x in metrics if x['size'] == size
                              and x['threads'] == threads and x['schedule'] == schedule), None)
                    if m:
                        f.write(f"| {size} | {threads} | {m['time_ms']:.2f} | "
                                f"{m['gflops']:.2f} | {m['speedup']:.2f} | "
                                f"{m['efficiency']:.2f} |\n")
            f.write("\n")

        # 写入关键观测点
        f.write("## 关键观测点\n\n")

        # 最佳性能
        best = max(metrics, key=lambda x: x['gflops'])
        f.write(f"- **最高性能**: {best['gflops']:.2f} GFLOPS "
                f"(规模={best['size']}, 线程={best['threads']}, 调度={best['schedule']})\n")

        # 最佳加速比
        best_speedup = max(metrics, key=lambda x: x['speedup'])
        f.write(f"- **最高加速比**: {best_speedup['speedup']:.2f}x "
                f"(规模={best_speedup['size']}, 线程={best_speedup['threads']}, 调度={best_speedup['schedule']})\n")

        f.write("\n")


def main():
    # 检查可执行文件
    if not EXE.exists():
        print(f"错误: 可执行文件不存在 {EXE}")
        print("请先在 code 目录运行: make")
        sys.exit(1)

    # 运行基准测试
    results = run_benchmark()

    # 计算指标
    metrics = calculate_metrics(results)

    # 保存结果
    save_results(metrics)
    print(f"\n结果已保存到: {RESULTS_FILE}")

    # 生成图表
    print("\n=== 生成图表 ===")
    generate_plots(metrics)

    print("\n基准测试完成!")


if __name__ == '__main__':
    main()