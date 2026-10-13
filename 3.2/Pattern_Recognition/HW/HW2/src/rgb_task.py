"""
rgb_task.py — 基于 PCA 的彩色图像压缩与重建实验

"""

import os
import sys
import time
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 将 src 目录加入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pca_core import PCA


# ============================================================
# 全局配置
# ============================================================
IMG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'img')
os.makedirs(IMG_DIR, exist_ok=True)

K_LIST = [10, 50, 100, 150]


def load_rgb_image(image_path: str):
    """
    读取 RGB 彩色图像，返回三个通道的矩阵。

    """
    print(f"[rgb_task] 正在加载彩色图像: {image_path}")
    img = Image.open(image_path).convert('RGB')
    W, H = img.size
    print(f"[rgb_task] 图像尺寸: {H}×{W}")

    # 转换为 numpy 数组并归一化到 [0, 1]
    img_array = np.array(img, dtype=np.float64) / 255.0

    channels = {
        'R': img_array[:, :, 0],
        'G': img_array[:, :, 1],
        'B': img_array[:, :, 2],
    }

    return channels, H, W


def compress_channel_pca(channel: np.ndarray, k: int):
    """
    使用 PCA 对单个通道进行压缩与重建。

    将通道视为 H×W 矩阵，以每一列为一个样本（H 维），共 W 个样本。
    降维到 k 维后重建。

    """
    H, W = channel.shape

    # 按列压缩：转置使每列成为样本
    # X shape: (W, H) — W 个样本，每个样本 H 维
    X = channel.T.copy()

    t_start = time.perf_counter()

    pca = PCA(n_components=k)
    Z = pca.fit_transform(X)       # (W, k)
    X_recon = pca.inverse_transform(Z)  # (W, H)

    elapsed = time.perf_counter() - t_start

    # 转置回 (H, W)
    recon = X_recon.T

    # 裁剪到 [0, 1] 范围（重建可能略有超出）
    recon = np.clip(recon, 0.0, 1.0)

    # 计算压缩比
    # 原始: H × W
    # 压缩: k × W (投影坐标) + k × H (主成分) + H (均值)
    original_size = H * W
    compressed_size = k * W + k * H + H
    compression_ratio = compressed_size / original_size

    # 计算 RMSE
    rmse = np.sqrt(np.mean((channel - recon) ** 2))

    return recon, compression_ratio, rmse, elapsed


def merge_channels(ch_r, ch_g, ch_b):
    """将三个通道合并为 RGB 图像数组。"""
    H, W = ch_r.shape
    rgb = np.zeros((H, W, 3), dtype=np.float64)
    rgb[:, :, 0] = ch_r
    rgb[:, :, 1] = ch_g
    rgb[:, :, 2] = ch_b
    return np.clip(rgb, 0.0, 1.0)


def plot_rgb_comparison(original: np.ndarray, reconstructions: dict,
                        save_path: str):
    """
    绘制原始图像与不同 k 值重建图像的对比图。

    Parameters
    ----------
    original : np.ndarray, shape (H, W, 3)
        原始 RGB 图像。
    reconstructions : dict
        键为 k 值，值为对应的重建 RGB 图像数组。
    save_path : str
        保存路径。
    """
    k_values = sorted(reconstructions.keys())
    n_total = 1 + len(k_values)

    fig, axes = plt.subplots(1, n_total, figsize=(3.5 * n_total, 4))

    # 原始图像
    axes[0].imshow(original)
    axes[0].set_title('Original', fontsize=13, fontweight='bold')
    axes[0].axis('off')

    # 各 k 值重建图像
    for j, k in enumerate(k_values):
        axes[j + 1].imshow(reconstructions[k])
        axes[j + 1].set_title(f'k={k}', fontsize=13, fontweight='bold')
        axes[j + 1].axis('off')

    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"[rgb_task] RGB 对比图已保存至: {save_path}")


