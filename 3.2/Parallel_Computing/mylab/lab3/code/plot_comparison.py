#!/usr/bin/env python3
"""
Lab3 多策略对比数据可视化脚本
读取 results_matrix_compare.txt 和 results_sum_compare.txt
生成策略对比柱状图
"""

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

import matplotlib.pyplot as plt
import numpy as np
import re
import os

# 设置字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def parse_matrix_results(filename):
    """解析矩阵乘法对比结果"""
    results = {}  # {size: {strategy: {threads: time}}}
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析数据 - 策略名包含连字符，使用 [\w-]+
    pattern = r'Strategy: ([\w-]+), Size: (\d+) x (\d+) x (\d+), Threads: (\d+), Time: ([\d.]+) s'
    for match in re.finditer(pattern, content):
        strategy = match.group(1)
        size = int(match.group(2))
        threads = int(match.group(5))
        time = float(match.group(6))
        
        if size not in results:
            results[size] = {}
        if strategy not in results[size]:
            results[size][strategy] = {}
        results[size][strategy][threads] = time
    
    return results

def parse_sum_results(filename):
    """解析数组求和对比结果"""
    results = {}  # {size: {strategy: {threads: time}}}
    
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析数据
    pattern = r'Strategy: (\w+-\w+|Global-Mutex|Local-Reduction), Size: (\d+), Threads: (\d+), Sum: \d+, Time: ([\d.]+) s'
    for match in re.finditer(pattern, content):
        strategy = match.group(1)
        size = int(match.group(2))
        threads = int(match.group(3))
        time = float(match.group(4))
        
        if size not in results:
            results[size] = {}
        if strategy not in results[size]:
            results[size][strategy] = {}
        results[size][strategy][threads] = time
    
    return results

def plot_matrix_comparison(results, output_file):
    """绘制矩阵乘法策略对比柱状图"""
    sizes = sorted(results.keys())
    strategies = ['Row-wise', 'Column-wise', 'Block-wise']
    threads_list = [1, 2, 4, 8, 16]
    
    # 为每个规模创建一个图表
    for size in sizes:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        x = np.arange(len(threads_list))
        width = 0.25
        
        data = results[size]
        
        for i, strategy in enumerate(strategies):
            if strategy in data:
                times = [data[strategy].get(t, 0) for t in threads_list]
                ax.bar(x + i * width, times, width, label=strategy)
        
        ax.set_xlabel('Threads', fontsize=12)
        ax.set_ylabel('Time (seconds)', fontsize=12)
        ax.set_title(f'Matrix Multiplication Strategy Comparison (Size: {size}x{size})', fontsize=14)
        ax.set_xticks(x + width)
        ax.set_xticklabels(threads_list)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # 使用对数刻度如果差异很大
        max_time = max([max(data[s].values()) for s in data if s in strategies])
        min_time = min([min(data[s].values()) for s in data if s in strategies])
        if max_time / min_time > 10:
            ax.set_yscale('log')
            ax.set_ylabel('Time (seconds, log scale)', fontsize=12)
        
        plt.tight_layout()
        plt.savefig(f'{output_file}_{size}.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_file}_{size}.png")
    
    # 创建综合对比图（16线程）
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(sizes))
    width = 0.25
    
    for i, strategy in enumerate(strategies):
        times = []
        for size in sizes:
            if strategy in results[size] and 16 in results[size][strategy]:
                times.append(results[size][strategy][16])
            else:
                times.append(0)
        ax.bar(x + i * width, times, width, label=strategy)
    
    ax.set_xlabel('Matrix Size', fontsize=12)
    ax.set_ylabel('Time (seconds)', fontsize=12)
    ax.set_title('Matrix Multiplication Strategy Comparison (16 Threads)', fontsize=14)
    ax.set_xticks(x + width)
    ax.set_xticklabels([f'{s}x{s}' for s in sizes])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_file}")

def plot_sum_comparison(results, output_file):
    """绘制数组求和策略对比柱状图"""
    sizes = sorted(results.keys())
    strategies = ['Global-Mutex', 'Local-Reduction']
    threads_list = [1, 2, 4, 8, 16]
    
    # 为每个规模创建一个图表
    for size in sizes:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        x = np.arange(len(threads_list))
        width = 0.35
        
        data = results[size]
        
        for i, strategy in enumerate(strategies):
            if strategy in data:
                times = [data[strategy].get(t, 0) for t in threads_list]
                ax.bar(x + i * width, times, width, label=strategy)
        
        ax.set_xlabel('Threads', fontsize=12)
        ax.set_ylabel('Time (seconds)', fontsize=12)
        ax.set_title(f'Array Sum Strategy Comparison (Size: {size//1000000}M)', fontsize=14)
        ax.set_xticks(x + width / 2)
        ax.set_xticklabels(threads_list)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # 使用对数刻度如果差异很大
        max_time = max([max(data[s].values()) for s in data if s in strategies])
        min_time = min([min(data[s].values()) for s in data if s in strategies])
        if max_time / min_time > 10:
            ax.set_yscale('log')
            ax.set_ylabel('Time (seconds, log scale)', fontsize=12)
        
        plt.tight_layout()
        plt.savefig(f'{output_file}_{size//1000000}M.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Saved: {output_file}_{size//1000000}M.png")
    
    # 创建综合对比图（多线程对比）
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(sizes))
    width = 0.35
    
    # 对比4线程（最佳配置）
    threads = 4
    for i, strategy in enumerate(strategies):
        times = []
        for size in sizes:
            if strategy in results[size] and threads in results[size][strategy]:
                times.append(results[size][strategy][threads])
            else:
                times.append(0)
        ax.bar(x + i * width, times, width, label=f'{strategy} ({threads} threads)')
    
    ax.set_xlabel('Array Size', fontsize=12)
    ax.set_ylabel('Time (seconds)', fontsize=12)
    ax.set_title(f'Array Sum Strategy Comparison ({threads} Threads)', fontsize=14)
    ax.set_xticks(x + width / 2)
    ax.set_xticklabels([f'{s//1000000}M' for s in sizes])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {output_file}")

def main():
    # 确保 img 目录存在
    os.makedirs('img', exist_ok=True)
    
    # 检测运行目录，自动调整路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.basename(script_dir) == 'code':
        # 从 code 目录运行
        base_dir = script_dir
        img_dir = os.path.join(os.path.dirname(script_dir), 'img')
    else:
        # 从项目根目录运行
        base_dir = os.path.join(script_dir, 'code')
        img_dir = os.path.join(script_dir, 'img')
    
    os.makedirs(img_dir, exist_ok=True)
    
    # 解析矩阵乘法对比数据
    matrix_file = os.path.join(base_dir, 'results_matrix_compare.txt')
    if os.path.exists(matrix_file):
        print(f"Reading: {matrix_file}")
        matrix_results = parse_matrix_results(matrix_file)
        print(f"Matrix results: {matrix_results}")
        plot_matrix_comparison(matrix_results, os.path.join(img_dir, 'matrix_strategy_compare'))
    else:
        print(f"Warning: {matrix_file} not found")
    
    # 解析数组求和对比数据
    sum_file = os.path.join(base_dir, 'results_sum_compare.txt')
    if os.path.exists(sum_file):
        print(f"Reading: {sum_file}")
        sum_results = parse_sum_results(sum_file)
        print(f"Sum results: {sum_results}")
        plot_sum_comparison(sum_results, os.path.join(img_dir, 'sum_strategy_compare'))
    else:
        print(f"Warning: {sum_file} not found")
    
    print("\nVisualization completed!")

if __name__ == '__main__':
    main()