import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib import rcParams
import matplotlib.font_manager as fm
import os

# 设置中文字体 - 更通用的配置
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
# 设置字体大小
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10

VIS_PATH = 'visulize_result'
os.makedirs(VIS_PATH, exist_ok=True)

def load_and_clean_data(csv_file='results.csv'):
    """加载和清理数据"""
    try:
        df = pd.read_csv(csv_file)
        # 填充空值为0
        df = df.fillna(0)
        print("数据加载成功！")
        print(f"数据形状: {df.shape}")
        print("\n数据预览:")
        print(df.head())
        return df
    except FileNotFoundError:
        print(f"未找到数据文件: {csv_file}\n请确认路径是否正确。")
        exit(1)

def create_performance_analysis(df):
    """创建性能分析图表"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. IQ条目数对性能的影响
    ax1 = axes[0, 0]
    iq_performance = df.groupby('IQEntries')['NumCycles'].mean()
    ax1.plot(iq_performance.index, iq_performance.values, 'o-', linewidth=2, markersize=8)
    ax1.set_xlabel('IQ Entries (IQ条目数)', fontsize=10)
    ax1.set_ylabel('Average Cycles (平均时钟数)', fontsize=10)
    ax1.set_title('IQ Entries Impact on CPU Performance\n(IQ条目数对CPU性能的影响)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    # 添加数值标注
    for x, y in zip(iq_performance.index, iq_performance.values):
        ax1.annotate(f'{y/1e6:.1f}M', (x, y), textcoords="offset points", xytext=(0,10), ha='center')
    
    # 2. ROB条目数对性能的影响
    ax2 = axes[0, 1]
    rob_performance = df.groupby('ROBEntries')['NumCycles'].mean()
    ax2.plot(rob_performance.index, rob_performance.values, 's-', linewidth=2, markersize=8, color='orange')
    ax2.set_xlabel('ROB Entries (ROB条目数)', fontsize=10)
    ax2.set_ylabel('Average Cycles (平均时钟数)', fontsize=10)
    ax2.set_title('ROB Entries Impact on CPU Performance\n(ROB条目数对CPU性能的影响)', fontsize=12)
    ax2.grid(True, alpha=0.3)
    # 添加数值标注
    for x, y in zip(rob_performance.index, rob_performance.values):
        ax2.annotate(f'{y/1e6:.1f}M', (x, y), textcoords="offset points", xytext=(0,10), ha='center')
    
    # 3. 物理寄存器数对性能的影响
    ax3 = axes[1, 0]
    phys_performance = df.groupby('PhysRegs')['NumCycles'].mean()
    ax3.plot(phys_performance.index, phys_performance.values, '^-', linewidth=2, markersize=8, color='green')
    ax3.set_xlabel('Physical Registers (物理寄存器数)', fontsize=10)
    ax3.set_ylabel('Average Cycles (平均时钟数)', fontsize=10)
    ax3.set_title('Physical Registers Impact on CPU Performance\n(物理寄存器数对CPU性能的影响)', fontsize=12)
    ax3.grid(True, alpha=0.3)
    # 添加数值标注
    for x, y in zip(phys_performance.index, phys_performance.values):
        ax3.annotate(f'{y/1e6:.1f}M', (x, y), textcoords="offset points", xytext=(0,10), ha='center')
    
    # 4. 综合性能对比热力图
    ax4 = axes[1, 1]
    subset_data = df[df['PhysRegs'] == 256]
    heatmap_data = subset_data.pivot(index='IQEntries', columns='ROBEntries', values='NumCycles')
    # 转换为百万单位显示
    heatmap_data_display = heatmap_data / 1e6
    sns.heatmap(heatmap_data_display, annot=True, fmt='.1f', cmap='viridis_r', ax=ax4, 
                cbar_kws={'label': 'Cycles (Million)'})
    ax4.set_title('Performance Heatmap (PhysRegs=256)\n(性能热力图, 物理寄存器=256)', fontsize=12)
    ax4.set_xlabel('ROB Entries (ROB条目数)', fontsize=10)
    ax4.set_ylabel('IQ Entries (IQ条目数)', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(os.path.join(VIS_PATH, 'performance_analysis.png'), dpi=300, bbox_inches='tight')
    plt.show()

def create_bottleneck_analysis(df):
    """创建瓶颈分析图表"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. ROB堵塞事件分析
    ax1 = axes[0, 0]
    rob_bottleneck = df.groupby('ROBEntries')['ROBFullEvents'].mean()
    rob_bottleneck = rob_bottleneck[rob_bottleneck > 0]
    if not rob_bottleneck.empty:
        bars1 = ax1.bar(rob_bottleneck.index.astype(str), rob_bottleneck.values, color='red', alpha=0.7)
        ax1.set_yscale('log')
        # 添加数值标注
        for bar, val in zip(bars1, rob_bottleneck.values):
            if val > 0:
                ax1.text(bar.get_x() + bar.get_width()/2, val, f'{val:.0e}', 
                        ha='center', va='bottom', fontsize=8)
    ax1.set_xlabel('ROB Entries (ROB条目数)', fontsize=10)
    ax1.set_ylabel('Average ROB Full Events\n(平均ROB堵塞事件数)', fontsize=10)
    ax1.set_title('ROB Bottleneck Analysis\n(ROB堵塞事件分析)', fontsize=12)
    
    # 2. IQ堵塞事件分析
    ax2 = axes[0, 1]
    iq_bottleneck = df.groupby('IQEntries')['IQFullEvents'].mean()
    iq_bottleneck = iq_bottleneck[iq_bottleneck > 0]
    if not iq_bottleneck.empty:
        bars2 = ax2.bar(iq_bottleneck.index.astype(str), iq_bottleneck.values, color='blue', alpha=0.7)
        ax2.set_yscale('log')
        # 添加数值标注
        for bar, val in zip(bars2, iq_bottleneck.values):
            if val > 0:
                ax2.text(bar.get_x() + bar.get_width()/2, val, f'{val:.0e}', 
                        ha='center', va='bottom', fontsize=8)
    ax2.set_xlabel('IQ Entries (IQ条目数)', fontsize=10)
    ax2.set_ylabel('Average IQ Full Events\n(平均IQ堵塞事件数)', fontsize=10)
    ax2.set_title('IQ Bottleneck Analysis\n(IQ堵塞事件分析)', fontsize=12)
    
    # 3. 寄存器堵塞事件分析
    ax3 = axes[1, 0]
    reg_bottleneck = df.groupby('PhysRegs')['FullRegistersEvents'].mean()
    reg_bottleneck = reg_bottleneck[reg_bottleneck > 0]
    if not reg_bottleneck.empty:
        bars3 = ax3.bar(reg_bottleneck.index.astype(str), reg_bottleneck.values, color='green', alpha=0.7)
        ax3.set_yscale('log')
        # 添加数值标注
        for bar, val in zip(bars3, reg_bottleneck.values):
            if val > 0:
                ax3.text(bar.get_x() + bar.get_width()/2, val, f'{val:.0e}', 
                        ha='center', va='bottom', fontsize=8)
    ax3.set_xlabel('Physical Registers (物理寄存器数)', fontsize=10)
    ax3.set_ylabel('Average Register Full Events\n(平均寄存器堵塞事件数)', fontsize=10)
    ax3.set_title('Register Bottleneck Analysis\n(物理寄存器堵塞事件分析)', fontsize=12)
    
    # 4. 瓶颈类型分布饼图
    ax4 = axes[1, 1]
    best_config = df.loc[df['NumCycles'].idxmin()]
    bottlenecks = {
        'ROB Full': best_config['ROBFullEvents'],
        'IQ Full': best_config['IQFullEvents'], 
        'Register Full': best_config['FullRegistersEvents']
    }
    bottlenecks = {k: v for k, v in bottlenecks.items() if pd.notna(v) and v > 0}
    if bottlenecks:
        wedges, texts, autotexts = ax4.pie(bottlenecks.values(), labels=bottlenecks.keys(), 
                                          autopct='%1.1f%%', startangle=90)
        ax4.set_title('Bottleneck Distribution (Best Config)\n(最佳配置下的瓶颈分布)', fontsize=12)
    else:
        ax4.text(0.5, 0.5, 'No Significant Bottleneck\nin Best Configuration\n(最佳配置下无明显瓶颈)', 
                ha='center', va='center', transform=ax4.transAxes, fontsize=10)
        ax4.set_title('Bottleneck Distribution (Best Config)\n(最佳配置下的瓶颈分布)', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(os.path.join(VIS_PATH, 'bottleneck_analysis.png'), dpi=300, bbox_inches='tight')
    plt.show()

def create_optimization_analysis(df):
    """创建优化路径分析"""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # 1. 参数优化效果对比
    ax1 = axes[0]
    configs = ['4,4', '16,16', '64,64', '256,256']
    cycles = []
    for config in configs:
        iq, rob = map(int, config.split(','))
        subset = df[(df['IQEntries'] == iq) & (df['ROBEntries'] == rob)]
        if not subset.empty:
            cycles.append(subset['NumCycles'].mean())
        else:
            cycles.append(np.nan)
    
    line = ax1.plot(configs, cycles, 'o-', linewidth=3, markersize=10, color='purple')[0]
    ax1.set_xlabel('Configuration (IQ,ROB)\n(配置 IQ,ROB)', fontsize=10)
    ax1.set_ylabel('Average Cycles\n(平均时钟数)', fontsize=10)
    ax1.set_title('Balanced Configuration Optimization Path\n(均衡配置优化路径)', fontsize=12)
    ax1.grid(True, alpha=0.3)
    # 添加数值标注
    for i, (config, cycle) in enumerate(zip(configs, cycles)):
        if not np.isnan(cycle):
            ax1.annotate(f'{cycle/1e6:.1f}M', (i, cycle), textcoords="offset points", 
                        xytext=(0,10), ha='center', fontsize=9)
    
    # 2. 最优配置分析
    ax2 = axes[1]
    top5 = df.nsmallest(5, 'NumCycles')
    config_labels = [f"P{int(row['PhysRegs'])}_I{int(row['IQEntries'])}_R{int(row['ROBEntries'])}" 
                    for _, row in top5.iterrows()]
    bars = ax2.bar(range(len(top5)), top5['NumCycles']/1e6, color='skyblue', alpha=0.8)
    ax2.set_xlabel('Configuration Rank (配置排名)', fontsize=10)
    ax2.set_ylabel('Cycles (Million)\n(时钟数 百万)', fontsize=10)
    ax2.set_title('Top 5 Best Configurations\n(Top 5 最佳配置)', fontsize=12)
    ax2.set_xticks(range(len(top5)))
    ax2.set_xticklabels(config_labels, rotation=45, ha='right')
    # 添加数值标注
    for bar, cycles in zip(bars, top5['NumCycles']):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{cycles:,.0f}', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(os.path.join(VIS_PATH, 'optimization_analysis.png'), dpi=300, bbox_inches='tight')
    plt.show()

def generate_summary_statistics(df):
    """生成总结统计"""
    print("\n=== 实验结果统计分析 ===")
    
    # 最佳配置
    best_idx = df['NumCycles'].idxmin()
    best_config = df.loc[best_idx]
    print(f"\n最佳配置:")
    print(f"  物理寄存器: {best_config['PhysRegs']}")
    print(f"  IQ条目数: {best_config['IQEntries']}")
    print(f"  ROB条目数: {best_config['ROBEntries']}")
    print(f"  时钟数: {best_config['NumCycles']:,.0f}")
    
    # 性能提升分析
    worst_idx = df['NumCycles'].idxmax()
    worst_cycles = df.loc[worst_idx, 'NumCycles']
    best_cycles = best_config['NumCycles']
    improvement = (worst_cycles - best_cycles) / worst_cycles * 100
    print(f"\n性能提升: {improvement:.1f}%")
    
    # 参数敏感性分析
    print("\n参数敏感性分析:")
    iq_variance = df.groupby('IQEntries')['NumCycles'].var().mean()
    rob_variance = df.groupby('ROBEntries')['NumCycles'].var().mean()
    phys_variance = df.groupby('PhysRegs')['NumCycles'].var().mean()
    
    print(f"  IQ条目数变化方差: {iq_variance:,.0f}")
    print(f"  ROB条目数变化方差: {rob_variance:,.0f}")
    print(f"  物理寄存器数变化方差: {phys_variance:,.0f}")

def main():
    """主函数"""
    # 加载数据
    df = load_and_clean_data()
    
    # 创建各种分析图表
    create_performance_analysis(df)
    create_bottleneck_analysis(df)
    create_optimization_analysis(df)
    
    # 生成统计分析
    generate_summary_statistics(df)
    
    print("\n所有图表已保存为PNG文件，可用于LaTeX文档插入。")

if __name__ == "__main__":
    main()
