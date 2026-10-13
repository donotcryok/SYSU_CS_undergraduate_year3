"""
face_task.py — 基于 PCA 的 Eigen Face 人脸压缩与重建实验
"""

import os
import sys
import numpy as np
import scipy.io as sio
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，用于服务器/命令行运行
import matplotlib.pyplot as plt

# 将 src 目录加入路径，以便导入 pca_core 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pca_core import PCA

# 图像保存目录
IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'img')
os.makedirs(IMG_DIR, exist_ok=True)

# 人脸图像尺寸（faces.mat 中每张人脸为 32×32 = 1024 维）
FACE_H, FACE_W = 32, 32

# 降维维度列表
K_LIST = [10, 50, 100, 150]

# 展示的人脸索引（从数据集中选择若干张用于对比展示）
DISPLAY_INDICES = [0, 23, 45, 67, 89]  # 选择 5 张人脸进行对比展示


def load_faces_data(mat_path: str):
    """
    加载 faces.mat 人脸数据集。
    """
    print(f"[face_task] 正在加载人脸数据: {mat_path}")
    data = sio.loadmat(mat_path)

    # 查找数据变量名（常见: 'X', 'faces', 'data'）
    # faces.mat 中存储的变量通常为 'X'
    if 'X' in data:
        X = data['X']
    elif 'faces' in data:
        X = data['faces']
    elif 'data' in data:
        X = data['data']
    else:
        # 尝试第一个非系统变量
        valid_keys = [k for k in data.keys() if not k.startswith('__')]
        X = data[valid_keys[0]]

    # 确保为 2D 数组: (n_samples, n_features)
    if X.ndim != 2:
        raise ValueError(f"人脸数据维度异常: {X.shape}，期望为 2D 数组。")

    n_faces, n_features = X.shape
    print(f"[face_task] 加载完成: {n_faces} 张人脸，每张 {n_features} 维 ({FACE_H}×{FACE_W})")
    print(f"[face_task] 数据范围: [{X.min():.4f}, {X.max():.4f}]")

    return X


def plot_eigenfaces(pca: PCA, save_path: str):
    """
    提取前 49 个主成分（Eigenfaces），拼接为 7×7 网格并保存。
    """
    n_eigen = min(49, pca.n_components)
    n_cols = 7
    n_rows = 7

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(10, 10))
    fig.suptitle('Top 49 Eigenfaces', fontsize=14, fontweight='bold')

    for i in range(n_eigen):
        row, col = divmod(i, n_cols)
        # 主成分方向存储在 components_ 中，每一列为一个主成分
        eigenface = pca.components_[:, i].reshape(FACE_H, FACE_W)

        # 归一化到 [0, 1] 以便显示
        eigenface_norm = (eigenface - eigenface.min()) / (eigenface.max() - eigenface.min() + 1e-8)

        axes[row, col].imshow(eigenface_norm, cmap='gray')
        axes[row, col].set_title(f'PC{i+1}', fontsize=7)
        axes[row, col].axis('off')

    # 若不足 49 个，隐藏多余子图
    for i in range(n_eigen, n_rows * n_cols):
        row, col = divmod(i, n_cols)
        axes[row, col].axis('off')

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[face_task] Eigenfaces 已保存至: {save_path}")


def plot_recovered_faces(originals: np.ndarray, reconstructions: dict,
                         indices: list, save_path: str):
    """
    绘制原始人脸与不同 k 值重建人脸的对比图。
    """
    n_faces = len(indices)
    n_methods = 1 + len(reconstructions)  # 原始 + 各 k 的重建
    k_values = sorted(reconstructions.keys())

    fig, axes = plt.subplots(n_faces, n_methods, figsize=(2.5 * n_methods, 2.5 * n_faces))

    # 处理单行情况
    if n_faces == 1:
        axes = axes.reshape(1, -1)

    # 列标题
    col_titles = ['Original'] + [f'k={k}' for k in k_values]
    for j, title in enumerate(col_titles):
        axes[0, j].set_title(title, fontsize=12, fontweight='bold')

    for i, idx in enumerate(indices):
        # 原始图像
        orig_img = originals[idx].reshape(FACE_H, FACE_W)
        axes[i, 0].imshow(orig_img, cmap='gray')
        axes[i, 0].axis('off')
        if i == 0:
            axes[i, 0].set_title('Original', fontsize=12, fontweight='bold')

        # 各 k 的重建图像
        for j, k in enumerate(k_values):
            recon_img = reconstructions[k][idx].reshape(FACE_H, FACE_W)
            axes[i, j + 1].imshow(recon_img, cmap='gray')
            axes[i, j + 1].axis('off')

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[face_task] 重建对比图已保存至: {save_path}")


