import os
import sys
import argparse
from collections import Counter, defaultdict
import numpy as np
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
# 设置中文字体
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
matplotlib.rcParams['axes.unicode_minus'] = False     # 用来正常显示负号

def read_decoding(decoding_path):
    mapping = {}
    if not os.path.exists(decoding_path):
        return mapping
    
    with open(decoding_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            # 期望格式: CODE 描述...
            code = parts[0]
            desc = ' '.join(parts[1:]).strip()
            mapping[code] = desc
    
    return mapping

def read_data(data_path):
    ids = []
    sexes = []
    pops = []
    genotypes = []
    
    with open(data_path, 'r', encoding='utf-8') as f:
        for lineno, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 4:
                raise ValueError(f"第 {lineno+1} 行列数不足")
            
            ids.append(parts[0])
            sexes.append(parts[1])
            pops.append(parts[2])
            genotypes.append(parts[3:])  # 基因型数据从第4列开始
    
    genotypes = np.array(genotypes, dtype=object)  # shape (n_samples, n_snps) 字符串类型
    return ids, sexes, pops, genotypes

def to_binary_matrix(genotypes):
    print("正在转换数据格式...")
    
    n_samples, n_snps = genotypes.shape
    X = np.zeros((n_samples, n_snps), dtype=np.float32)
    
    # 对每一列（每个SNP位点）求众数
    for j in range(n_snps):
        col = genotypes[:, j]
        # 计算众数（最常见的核苷酸）
        cnt = Counter(col)
        mode, _ = cnt.most_common(1)[0]
        # 标记不等于众数的位置为1
        X[:, j] = (col != mode).astype(np.float32)
        
        if j % 2000 == 0:
            print(f"  进度: {j+1}/{n_snps}")
    
    print("数据转换完成")
    return X

def center_columns(X):
    col_means = X.mean(axis=0)
    return X - col_means, col_means

def plot_pc_scatter(scores, pops, pop2label, outpath, pcx=1, pcy=2):
    unique_pops = sorted(set(pops))
    # 颜色映射
    cmap = plt.get_cmap('tab10')
    color_map = {p: cmap(i % 10) for i, p in enumerate(unique_pops)}
    
    plt.figure(figsize=(10, 8))
    for p in unique_pops:
        idx = [i for i, pp in enumerate(pops) if pp == p]
        label = pop2label.get(p, p)  # 如果有解码就用解码，否则用原代码
        plt.scatter(scores[idx, pcx-1], scores[idx, pcy-1], s=15, 
                   color=color_map[p], label=label, alpha=0.7)
    
    plt.xlabel(f'主成分 {pcx}')
    plt.ylabel(f'主成分 {pcy}')
    plt.title(f'PC{pcx} vs PC{pcy}')
    plt.legend(markerscale=2, fontsize='small', loc='best')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(outpath, dpi=200, bbox_inches='tight')
    plt.close()

def plot_third_component_abs(component_vec, outpath):
    indices = np.arange(1, len(component_vec)+1)  # 1-based索引
    
    plt.figure(figsize=(12, 6))
    plt.plot(indices, np.abs(component_vec), linewidth=0.8, color='blue')
    plt.xlabel('SNP索引')
    plt.ylabel('第三主成分系数绝对值')
    plt.title('第三主成分系数绝对值分布')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(outpath, dpi=200, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='基因组数据的主成分分析')
    parser.add_argument('--data', default='p4dataset2024.txt', 
                       help='数据文件路径（默认：当前目录下的p4dataset2024.txt）')
    parser.add_argument('--decoding', default='p4dataset2024_decoding.txt', 
                       help='解码文件路径（默认：当前目录下的p4dataset2024_decoding.txt）')
    parser.add_argument('--outdir', default='.', 
                       help='输出目录（默认：当前目录）')
    args = parser.parse_args()

    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 处理文件路径：如果是相对路径，则相对于脚本目录
    if not os.path.isabs(args.data):
        data_path = os.path.join(script_dir, args.data)
    else:
        data_path = args.data
        
    if not os.path.isabs(args.decoding):
        decoding_path = os.path.join(script_dir, args.decoding)
    else:
        decoding_path = args.decoding

    # 如果默认解码文件不存在，尝试其他可能的命名
    if not os.path.exists(decoding_path):
        alt_names = [
            'p4dataset2024decoding.txt',  # 无下划线
            'p4dataset2024_decode.txt',   # decode代替decoding
            'decoding.txt'                # 简化命名
        ]
        
        for alt_name in alt_names:
            alt_path = os.path.join(script_dir, alt_name)
            if os.path.exists(alt_path):
                decoding_path = alt_path
                break

    # 检查数据文件是否存在
    if not os.path.exists(data_path):
        print(f"错误：找不到数据文件 {data_path}", file=sys.stderr)
        sys.exit(1)

    # 创建输出目录
    os.makedirs(args.outdir, exist_ok=True)

    print("开始基因组数据PCA分析...")
    
    # 读取解码文件（如果存在）
    pop2label = read_decoding(decoding_path)
    if pop2label:
        print(f"读取到 {len(pop2label)} 个人群标签")
    
    # 读取基因型数据
    print("正在读取基因型数据...")
    ids, sexes, pops, genotypes = read_data(data_path)
    n_samples, n_snps = genotypes.shape
    print(f"数据规模: {n_samples} 个样本, {n_snps} 个SNP位点")
    print(f"人群类别: {sorted(set(pops))}")

    # 构造二值矩阵并中心化
    X = to_binary_matrix(genotypes)
    Xc, col_means = center_columns(X)
    print("数据预处理完成")

    # PCA分析
    print("正在进行PCA分析...")
    n_components = min(10, n_snps, n_samples)
    pca = PCA(n_components=n_components, svd_solver='auto', whiten=False)
    scores = pca.fit_transform(Xc)
    components = pca.components_
    explained = pca.explained_variance_ratio_
    print("PCA分析完成")

    # 输出维度信息
    print(f"\n维度信息:")
    print(f"  主成分矩阵: {components.shape}")
    print(f"  投影矩阵: {scores.shape}")

    # 绘图
    print("\n正在生成图像...")
    out1 = os.path.join(args.outdir, 'pc1_vs_pc2.png')
    plot_pc_scatter(scores, pops, pop2label, out1, pcx=1, pcy=2)
    print(f"  保存: pc1_vs_pc2.png")

    if components.shape[0] >= 3:
        out2 = os.path.join(args.outdir, 'pc1_vs_pc3.png')
        plot_pc_scatter(scores, pops, pop2label, out2, pcx=1, pcy=3)
        print(f"  保存: pc1_vs_pc3.png")
        
        pc3 = components[2, :]
        out3 = os.path.join(args.outdir, 'abs_pc3_vs_snpindex.png')
        plot_third_component_abs(pc3, out3)
        print(f"  保存: abs_pc3_vs_snpindex.png")

    # 方差解释
    first_var_pct = explained[0] * 100
    if len(explained) >= 3:
        top3_var_pct = explained[:3].sum() * 100
        print(f"\n方差解释:")
        print(f"  第一主成分: {first_var_pct:.2f}%")
        print(f"  前三主成分: {top3_var_pct:.2f}%")

    print(f"\n分析完成！结果保存在: {os.path.abspath(args.outdir)}")

if __name__ == '__main__':
    main()
