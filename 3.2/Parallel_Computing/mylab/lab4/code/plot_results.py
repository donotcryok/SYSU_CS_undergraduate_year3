#!/usr/bin/env python3
"""
plot_results.py - 读取测试结果并生成加速比图表
使用方法:
    使用前请先运行 bash code/run_tests.sh 生成测试数据并且安装requiredments.txt中列出的Python依赖库。
    python code/plot_results.py
输出:
    img/mc_speedup.png - 蒙特卡洛方法在不同规模下的多线程加速比折线图
"""

import os
import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def parse_results(filepath):
    """解析results.txt文件，提取蒙特卡洛测试数据"""
    data = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 查找蒙特卡洛测试数据部分
    in_mc_section = False
    header_found = False
    thread_counts = []
    
    for line in lines:
        line = line.strip()
        
        if '蒙特卡洛测试' in line:
            in_mc_section = True
            continue
        
        if not in_mc_section:
            continue
        
        # 解析表头
        if line.startswith('Scale'):
            parts = line.split(',')
            thread_counts = [int(p.replace('threads', '').replace('threads', '')) for p in parts[1:]]
            header_found = True
            continue
        
        if not header_found:
            continue
        
        # 解析数据行
        if line and not line.startswith('=') and not line.startswith('-'):
            parts = line.split(',')
            if len(parts) >= 2:
                try:
                    scale = int(parts[0])
                    times = [float(p) for p in parts[1:] if p]
                    if times:
                        data[scale] = times
                except ValueError:
                    continue
    
    return data, thread_counts

def calculate_speedup(data, thread_counts):
    """计算加速比"""
    speedup_data = {}
    
    for scale, times in data.items():
        if len(times) > 0 and times[0] > 0:
            base_time = times[0]  # 单线程时间作为基准
            speedups = [base_time / t if t > 0 else 0 for t in times]
            speedup_data[scale] = speedups
    
    return speedup_data

def plot_speedup(speedup_data, thread_counts, output_path):
    """绘制加速比折线图"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 颜色和标记
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    markers = ['o', 's', '^', 'D', 'v', 'p']
    
    # 绘制每个规模的加速比曲线
    scales = sorted(speedup_data.keys())
    
    for i, scale in enumerate(scales):
        speedups = speedup_data[scale]
        # 只绘制有线程数对应的点
        valid_threads = thread_counts[:len(speedups)]
        valid_speedups = speedups[:len(valid_threads)]
        
        # 格式化规模显示
        if scale >= 1000000:
            scale_label = f'{scale/1000000:.0f}M'
        elif scale >= 1000:
            scale_label = f'{scale/1000:.0f}K'
        else:
            scale_label = str(scale)
        
        ax.plot(valid_threads, valid_speedups, 
                color=colors[i % len(colors)],
                marker=markers[i % len(markers)],
                linewidth=2,
                markersize=8,
                label=f'N={scale_label}')
    
    # 绘制理想加速比线
    max_threads = max(thread_counts) if thread_counts else 16
    ideal_threads = list(range(1, max_threads + 1))
    ideal_speedup = ideal_threads
    ax.plot(ideal_threads, ideal_speedup, 
            'k--', 
            linewidth=1.5, 
            alpha=0.7,
            label='Ideal Speedup')
    
    # 设置图表属性
    ax.set_xlabel('Number of Threads', fontsize=12)
    ax.set_ylabel('Speedup', fontsize=12)
    ax.set_title('Monte Carlo Method Multi-thread Speedup', fontsize=14, fontweight='bold')
    ax.set_xticks(thread_counts)
    ax.set_xlim(0.5, max_threads + 0.5)
    ax.set_ylim(0, max_threads + 1)
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(loc='upper left', fontsize=10)
    
    # 添加说明文字
    ax.text(0.98, 0.02, 
            '加速比 = 单线程时间 / 多线程时间',
            transform=ax.transAxes,
            fontsize=9,
            ha='right',
            va='bottom',
            style='italic',
            alpha=0.7)
    
    plt.tight_layout()
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 保存图表
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"图表已保存到: {output_path}")
    
    plt.close()

def plot_efficiency(speedup_data, thread_counts, output_path):
    """绘制并行效率图"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    markers = ['o', 's', '^', 'D', 'v', 'p']
    
    scales = sorted(speedup_data.keys())
    
    for i, scale in enumerate(scales):
        speedups = speedup_data[scale]
        valid_threads = thread_counts[:len(speedups)]
        
        # 计算效率 = 加速比 / 线程数
        efficiencies = [s / t if t > 0 else 0 for s, t in zip(speedups, valid_threads)]
        
        if scale >= 1000000:
            scale_label = f'{scale/1000000:.0f}M'
        elif scale >= 1000:
            scale_label = f'{scale/1000:.0f}K'
        else:
            scale_label = str(scale)
        
        ax.plot(valid_threads, efficiencies,
                color=colors[i % len(colors)],
                marker=markers[i % len(markers)],
                linewidth=2,
                markersize=8,
                label=f'N={scale_label}')
    
    ax.set_xlabel('Number of Threads', fontsize=12)
    ax.set_ylabel('Parallel Efficiency', fontsize=12)
    ax.set_title('Monte Carlo Method Multi-thread Efficiency', fontsize=14, fontweight='bold')
    ax.set_xticks(thread_counts)
    ax.set_ylim(0, 1.1)
    ax.axhline(y=1.0, color='k', linestyle='--', alpha=0.5, label='理想效率')
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend(loc='upper right', fontsize=10)
    
    plt.tight_layout()
    
    efficiency_path = output_path.replace('speedup.png', 'efficiency.png')
    plt.savefig(efficiency_path, dpi=150, bbox_inches='tight')
    print(f"效率图已保存到: {efficiency_path}")
    
    plt.close()

def main():
    # 路径设置
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    results_file = os.path.join(root_dir, 'results.txt')
    output_file = os.path.join(root_dir, 'img', 'mc_speedup.png')
    
    # 检查结果文件是否存在
    if not os.path.exists(results_file):
        print(f"错误: 找不到结果文件 {results_file}")
        print("请先运行 bash code/run_tests.sh 生成测试数据")
        return
    
    print("正在解析测试结果...")
    data, thread_counts = parse_results(results_file)
    
    if not data:
        print("错误: 未能从结果文件中提取数据")
        return
    
    print(f"解析到 {len(data)} 个测试规模")
    print(f"线程数: {thread_counts}")
    
    print("正在计算加速比...")
    speedup_data = calculate_speedup(data, thread_counts)
    
    print("正在生成图表...")
    plot_speedup(speedup_data, thread_counts, output_file)
    plot_efficiency(speedup_data, thread_counts, output_file)
    
    print("\n图表生成完成！")

if __name__ == '__main__':
    main()