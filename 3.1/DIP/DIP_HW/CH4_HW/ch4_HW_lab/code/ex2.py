import numpy as np
import cv2
import matplotlib.pyplot as plt
import os
from ex1 import fft_2d, ifft_2d, display_spectrum

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def create_gaussian_lpf(M, N, sigma):
    """创建高斯低通滤波器"""
    # 创建频域坐标
    u = np.arange(M) - M // 2
    v = np.arange(N) - N // 2
    U, V = np.meshgrid(v, u)
    
    # 计算距离矩阵
    D_squared = U**2 + V**2
    
    # 高斯低通滤波器
    H = np.exp(-D_squared / (2 * sigma**2))
    
    return H

def find_optimal_sigma(spectrum, target_energy_ratio=0.95):
    """找到使能量占比达到目标值的最优sigma"""
    M, N = spectrum.shape
    total_energy = np.sum(np.abs(spectrum)**2)
    target_energy = total_energy * target_energy_ratio
    
    # 二分搜索找最优sigma
    sigma_low, sigma_high = 1, min(M, N) // 2
    tolerance = 0.001
    
    while sigma_high - sigma_low > tolerance:
        sigma = (sigma_low + sigma_high) / 2
        H = create_gaussian_lpf(M, N, sigma)
        
        # 计算滤波后的能量
        filtered_spectrum = spectrum * H
        filtered_energy = np.sum(np.abs(filtered_spectrum)**2)
        energy_ratio = filtered_energy / total_energy
        
        if energy_ratio < target_energy_ratio:
            sigma_low = sigma
        else:
            sigma_high = sigma
    
    return (sigma_low + sigma_high) / 2

def process_fig3_gaussian_filter():
    """处理fig3的高斯低通滤波"""
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 查找fig3图像
    img_folder = os.path.join(current_dir, "img")
    if not os.path.exists(img_folder):
        alt_paths = [
            os.path.join(current_dir, "img"),
            os.path.join(current_dir, "code", "img"),
            os.path.join(os.path.dirname(current_dir), "img")
        ]
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                img_folder = alt_path
                break
    
    # 找到fig3文件
    fig3_path = None
    possible_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']
    for ext in possible_extensions:
        test_path = os.path.join(img_folder, 'fig3' + ext)
        if os.path.exists(test_path):
            fig3_path = test_path
            break
    
    if fig3_path is None:
        print("未找到fig3图像文件")
        return
    
    print("=== fig3高斯低通滤波处理 ===")
    print(f"处理文件: {fig3_path}")
    
    # (a) 读取原始图像f
    f = cv2.imread(fig3_path, cv2.IMREAD_GRAYSCALE)
    if f is None:
        print("无法读取fig3图像")
        return
    
    M, N = f.shape
    print(f"图像尺寸: {M}x{N}")
    
    # 检查是否为2的幂，如果不是则填充
    if (M & (M - 1)) != 0 or (N & (N - 1)) != 0:
        # 填充到最接近的2的幂
        new_M = 2 ** int(np.ceil(np.log2(M)))
        new_N = 2 ** int(np.ceil(np.log2(N)))
        
        # 创建填充的图像
        padded_f = np.zeros((new_M, new_N))
        padded_f[:M, :N] = f
        f_work = padded_f
        print(f"填充后尺寸: {new_M}x{new_N}")
    else:
        f_work = f.copy()
        new_M, new_N = M, N
    
    f_work = f_work.astype(np.float64)
    
    # (b) 对f进行填充并乘以(-1)^(x+y)得到fp
    x, y = np.meshgrid(np.arange(new_N), np.arange(new_M))
    multiplier = (-1) ** (x + y)
    fp = f_work * multiplier
    
    # (c) 计算fp的DFT得到F
    print("计算2D FFT...")
    F = fft_2d(fp)
    
    # (d) 生成高斯低通滤波器H，使能量占95%
    print("生成高斯低通滤波器...")
    optimal_sigma = find_optimal_sigma(F, target_energy_ratio=0.95)
    H = create_gaussian_lpf(new_M, new_N, optimal_sigma)
    print(f"最优sigma: {optimal_sigma:.2f}")
    
    # 验证能量比例
    total_energy = np.sum(np.abs(F)**2)
    filtered_energy = np.sum(np.abs(F * H)**2)
    actual_ratio = filtered_energy / total_energy
    print(f"实际能量占比: {actual_ratio:.3f}")
    
    # (e) 计算HF
    HF = H * F
    
    # (f) 计算HF的频谱
    HF_magnitude = np.abs(HF)
    
    # (g) 对HF进行IDFT得到gp
    print("计算2D IFFT...")
    gp = ifft_2d(HF)
    gp_real = np.real(gp)
    
    # (h) 对gp乘以(-1)^(x+y)并提取前M行N列得到g
    g_full = gp_real * multiplier
    g = g_full[:M, :N]  # 提取原始尺寸
    
    # 显示8个子图
    plt.figure(figsize=(20, 10))
    
    # (a) 原始图像f
    plt.subplot(2, 4, 1)
    plt.imshow(f, cmap='gray')
    plt.title('(a) 原始图像f')
    plt.axis('off')
    
    # (b) 填充并乘以(-1)^(x+y)后的图像fp
    plt.subplot(2, 4, 2)
    plt.imshow(fp, cmap='gray')
    plt.title('(b) 预处理图像fp')
    plt.axis('off')
    
    # (c) fp乘以(-1)^(x+y)后的结果(用于显示)
    fp_display = fp * multiplier
    plt.subplot(2, 4, 3)
    plt.imshow(fp_display, cmap='gray')
    plt.title('(c) fp×(-1)^(x+y)')
    plt.axis('off')
    
    # (d) F的频谱
    plt.subplot(2, 4, 4)
    F_shifted = np.fft.fftshift(F)
    F_display = display_spectrum(F_shifted)
    plt.imshow(F_display, cmap='hot')
    plt.title('(d) F的频谱')
    plt.axis('off')
    
    # (e) 高斯低通滤波器H
    plt.subplot(2, 4, 5)
    H_shifted = np.fft.fftshift(H)
    plt.imshow(H_shifted, cmap='gray')
    plt.title(f'(e) 高斯低通滤波器H\n(σ={optimal_sigma:.1f})')
    plt.axis('off')
    
    # (f) HF的频谱
    plt.subplot(2, 4, 6)
    HF_shifted = np.fft.fftshift(HF)
    HF_display = display_spectrum(HF_shifted)
    plt.imshow(HF_display, cmap='hot')
    plt.title('(f) 滤波后频谱HF')
    plt.axis('off')
    
    # (g) IDFT结果gp
    plt.subplot(2, 4, 7)
    plt.imshow(gp_real, cmap='gray')
    plt.title('(g) IDFT结果gp')
    plt.axis('off')
    
    # (h) 最终结果g
    plt.subplot(2, 4, 8)
    plt.imshow(g, cmap='gray')
    plt.title('(h) 最终滤波结果g')
    plt.axis('off')
    
    plt.tight_layout()
    
    # 保存结果
    output_path = os.path.join(current_dir, 'fig3_gaussian_filter_result.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"结果已保存到: {output_path}")
    plt.show()
    
    # 输出统计信息
    print(f"\n=== 处理结果统计 ===")
    print(f"高斯滤波器sigma: {optimal_sigma:.3f}")
    print(f"能量保留比例: {actual_ratio:.3f}")
    print(f"原图像尺寸: {M}x{N}")
    print(f"处理尺寸: {new_M}x{new_N}")

def main():
    """主函数"""
    process_fig3_gaussian_filter()

if __name__ == "__main__":
    main()