def plot_metrics(k_list: list, metrics: dict, save_path: str):
    """
    绘制压缩比和重建误差随 k 变化的折线图。
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # 定义颜色
    colors = {'R': '#e74c3c', 'G': '#2ecc71', 'B': '#3498db'}

    # 子图1: 压缩比
    for ch_name in ['R', 'G', 'B']:
        ratios = [metrics[k]['compression_ratio'][ch_name] for k in k_list]
        axes[0].plot(k_list, ratios, 'o-', color=colors[ch_name],
                     linewidth=1.8, markersize=7, label=f'{ch_name} channel')
    axes[0].set_xlabel('Number of Components (k)', fontsize=11)
    axes[0].set_ylabel('Compression Ratio', fontsize=11)
    axes[0].set_title('Compression Ratio vs. k', fontsize=12, fontweight='bold')
    axes[0].legend(fontsize=9)
    axes[0].grid(alpha=0.3)

    # 子图2: RMSE
    for ch_name in ['R', 'G', 'B']:
        rmses = [metrics[k]['rmse'][ch_name] for k in k_list]
        axes[1].plot(k_list, rmses, 's-', color=colors[ch_name],
                     linewidth=1.8, markersize=7, label=f'{ch_name} channel')
    axes[1].set_xlabel('Number of Components (k)', fontsize=11)
    axes[1].set_ylabel('RMSE', fontsize=11)
    axes[1].set_title('Reconstruction RMSE vs. k', fontsize=12, fontweight='bold')
    axes[1].legend(fontsize=9)
    axes[1].grid(alpha=0.3)

    # 子图3: 计算时间
    for ch_name in ['R', 'G', 'B']:
        times = [metrics[k]['time'][ch_name] for k in k_list]
        axes[2].plot(k_list, times, 'd-', color=colors[ch_name],
                     linewidth=1.8, markersize=7, label=f'{ch_name} channel')
    axes[2].set_xlabel('Number of Components (k)', fontsize=11)
    axes[2].set_ylabel('Computation Time (s)', fontsize=11)
    axes[2].set_title('Computation Time vs. k', fontsize=12, fontweight='bold')
    axes[2].legend(fontsize=9)
    axes[2].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[rgb_task] 指标折线图已保存至: {save_path}")


def main():
    """主函数：执行完整的彩色图像 PCA 压缩实验。"""
    print("=" * 60)
    print("彩色图像 PCA 压缩实验")
    print("=" * 60)

    # ---- 1. 加载图像 ----
    image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              'data', 'woman.png')
    channels, H, W = load_rgb_image(image_path)

    # 构建原始 RGB 图像数组
    original_rgb = merge_channels(channels['R'], channels['G'], channels['B'])

    # ---- 2. 对不同 k 值进行压缩与重建 ----
    metrics = {}
    reconstructions_rgb = {}

    for k in K_LIST:
        print(f"\n[rgb_task] k={k}: 压缩中...")

        recon_channels = {}
        metrics[k] = {
            'compression_ratio': {},
            'rmse': {},
            'time': {},
        }

        for ch_name in ['R', 'G', 'B']:
            recon, comp_ratio, rmse, elapsed = compress_channel_pca(
                channels[ch_name], k
            )
            recon_channels[ch_name] = recon
            metrics[k]['compression_ratio'][ch_name] = comp_ratio
            metrics[k]['rmse'][ch_name] = rmse
            metrics[k]['time'][ch_name] = elapsed

            print(f"  {ch_name} 通道 | 压缩比: {comp_ratio:.4f} | "
                  f"RMSE: {rmse:.6f} | 耗时: {elapsed:.4f}s")

        recon_rgb = merge_channels(recon_channels['R'],
                                   recon_channels['G'],
                                   recon_channels['B'])
        reconstructions_rgb[k] = recon_rgb

    # ---- 3. 绘制对比图 ----
    plot_rgb_comparison(original_rgb, reconstructions_rgb,
                        os.path.join(IMG_DIR, 'rgb_comparison.jpg'))

    # 单独为每个 k 值绘制一组对比图
    for k in K_LIST:
        plot_rgb_comparison(original_rgb, {k: reconstructions_rgb[k]},
                            os.path.join(IMG_DIR, f'rgb_recovered_k{k}.jpg'))

    # ---- 4. 绘制指标折线图 ----
    plot_metrics(K_LIST, metrics, os.path.join(IMG_DIR, 'rgb_metrics.jpg'))

    print("\n" + "=" * 60)
    print("彩色图像 PCA 实验完成！所有结果已保存至 img/ 目录。")
    print("=" * 60)


if __name__ == "__main__":
    main()
