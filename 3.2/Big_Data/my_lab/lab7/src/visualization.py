# -*- coding: utf-8 -*-
"""
可视化模块
生成推荐系统评估结果的对比图表
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # 非交互式后端

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False


class RecommenderVisualizer:
    """
    推荐系统可视化器
    
    生成各类评估指标的可视化图表
    """
    
    def __init__(self, output_dir='../img/'):
        """
        初始化可视化器
        
        Args:
            output_dir: 图片输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def plot_metrics_comparison(self, results_df, save_name='metrics_comparison.png'):
        """
        绘制各模型指标对比柱状图
        
        Args:
            results_df: 结果DataFrame (index为模型名)
            save_name: 保存文件名
        """
        # 选择要绘制的指标
        metrics = ['recall', 'precision', 'f1_score', 'coverage', 'diversity']
        metric_names = ['召回率', '精确率', 'F1分数', '覆盖率', '多样性']
        
        # 过滤存在的指标
        available_metrics = [m for m in metrics if m in results_df.columns]
        available_names = [metric_names[i] for i, m in enumerate(metrics) if m in results_df.columns]
        
        if not available_metrics:
            print("没有可用的指标进行可视化")
            return
        
        # 准备数据
        models = results_df.index.tolist()
        n_models = len(models)
        n_metrics = len(available_metrics)
        
        # 设置柱状图参数
        x = np.arange(n_metrics)
        width = 0.8 / n_models
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 颜色方案
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
        
        # 绘制每个模型的柱状图
        for i, model in enumerate(models):
            values = [results_df.loc[model, m] for m in available_metrics]
            bars = ax.bar(x + i * width, values, width, label=model, color=colors[i % len(colors)])
            
            # 在柱状图上显示数值
            for bar, val in zip(bars, values):
                height = bar.get_height()
                ax.annotate(f'{val:.3f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=8)
        
        # 设置图表属性
        ax.set_xlabel('评估指标', fontsize=12)
        ax.set_ylabel('数值', fontsize=12)
        ax.set_title('推荐系统性能对比', fontsize=14, fontweight='bold')
        ax.set_xticks(x + width * (n_models - 1) / 2)
        ax.set_xticklabels(available_names, fontsize=11)
        ax.legend(loc='upper right', fontsize=10)
        ax.set_ylim(0, 1.1)
        
        # 添加网格线
        ax.yaxis.grid(True, linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        # 保存图片
        save_path = os.path.join(self.output_dir, save_name)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"图表已保存: {save_path}")
        
    def plot_recall_comparison(self, results_df, save_name='recall_comparison.png'):
        """
        绘制召回率对比柱状图
        
        Args:
            results_df: 结果DataFrame
            save_name: 保存文件名
        """
        if 'recall' not in results_df.columns:
            print("没有召回率数据")
            return
        
        models = results_df.index.tolist()
        recalls = results_df['recall'].values
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(8, 6))
        
        colors = ['#3498db', '#e74c3c', '#2ecc71']
        bars = ax.bar(models, recalls, color=colors[:len(models)], edgecolor='black', linewidth=1.2)
        
        # 在柱状图上显示数值
        for bar, val in zip(bars, recalls):
            height = bar.get_height()
            ax.annotate(f'{val:.4f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 5),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax.set_xlabel('推荐算法', fontsize=12)
        ax.set_ylabel('召回率 (Recall Rate)', fontsize=12)
        ax.set_title('各算法召回率对比', fontsize=14, fontweight='bold')
        ax.set_ylim(0, max(recalls) * 1.2)
        
        # 添加网格线
        ax.yaxis.grid(True, linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        # 保存图片
        save_path = os.path.join(self.output_dir, save_name)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"图表已保存: {save_path}")
        
    def plot_coverage_comparison(self, results_df, save_name='coverage_comparison.png'):
        """
        绘制覆盖率对比柱状图
        
        Args:
            results_df: 结果DataFrame
            save_name: 保存文件名
        """
        if 'coverage' not in results_df.columns:
            print("没有覆盖率数据")
            return
        
        models = results_df.index.tolist()
        coverages = results_df['coverage'].values
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(8, 6))
        
        colors = ['#9b59b6', '#f39c12', '#1abc9c']
        bars = ax.bar(models, coverages, color=colors[:len(models)], edgecolor='black', linewidth=1.2)
        
        # 在柱状图上显示数值
        for bar, val in zip(bars, coverages):
            height = bar.get_height()
            ax.annotate(f'{val:.4f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 5),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax.set_xlabel('推荐算法', fontsize=12)
        ax.set_ylabel('覆盖率 (Coverage)', fontsize=12)
        ax.set_title('各算法覆盖率对比', fontsize=14, fontweight='bold')
        ax.set_ylim(0, max(coverages) * 1.2)
        
        # 添加网格线
        ax.yaxis.grid(True, linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        # 保存图片
        save_path = os.path.join(self.output_dir, save_name)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"图表已保存: {save_path}")
        
    def plot_diversity_comparison(self, results_df, save_name='diversity_comparison.png'):
        """
        绘制多样性对比柱状图
        
        Args:
            results_df: 结果DataFrame
            save_name: 保存文件名
        """
        if 'diversity' not in results_df.columns:
            print("没有多样性数据")
            return
        
        models = results_df.index.tolist()
        diversities = results_df['diversity'].values
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(8, 6))
        
        colors = ['#e67e22', '#8e44ad', '#16a085']
        bars = ax.bar(models, diversities, color=colors[:len(models)], edgecolor='black', linewidth=1.2)
        
        # 在柱状图上显示数值
        for bar, val in zip(bars, diversities):
            height = bar.get_height()
            ax.annotate(f'{val:.4f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 5),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=12, fontweight='bold')
        
        ax.set_xlabel('推荐算法', fontsize=12)
        ax.set_ylabel('多样性 (Diversity)', fontsize=12)
        ax.set_title('各算法多样性对比', fontsize=14, fontweight='bold')
        ax.set_ylim(0, max(diversities) * 1.2 if max(diversities) > 0 else 1)
        
        # 添加网格线
        ax.yaxis.grid(True, linestyle='--', alpha=0.7)
        ax.set_axisbelow(True)
        
        plt.tight_layout()
        
        # 保存图片
        save_path = os.path.join(self.output_dir, save_name)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"图表已保存: {save_path}")
        
    def plot_radar_chart(self, results_df, save_name='radar_chart.png'):
        """
        绘制雷达图对比
        
        Args:
            results_df: 结果DataFrame
            save_name: 保存文件名
        """
        metrics = ['recall', 'precision', 'f1_score', 'coverage', 'diversity']
        metric_names = ['召回率', '精确率', 'F1分数', '覆盖率', '多样性']
        
        # 过滤存在的指标
        available_metrics = [m for m in metrics if m in results_df.columns]
        available_names = [metric_names[i] for i, m in enumerate(metrics) if m in results_df.columns]
        
        if len(available_metrics) < 3:
            print("指标数量不足，无法绘制雷达图")
            return
        
        # 准备数据
        models = results_df.index.tolist()
        n_metrics = len(available_metrics)
        
        # 计算角度
        angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
        angles += angles[:1]  # 闭合
        
        # 创建图形
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
        
        for i, model in enumerate(models):
            values = results_df.loc[model, available_metrics].values.tolist()
            values += values[:1]  # 闭合
            
            ax.plot(angles, values, 'o-', linewidth=2, label=model, color=colors[i % len(colors)])
            ax.fill(angles, values, alpha=0.25, color=colors[i % len(colors)])
        
        # 设置标签
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(available_names, fontsize=11)
        ax.set_ylim(0, 1)
        
        ax.set_title('推荐系统综合性能雷达图', fontsize=14, fontweight='bold', y=1.08)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), fontsize=10)
        
        plt.tight_layout()
        
        # 保存图片
        save_path = os.path.join(self.output_dir, save_name)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"图表已保存: {save_path}")
        
    def plot_all_metrics(self, results_df, save_name='all_metrics_comparison.png'):
        """
        绘制综合指标对比图（子图形式）
        
        Args:
            results_df: 结果DataFrame
            save_name: 保存文件名
        """
        metrics = ['recall', 'precision', 'f1_score', 'coverage', 'diversity']
        metric_names = ['召回率', '精确率', 'F1分数', '覆盖率', '多样性']
        
        # 过滤存在的指标
        available = [(m, n) for m, n in zip(metrics, metric_names) if m in results_df.columns]
        
        if not available:
            print("没有可用的指标进行可视化")
            return
        
        n_metrics = len(available)
        models = results_df.index.tolist()
        
        # 创建子图
        fig, axes = plt.subplots(1, n_metrics, figsize=(4 * n_metrics, 5))
        if n_metrics == 1:
            axes = [axes]
        
        colors = ['#3498db', '#e74c3c', '#2ecc71']
        
        for ax, (metric, name) in zip(axes, available):
            values = results_df[metric].values
            bars = ax.bar(models, values, color=colors[:len(models)], edgecolor='black', linewidth=1)
            
            # 显示数值
            for bar, val in zip(bars, values):
                height = bar.get_height()
                ax.annotate(f'{val:.3f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=10)
            
            ax.set_title(name, fontsize=12, fontweight='bold')
            ax.set_ylim(0, max(values) * 1.2 if max(values) > 0 else 1)
            ax.yaxis.grid(True, linestyle='--', alpha=0.7)
            ax.set_axisbelow(True)
        
        plt.suptitle('推荐系统性能综合对比', fontsize=14, fontweight='bold', y=1.02)
        plt.tight_layout()
        
        # 保存图片
        save_path = os.path.join(self.output_dir, save_name)
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"图表已保存: {save_path}")
        
    def generate_all_plots(self, results_df):
        """
        生成所有可视化图表
        
        Args:
            results_df: 结果DataFrame
        """
        print("\n生成可视化图表...")
        
        self.plot_metrics_comparison(results_df)
        self.plot_recall_comparison(results_df)
        self.plot_coverage_comparison(results_df)
        self.plot_diversity_comparison(results_df)
        self.plot_radar_chart(results_df)
        self.plot_all_metrics(results_df)
        
        print("所有图表生成完成!")


if __name__ == '__main__':
    # 测试代码
    # 创建模拟数据
    test_results = pd.DataFrame({
        'recall': [0.15, 0.12, 0.18],
        'precision': [0.08, 0.06, 0.10],
        'f1_score': [0.10, 0.08, 0.12],
        'coverage': [0.25, 0.45, 0.35],
        'diversity': [0.65, 0.75, 0.70]
    }, index=['CF', 'CB', 'Hybrid'])
    
    visualizer = RecommenderVisualizer()
    visualizer.generate_all_plots(test_results)