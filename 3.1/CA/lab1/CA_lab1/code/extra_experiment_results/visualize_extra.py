import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10

VIS_PATH = os.path.dirname(__file__)  # 保存到当前目录

def load_and_clean_extra_data(csv_file='extra_results.csv'):
    """加载和清理扩展实验数据"""
    try:
        df = pd.read_csv(csv_file)
        # 移除ERROR行
        df = df[df['NumCycles'] != 'ERROR']
        # 转换数据类型
        numeric_columns = ['NumCycles', 'L1DCacheMisses', 'L2CacheMisses', 'L1DHitRate', 'L2HitRate']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 填充空值
        df = df.fillna(0)
        
        print("扩展实验数据加载成功！")
        print(f"数据形状: {df.shape}")
        print("\n数据预览:")
        print(df.head())
        return df
    except FileNotFoundError:
        print(f"未找到扩展实验数据文件: {csv_file}")
        return None
    except Exception as e:
        print(f"加载数据时出错: {e}")
        return None

def create_cache_performance_analysis(df):
    """创建缓存性能分析图表（仅中文标注）"""
    if df is None or df.empty:
        print("没有数据可供分析")
        return
        
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 1. L1D缓存大小对性能的影响
    ax1 = axes[0, 0]
    l1d_performance = df.groupby('L1DSize')['NumCycles'].mean()
    ax1.plot(range(len(l1d_performance)), l1d_performance.values, 'o-', linewidth=2, markersize=8)
    ax1.set_xlabel('L1D缓存大小', fontsize=10)
    ax1.set_ylabel('平均时钟数', fontsize=10)
    ax1.set_title('L1D缓存大小对性能的影响', fontsize=12)
    ax1.set_xticks(range(len(l1d_performance)))
    ax1.set_xticklabels(l1d_performance.index, rotation=45)
    ax1.grid(True, alpha=0.3)
    
    # 2. L2缓存大小对性能的影响
    ax2 = axes[0, 1]
    l2_performance = df.groupby('L2Size')['NumCycles'].mean()
    ax2.plot(range(len(l2_performance)), l2_performance.values, 's-', linewidth=2, markersize=8, color='orange')
    ax2.set_xlabel('L2缓存大小', fontsize=10)
    ax2.set_ylabel('平均时钟数', fontsize=10)
    ax2.set_title('L2缓存大小对性能的影响', fontsize=12)
    ax2.set_xticks(range(len(l2_performance)))
    ax2.set_xticklabels(l2_performance.index, rotation=45)
    ax2.grid(True, alpha=0.3)
    
    # 3. 缓存命中率分析
    ax3 = axes[1, 0]
    cache_sizes = df['L1DSize'].unique()
    l1d_hit_rates = [df[df['L1DSize'] == size]['L1DHitRate'].mean() for size in cache_sizes]
    l2_hit_rates = [df[df['L1DSize'] == size]['L2HitRate'].mean() for size in cache_sizes]
    
    x = np.arange(len(cache_sizes))
    width = 0.35
    
    bars1 = ax3.bar(x - width/2, l1d_hit_rates, width, label='L1D命中率', alpha=0.8)
    bars2 = ax3.bar(x + width/2, l2_hit_rates, width, label='L2命中率', alpha=0.8)
    
    ax3.set_xlabel('缓存大小', fontsize=10)
    ax3.set_ylabel('命中率 (%)', fontsize=10)
    ax3.set_title('缓存命中率分析', fontsize=12)
    ax3.set_xticks(x)
    ax3.set_xticklabels(cache_sizes, rotation=45)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # 4. 性能热力图
    ax4 = axes[1, 1]
    heatmap_data = df.pivot(index='L1DSize', columns='L2Size', values='NumCycles')
    heatmap_data_display = heatmap_data / 1e6  # 转换为百万单位
    sns.heatmap(heatmap_data_display, annot=True, fmt='.2f', cmap='viridis_r', ax=ax4,
                cbar_kws={'label': '时钟数 (百万)'})
    ax4.set_title('缓存配置性能热力图', fontsize=12)
    ax4.set_xlabel('L2缓存大小', fontsize=10)
    ax4.set_ylabel('L1D缓存大小', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(os.path.join(VIS_PATH, 'cache_performance_analysis.png'), dpi=300, bbox_inches='tight')
    plt.show()

def generate_cache_summary_statistics(df):
    """生成缓存实验总结统计"""
    if df is None or df.empty:
        print("没有数据可供分析")
        return
        
    print("\n=== 缓存实验结果统计分析 ===")
    
    # 最佳配置
    best_idx = df['NumCycles'].idxmin()
    best_config = df.loc[best_idx]
    print(f"\n最佳缓存配置:")
    print(f"  L1D缓存大小: {best_config['L1DSize']}")
    print(f"  L2缓存大小: {best_config['L2Size']}")
    print(f"  时钟数: {best_config['NumCycles']:,.0f}")
    print(f"  L1D命中率: {best_config['L1DHitRate']:.2f}%")
    print(f"  L2命中率: {best_config['L2HitRate']:.2f}%")
    
    # 性能提升分析
    worst_idx = df['NumCycles'].idxmax()
    worst_cycles = df.loc[worst_idx, 'NumCycles']
    best_cycles = best_config['NumCycles']
    improvement = (worst_cycles - best_cycles) / worst_cycles * 100
    print(f"\n性能提升: {improvement:.1f}%")
    
    # 缓存大小敏感性分析
    print("\n缓存大小敏感性分析:")
    l1d_variance = df.groupby('L1DSize')['NumCycles'].var().mean()
    l2_variance = df.groupby('L2Size')['NumCycles'].var().mean()
    
    print(f"  L1D缓存大小变化方差: {l1d_variance:,.0f}")
    print(f"  L2缓存大小变化方差: {l2_variance:,.0f}")

def main():
    """主函数"""
    # 加载数据
    df = load_and_clean_extra_data()
    
    if df is not None and not df.empty:
        # 创建分析图表
        create_cache_performance_analysis(df)
        
        # 生成统计分析
        generate_cache_summary_statistics(df)
        
        print(f"\n缓存实验分析图表已保存到 {VIS_PATH} 目录")
    else:
        print("无法进行分析，请检查数据文件")

if __name__ == "__main__":
    main()
