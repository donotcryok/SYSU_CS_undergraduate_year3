import numpy as np
import cv2
import matplotlib.pyplot as plt
import os

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def is_power_of_two(n):
    """检查是否为2的幂"""
    return (n & (n - 1)) == 0 and n > 0

def resize_to_power_of_two(image):
    """将图像尺寸调整为2的幂"""
    M, N = image.shape
    
    # 找到最接近的2的幂
    new_M = 2 ** int(np.ceil(np.log2(M)))
    new_N = 2 ** int(np.ceil(np.log2(N)))
    
    # 调整图像尺寸
    resized = cv2.resize(image, (new_N, new_M), interpolation=cv2.INTER_LINEAR)
    return resized, (M, N)  # 返回调整后的图像和原始尺寸

def bit_reverse(a, n):
    """位反转函数"""
    result = [0] * n
    log2n = int(np.log2(n))
    for i in range(n):
        # 将索引转换为二进制，反转，再转回十进制
        binary_repr = format(i, f'0{log2n}b')
        reversed_binary = binary_repr[::-1]
        reversed_index = int(reversed_binary, 2)
        result[i] = a[reversed_index]
    return result

def fft_1d(x):
    """修正的一维快速傅里叶变换"""
    N = len(x)
    if N <= 1:
        return np.array(x, dtype=complex)
    
    if not is_power_of_two(N):
        raise ValueError(f"输入长度{N}必须是2的幂")
    
    # 位反转重排
    indices = bit_reverse(list(range(N)), N)
    x_reordered = [x[i] for i in indices]
    X = np.array(x_reordered, dtype=complex)
    
    # 蝶形运算
    length = 2
    while length <= N:
        half_len = length // 2
        # 主旋转因子
        w_m = np.exp(-2j * np.pi / length)
        
        for k in range(0, N, length):
            w = 1.0
            for j in range(half_len):
                # 蝶形运算
                u = X[k + j]
                v = w * X[k + j + half_len]
                X[k + j] = u + v
                X[k + j + half_len] = u - v
                w *= w_m  # 更新旋转因子
        length <<= 1  # 乘以2
    
    return X

def ifft_1d(X):
    """一维快速傅里叶逆变换"""
    N = len(X)
    # 使用公式：IFFT(X) = conj(FFT(conj(X))) / N
    return np.conj(fft_1d(np.conj(X))) / N

def fft_2d(image):
    """二维快速傅里叶变换"""
    M, N = image.shape
    
    # 对每一行进行FFT
    temp = np.zeros((M, N), dtype=complex)
    for i in range(M):
        temp[i, :] = fft_1d(image[i, :])
    
    # 对每一列进行FFT
    result = np.zeros((M, N), dtype=complex)
    for j in range(N):
        result[:, j] = fft_1d(temp[:, j])
    
    return result

def ifft_2d(spectrum):
    """二维快速傅里叶逆变换"""
    M, N = spectrum.shape
    
    # 对每一行进行IFFT
    temp = np.zeros((M, N), dtype=complex)
    for i in range(M):
        temp[i, :] = ifft_1d(spectrum[i, :])
    
    # 对每一列进行IFFT
    result = np.zeros((M, N), dtype=complex)
    for j in range(N):
        result[:, j] = ifft_1d(temp[:, j])
    
    return result

def display_spectrum(spectrum):
    """显示频谱（对数尺度）"""
    magnitude = np.abs(spectrum)
    # 避免log(0)
    magnitude[magnitude == 0] = 1e-10
    log_magnitude = np.log(1 + magnitude)
    return log_magnitude

def process_image(image_path, save_dir):
    """处理单个图像"""
    # 读取图像
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"无法读取图像: {image_path}")
        return
    
    # 检查尺寸是否为2的幂
    M, N = img.shape
    if (M & (M - 1)) != 0 or (N & (N - 1)) != 0:
        print(f"警告: 图像尺寸 {M}x{N} 不是2的幂")
        return
    
    # 转换为浮点数
    img_float = img.astype(np.float64)
    
    # 进行2D FFT和IFFT
    spectrum = fft_2d(img_float)
    reconstructed = ifft_2d(spectrum)
    reconstructed_real = np.real(reconstructed)
    
    # 验证重构误差
    error = np.mean(np.abs(img_float - reconstructed_real))
    
    # 显示结果
    plt.figure(figsize=(15, 5))
    
    # 原图
    plt.subplot(1, 3, 1)
    plt.imshow(img, cmap='gray')
    plt.title(f'原图 ({M}x{N})')
    plt.axis('off')
    
    # 频谱（中心化显示）
    plt.subplot(1, 3, 2)
    spectrum_shifted = np.fft.fftshift(spectrum)
    spectrum_display = display_spectrum(spectrum_shifted)
    plt.imshow(spectrum_display, cmap='hot')
    plt.title('频域谱（对数尺度）')
    plt.axis('off')
    
    # 重构图像
    plt.subplot(1, 3, 3)
    plt.imshow(reconstructed_real, cmap='gray')
    plt.title(f'重构图像 (误差: {error:.2e})')
    plt.axis('off')
    
    plt.tight_layout()
    
    # 保存到指定目录
    output_path = os.path.join(save_dir, f'fft_result_{os.path.splitext(os.path.basename(image_path))[0]}.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.show()
    
    return spectrum, reconstructed_real

def main():
    """主函数"""
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 图像路径 - 修正为相对路径
    img_folder = os.path.join(current_dir, "img")
    if not os.path.exists(img_folder):
        # 尝试其他可能的路径
        alt_paths = [
            os.path.join(current_dir, "img"),
            os.path.join(current_dir, "code", "img"),
            os.path.join(os.path.dirname(current_dir), "img")
        ]
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                img_folder = alt_path
                break
    
    image_files = ["fig1", "fig2"]  # 只处理fig1和fig2
    
    # 自动检测图像文件格式
    found_files = []
    for base_name in image_files:
        possible_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']
        
        found = False
        for ext in possible_extensions:
            test_path = os.path.join(img_folder, base_name + ext)
            if os.path.exists(test_path):
                found_files.append(base_name + ext)
                found = True
                break
        
        if not found:
            print(f"未找到 {base_name} 文件")
    
    print("=== 二维FFT演示 ===")
    
    results = {}
    
    for img_file in found_files:
        img_path = os.path.join(img_folder, img_file)
        if os.path.exists(img_path):
            print(f"处理 {img_file}...")
            try:
                spectrum, reconstructed = process_image(img_path, current_dir)
                results[img_file] = (spectrum, reconstructed)
            except Exception as e:
                print(f"处理 {img_file} 时发生错误: {e}")
    
    print(f"处理完成，共处理 {len(results)} 个图像")
    
    # 与numpy FFT的对比
    if results:
        print("\n与numpy.fft2的差异对比:")
        for img_file, (our_spectrum, _) in results.items():
            img_path = os.path.join(img_folder, img_file)
            if os.path.exists(img_path):
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    numpy_spectrum = np.fft.fft2(img)
                    diff = np.mean(np.abs(our_spectrum - numpy_spectrum))
                    print(f"{img_file}: {diff:.6f}")

if __name__ == "__main__":
    main()
