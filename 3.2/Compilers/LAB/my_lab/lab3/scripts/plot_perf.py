#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能测试可视化脚本 - 尾递归消除性能对比图表生成

本脚本读取 PerformanceTest.java 生成的 perf_results.csv 文件，
绘制递归版本与循环版本的执行时间对比折线图，并标注栈溢出临界点。

使用方法:
    python scripts/plot_perf.py

输出文件:
    img/performance_chart.png

依赖:
    pip install pandas matplotlib
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 设置中文字体支持
def setup_chinese_font():
    """配置 matplotlib 支持中文显示"""
    # 尝试使用系统中文字体
    chinese_fonts = [
        'SimHei',      # 黑体 (Windows)
        'Microsoft YaHei',  # 微软雅黑 (Windows)
        'PingFang SC', # 苹方 (macOS)
        'WenQuanYi Micro Hei',  # 文泉驿 (Linux)
        'Noto Sans CJK SC',     # Noto (跨平台)
    ]
    
    for font_name in chinese_fonts:
        try:
            # 检查字体是否存在
            font_path = fm.findfont(fm.FontProperties(family=font_name))
            if font_path and 'arial' not in font_path.lower():
                plt.rcParams['font.sans-serif'] = [font_name]
                plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
                print(f"使用中文字体: {font_name}")
                return True
        except:
            continue
    
    # 如果找不到中文字体，使用默认字体并警告
    print("警告: 未找到中文字体，图表中的中文可能显示为方块")
    print("建议安装: pip install matplotlib-fontja 或手动配置字体")
    return False

def load_performance_data(csv_path):
    """
    加载性能测试数据
    
    Args:
        csv_path: CSV 文件路径
        
    Returns:
        pandas DataFrame 包含性能数据
    """
    if not os.path.exists(csv_path):
        print(f"错误: 找不到数据文件 {csv_path}")
        print("请先运行性能测试: perf_test.bat 或 java PerformanceTest")
        sys.exit(1)
    
    try:
        df = pd.read_csv(csv_path)
        print(f"成功加载数据: {csv_path}")
        print(f"数据行数: {len(df)}")
        return df
    except Exception as e:
        print(f"读取 CSV 文件失败: {e}")
        sys.exit(1)

def plot_performance_chart(df, output_path):
    """
    绘制性能对比图表
    
    Args:
        df: 性能数据 DataFrame
        output_path: 输出图片路径
    """
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 提取数据
    lengths = df['ExpressionLength'].values
    recursive_times = df['RecursiveTime_ms'].values
    iterative_times = df['IterativeTime_ms'].values
    
    # 处理 NaN 值（栈溢出情况）
    # 将 NaN 替换为 None，matplotlib 会自动断开线条
    recursive_times_clean = [t if not pd.isna(t) else None for t in recursive_times]
    
    # 找到栈溢出的临界点（第一个 NaN 的位置）
    stack_overflow_idx = None
    stack_overflow_length = None
    for i, t in enumerate(recursive_times):
        if pd.isna(t):
            stack_overflow_idx = i
            stack_overflow_length = lengths[i]
            break
    
    # 绘制循环版本（迭代）的折线 - 蓝色实线
    ax.plot(lengths, iterative_times, 
            color='#2196F3', 
            linewidth=2.5, 
            marker='o', 
            markersize=8,
            label='循环版本 (Iterative) - 消除尾递归',
            linestyle='-')
    
    # 绘制递归版本的折线 - 红色实线（在栈溢出前）
    # 只绘制栈溢出之前的数据
    if stack_overflow_idx is not None:
        valid_lengths = lengths[:stack_overflow_idx]
        valid_times = recursive_times_clean[:stack_overflow_idx]
    else:
        valid_lengths = lengths
        valid_times = recursive_times_clean
    
    ax.plot(valid_lengths, valid_times, 
            color='#F44336', 
            linewidth=2.5, 
            marker='s', 
            markersize=8,
            label='递归版本 (Recursive) - 原始实现',
            linestyle='-')
    
    # 标注栈溢出临界点
    if stack_overflow_length is not None:
        # 绘制垂直虚线表示栈溢出临界点
        ax.axvline(x=stack_overflow_length, 
                   color='#FF9800', 
                   linestyle='--', 
                   linewidth=2,
                   label=f'栈溢出临界点 (≈{stack_overflow_length}字符)')
        
        # 添加文字注释
        ax.annotate('StackOverflowError!\n递归版本栈溢出',
                    xy=(stack_overflow_length, ax.get_ylim()[1] * 0.8),
                    xytext=(stack_overflow_length + 5000, ax.get_ylim()[1] * 0.9),
                    fontsize=12,
                    color='#FF5722',
                    weight='bold',
                    arrowprops=dict(arrowstyle='->', color='#FF5722', lw=1.5),
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF3E0', edgecolor='#FF5722'))
    
    # 设置坐标轴
    ax.set_xlabel('表达式长度 (字符数)', fontsize=14, weight='bold')
    ax.set_ylabel('执行时间 (毫秒)', fontsize=14, weight='bold')
    ax.set_title('尾递归消除性能对比测试\n递归版本 vs 循环版本执行时间', 
                 fontsize=16, weight='bold', pad=20)
    
    # 设置网格
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # 设置图例
    ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
    
    # 设置坐标轴范围
    ax.set_xlim(0, max(lengths) * 1.1)
    y_max = max([t for t in iterative_times if not pd.isna(t)]) * 1.5
    ax.set_ylim(0, max(y_max, 10))  # 至少显示 10ms
    
    # 添加性能分析结论文本框
    conclusion_text = """
性能分析结论:
• 递归版本: 空间复杂度 O(N)，易栈溢出
• 循环版本: 空间复杂度 O(1)，稳定可靠
• 消除尾递归可避免栈溢出风险
"""
    ax.text(0.98, 0.02, conclusion_text,
            transform=ax.transAxes,
            fontsize=10,
            verticalalignment='bottom',
            horizontalalignment='right',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#E8F5E9', edgecolor='#4CAF50', alpha=0.9))
    
    # 调整布局
    plt.tight_layout()
    
    # 确保 img 目录存在
    img_dir = os.path.dirname(output_path)
    if img_dir and not os.path.exists(img_dir):
        os.makedirs(img_dir)
    
    # 保存图表
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"图表已保存: {output_path}")
    
    # 显示图表（可选）
    # plt.show()

def main():
    """主函数"""
    print("=" * 50)
    print("  尾递归消除性能对比图表生成")
    print("=" * 50)
    print()
    
    # 配置中文字体
    setup_chinese_font()
    
    # 数据文件路径
    csv_path = "data/perf_results.csv"
    output_path = "img/performance_chart.png"
    
    # 加载数据
    df = load_performance_data(csv_path)
    print()
    print("数据预览:")
    print(df.to_string())
    print()
    
    # 绘制图表
    plot_performance_chart(df, output_path)
    
    print()
    print("=" * 50)
    print("  图表生成完成!")
    print("=" * 50)
    print()
    print(f"输出文件: {output_path}")
    print("请在实验报告 design.tex 中引用此图片")

if __name__ == "__main__":
    main()