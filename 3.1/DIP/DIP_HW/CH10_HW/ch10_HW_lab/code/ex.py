import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

# --- 1. 自动获取路径 ---
# 获取当前脚本所在的目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 拼接输入图片的完整路径
image_path = os.path.join(current_dir, 'origin.png')

print(f"正在读取图片: {image_path}")

# --- 2. 读取图像 ---
img = cv2.imread(image_path, 0)

if img is None:
    print("Error: 无法读取图像，请检查文件是否存在！")
else:
    print("图片读取成功，开始处理...")

    # --- 3. 图像处理 ---
    # 高斯模糊去噪
    blur = cv2.GaussianBlur(img, (5, 5), 0)

    # Otsu 阈值化
    # ret 是计算出的最佳阈值，th 是处理后的二值图像
    ret, th = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    print(f"Otsu 算法计算出的最佳阈值为: {ret}")

    # --- 4. 保存【结果图】 (二值化图像) ---
    # 使用 cv2.imwrite 保存，可以得到没有坐标轴和白边的纯净图片
    result_filename = 'otsu_result.png'
    save_result_path = os.path.join(current_dir, result_filename)
    cv2.imwrite(save_result_path, th)
    print(f"[保存成功] 分割结果图已保存至: {save_result_path}")

    # --- 5. 保存【直方图】 ---
    plt.figure()  # 创建一个新的绘图窗口，确保和之前的图分开
    plt.hist(blur.ravel(), 256, [0, 256], color='gray')
    # 画出红色阈值线
    plt.axvline(x=ret, color='r', linestyle='dashed', linewidth=2, label=f'Threshold: {ret}')
    plt.title('Histogram & Otsu Threshold')
    plt.xlabel('Pixel Value')
    plt.ylabel('Frequency')
    plt.legend()
    
    hist_filename = 'otsu_histogram.png'
    save_hist_path = os.path.join(current_dir, hist_filename)
    plt.savefig(save_hist_path)
    print(f"[保存成功] 直方图已保存至: {save_hist_path}")

    # --- 6. 显示结果 (可选) ---
    # 如果你想在屏幕上也看一眼，可以保留这行；如果只想后台保存，可以注释掉 plt.show()
    plt.show()