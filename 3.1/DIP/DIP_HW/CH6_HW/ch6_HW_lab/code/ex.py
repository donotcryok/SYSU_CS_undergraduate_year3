import cv2
import numpy as np
import os

def bgr_to_hsi(img):
    img_float = img.astype(np.float32) / 255.0
    b, g, r = cv2.split(img_float)

    # 计算分子和分母，得到theta
    num = 0.5 * ((r - g) + (r - b))
    den = np.sqrt((r - g)**2 + (r - b) * (g - b))
    theta = np.arccos(np.clip(num / (den + 1e-6), -1.0, 1.0))  # 防止除零

    # 计算H分量
    h = theta.copy()
    h[b > g] = 2 * np.pi - h[b > g]

    # 计算S分量
    sum_rgb = r + g + b
    min_rgb = np.minimum(np.minimum(r, g), b)
    s = 1 - 3 * min_rgb / (sum_rgb + 1e-6)
    s[sum_rgb == 0] = 0

    # 计算I分量
    i = sum_rgb / 3.0

    return cv2.merge((h, s, i))

def hsi_to_bgr(img_hsi):
    h, s, i = cv2.split(img_hsi)
    b, g, r = np.zeros_like(h), np.zeros_like(h), np.zeros_like(h)
    epsilon = 1e-6  # 防止除零

    #区间0: 0 <= H < 120度
    mask1 = (h < 2 * np.pi / 3)
    h1 = h[mask1]
    b[mask1] = i[mask1] * (1 - s[mask1])
    r[mask1] = i[mask1] * (1 + (s[mask1] * np.cos(h1)) / (np.cos(np.pi / 3 - h1) + epsilon))
    g[mask1] = 3 * i[mask1] - (r[mask1] + b[mask1])

    #区间1: 120 <= H < 240度
    mask2 = (h >= 2 * np.pi / 3) & (h < 4 * np.pi / 3)
    h2 = h[mask2] - 2 * np.pi / 3
    r[mask2] = i[mask2] * (1 - s[mask2])
    g[mask2] = i[mask2] * (1 + (s[mask2] * np.cos(h2)) / (np.cos(np.pi / 3 - h2) + epsilon))
    b[mask2] = 3 * i[mask2] - (r[mask2] + g[mask2])

    #区间2: 240 <= H < 360度
    mask3 = (h >= 4 * np.pi / 3)
    h3 = h[mask3] - 4 * np.pi / 3
    g[mask3] = i[mask3] * (1 - s[mask3])
    b[mask3] = i[mask3] * (1 + (s[mask3] * np.cos(h3)) / (np.cos(np.pi / 3 - h3) + epsilon))
    r[mask3] = 3 * i[mask3] - (g[mask3] + b[mask3])

    img_bgr = cv2.merge((b, g, r))
    img_bgr = np.clip(img_bgr, 0, 1)
    return np.clip(img_bgr * 255, 0, 255).astype(np.uint8)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(script_dir, 'origin.png')

    img = cv2.imread(img_path)
    if img is None:
        print(f"Error: 无法读取图像，请确保 {img_path} 存在。")
        return

    print(f"正在处理图像: {img_path}")

    hsi_temp = bgr_to_hsi(img)
    img_reconstructed = hsi_to_bgr(hsi_temp)
    mse = np.mean((img.astype(float) - img_reconstructed.astype(float)) ** 2)
    print(f"RGB->HSI->RGB 转换的均方误差 (MSE): {mse:.2f}")
    if mse > 10: # 阈值
        print("警告：HSI色彩空间转换可能存在较大误差。")

    #方法1：采用HSI空间，仅在I分量上作直方图均衡
    # 1.BGR转HSI
    hsi_img = bgr_to_hsi(img)
    h, s, i = cv2.split(hsi_img)
    
    # 2.对强度I进行直方图均衡化
    # 将I [0, 1] 映射到 [0, 255] uint8
    i_uint8 = (i * 255).astype(np.uint8)
    i_eq_uint8 = cv2.equalizeHist(i_uint8)
    
    # 归一化回[0, 1]
    i_eq = i_eq_uint8.astype(np.float32) / 255.0
    
    # 3.合并通道
    hsi_eq = cv2.merge((h, s, i_eq))
    
    # 4.HSI转回BGR
    img_hsi_eq = hsi_to_bgr(hsi_eq)
    
    res1_path = os.path.join(script_dir, 'result_method1_hsi.png')
    cv2.imwrite(res1_path, img_hsi_eq)
    print(f"方法 #1 (HSI) 结果已保存: {res1_path}")

    # 方法 #2: 采用RGB空间，分别在RGB三个空间上作直方图均衡化
    b_raw, g_raw, r_raw = cv2.split(img)
    
    b_eq2 = cv2.equalizeHist(b_raw)
    g_eq2 = cv2.equalizeHist(g_raw)
    r_eq2 = cv2.equalizeHist(r_raw)
    
    img_rgb_eq = cv2.merge((b_eq2, g_eq2, r_eq2))
    
    res2_path = os.path.join(script_dir, 'result_method2_rgb.png')
    cv2.imwrite(res2_path, img_rgb_eq)
    print(f"方法 #2 (RGB) 结果已保存: {res2_path}")

if __name__ == "__main__":
    main()