def plot_variance_curve(pca: PCA, save_path: str):
    """
    绘制方差贡献率曲线（累计方差解释率随主成分数量变化的折线图）。
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 子图1: 逐个主成分的方差贡献率
    axes[0].bar(range(1, len(pca.explained_variance_ratio_) + 1),
                pca.explained_variance_ratio_, alpha=0.7, color='steelblue', edgecolor='white')
    axes[0].set_xlabel('Principal Component Index', fontsize=11)
    axes[0].set_ylabel('Explained Variance Ratio', fontsize=11)
    axes[0].set_title('Individual Explained Variance Ratio', fontsize=12, fontweight='bold')
    axes[0].grid(axis='y', alpha=0.3)

    # 标记前 k 列表中的值
    for k in K_LIST:
        if k <= len(pca.explained_variance_ratio_):
            cumsum = np.cumsum(pca.explained_variance_ratio_)
            axes[0].axvline(x=k, color='crimson', linestyle='--', alpha=0.5, linewidth=0.8)

    # 子图2: 累计方差贡献率
    cumsum = np.cumsum(pca.explained_variance_ratio_)
    axes[1].plot(range(1, len(cumsum) + 1), cumsum, 'b-', linewidth=1.5)
    axes[1].set_xlabel('Number of Principal Components', fontsize=11)
    axes[1].set_ylabel('Cumulative Explained Variance Ratio', fontsize=11)
    axes[1].set_title('Cumulative Explained Variance Ratio', fontsize=12, fontweight='bold')
    axes[1].grid(alpha=0.3)

    # 标注 k 值对应的累计贡献率
    for k in K_LIST:
        if k <= len(cumsum):
            axes[1].scatter(k, cumsum[k-1], color='crimson', s=60, zorder=5)
            axes[1].annotate(f'k={k}\n{cumsum[k-1]:.3f}',
                             (k, cumsum[k-1]),
                             textcoords="offset points",
                             xytext=(10, -15),
                             fontsize=8, color='crimson')

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[face_task] 方差曲线已保存至: {save_path}")


def main():
    """主函数：执行完整的人脸 PCA 压缩实验。"""
    print("=" * 60)
    print("Eigen Face PCA 压缩实验")
    print("=" * 60)

    # ---- 1. 加载数据 ----
    mat_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'data', 'faces.mat')
    X = load_faces_data(mat_path)
    n_faces, n_features = X.shape

    # ---- 2. 全成分 PCA 拟合，用于方差分析 ----
    print(f"\n[face_task] 正在拟合全成分 PCA（用于方差分析）...")
    pca_full = PCA(n_components=None)
    pca_full.fit(X)
    total_components = pca_full.n_components
    print(f"[face_task] 总主成分数: {total_components}")

    # ---- 3. 绘制方差贡献率曲线 ----
    plot_variance_curve(pca_full, os.path.join(IMG_DIR, 'face_variance.jpg'))

    # ---- 4. 提取前 49 个 Eigenfaces 并可视化 ----
    # 使用一个仅取 49 个成分的 PCA 模型
    pca_49 = PCA(n_components=49)
    pca_49.fit(X)
    plot_eigenfaces(pca_49, os.path.join(IMG_DIR, 'eigen_faces.jpg'))

    # ---- 5. 对不同 k 值进行降维与重建 ----
    reconstructions = {}
    for k in K_LIST:
        print(f"\n[face_task] k={k}: 降维中...")
        pca_k = PCA(n_components=k)
        Z = pca_k.fit_transform(X)
        X_recon = pca_k.inverse_transform(Z)

        # 计算重建误差 (RMSE)
        rmse = np.sqrt(np.mean((X - X_recon) ** 2))
        reconstructions[k] = X_recon

        cum_var = pca_k.explained_variance_ratio_.sum()
        compression = pca_k.n_components / n_features
        print(f"  k={k:3d} | 累计方差贡献率: {cum_var:.4f} | "
              f"RMSE: {rmse:.6f} | 维度压缩比: {compression:.4f}")

    # ---- 6. 绘制重建对比图 ----
    plot_recovered_faces(X, reconstructions, DISPLAY_INDICES,
                         os.path.join(IMG_DIR, 'recovered_faces_comparison.jpg'))

    # 单独为每个 k 值绘制一组对比图（用于报告）
    for k in K_LIST:
        plot_recovered_faces(X, {k: reconstructions[k]}, DISPLAY_INDICES,
                             os.path.join(IMG_DIR, f'recovered_faces_top_{k}.jpg'))

    print("\n" + "=" * 60)
    print("Eigen Face 实验完成！所有结果已保存至 img/ 目录。")
    print("=" * 60)


if __name__ == "__main__":
    main()
