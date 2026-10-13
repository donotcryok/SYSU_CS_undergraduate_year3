# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import os


def read_image(image_path, grayscale=False):
    """
    读取图像文件
    param:
        image_path: 图像文件路径
        grayscale: 是否转换为灰度图，默认为False
    return:
        图像数组
    """
    if grayscale:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    else:
        img = cv2.imread(image_path)
    
    if img is None:
        raise FileNotFoundError(f"无法读取图像: {image_path}")
    
    return img


def save_image(image, save_path):
    """
    保存图像到文件
    param:
        image: 图像数组
        save_path: 保存路径
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    cv2.imwrite(save_path, image)
    print(f"图像已保存至: {save_path}")


def draw_keypoints(image, keypoints, color=(0, 255, 0), radius=3):
    """
    在图像上绘制关键点
    
    param:
        image: 输入图像
        keypoints: 关键点列表，格式为 [(x, y), ...] 或 numpy 数组
        color: 绘制颜色，默认绿色
        radius: 绘制半径，默认3
    
    return:
        绘制了关键点的图像
    """
    result = image.copy()
    if len(image.shape) == 2:
        result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
    
    for kp in keypoints:
        if isinstance(kp, (tuple, list, np.ndarray)):
            x, y = int(kp[0]), int(kp[1])
        else:
            x, y = int(kp.pt[0]), int(kp.pt[1])
        cv2.circle(result, (x, y), radius, color, -1)
    
    return result


def draw_matches(img1, kp1, img2, kp2, matches, save_path=None):
    """
    绘制特征匹配结果
    
    param:
        img1: 第一张图像
        kp1: 第一张图像的关键点
        img2: 第二张图像
        kp2: 第二张图像的关键点
        matches: 匹配对列表，格式为 [(idx1, idx2), ...]
        save_path: 保存路径，如果为None则不保存
    
    return:
        匹配结果图像
    """
    # 创建输出图像
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]
    
    # 确保图像是彩色格式
    if len(img1.shape) == 2:
        img1_color = cv2.cvtColor(img1, cv2.COLOR_GRAY2BGR)
    else:
        img1_color = img1.copy()
    
    if len(img2.shape) == 2:
        img2_color = cv2.cvtColor(img2, cv2.COLOR_GRAY2BGR)
    else:
        img2_color = img2.copy()
    
    # 拼接图像
    result = np.zeros((max(h1, h2), w1 + w2, 3), dtype=np.uint8)
    result[:h1, :w1] = img1_color
    result[:h2, w1:w1+w2] = img2_color
    
    # 绘制匹配线
    for i, (idx1, idx2) in enumerate(matches):
        pt1 = kp1[idx1]
        pt2 = kp2[idx2]
        
        if isinstance(pt1, (tuple, list, np.ndarray)):
            x1, y1 = int(pt1[0]), int(pt1[1])
        else:
            x1, y1 = int(pt1.pt[0]), int(pt1.pt[1])
        
        if isinstance(pt2, (tuple, list, np.ndarray)):
            x2, y2 = int(pt2[0]), int(pt2[1])
        else:
            x2, y2 = int(pt2.pt[0]), int(pt2.pt[1])
        
        # 随机颜色
        color = tuple(np.random.randint(0, 255, 3).tolist())
        
        # 绘制关键点
        cv2.circle(result, (x1, y1), 3, color, -1)
        cv2.circle(result, (x2 + w1, y2), 3, color, -1)
        
        # 绘制连接线
        cv2.line(result, (x1, y1), (x2 + w1, y2), color, 1)
    
    if save_path:
        save_image(result, save_path)
    
    return result


def convert_to_grayscale(image):
    """
    将图像转换为灰度图
    """
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def normalize_image(image, target_range=(0, 255)):
    """
    将图像归一化到指定范围
    
    param:
        image: 输入图像
        target_range: 目标范围，默认(0, 255)
    
    return:
        归一化后的图像
    """
    min_val, max_val = target_range
    img_min, img_max = image.min(), image.max()
    
    if img_max - img_min == 0:
        return np.zeros_like(image, dtype=np.float32)
    
    normalized = (image - img_min) / (img_max - img_min) * (max_val - min_val) + min_val
    return normalized.astype(np.uint8)


def apply_gaussian_blur(image, kernel_size=5, sigma=1.0):
    """
    应用高斯模糊
    """
    return cv2.GaussianBlur(image, (kernel_size, kernel_size), sigma)


def compute_sobel_gradients(image):
    """
    使用Sobel算子计算图像梯度
    """
    # 计算x方向梯度
    Ix = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
    # 计算y方向梯度
    Iy = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
    
    return Ix, Iy


def show_image(image, title="Image", wait=True):
    """
    显示图像
    """
    cv2.imshow(title, image)
    if wait:
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def show_images(images, titles=None, figsize=(15, 5)):
    """
    使用matplotlib显示多张图像
    """
    n = len(images)
    plt.figure(figsize=figsize)
    
    for i, img in enumerate(images):
        plt.subplot(1, n, i + 1)
        if len(img.shape) == 2:
            plt.imshow(img, cmap='gray')
        else:
            plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if titles:
            plt.title(titles[i])
        plt.axis('off')
    
    plt.tight_layout()
    plt.show()


def ensure_dir(directory):
    """
    确保目录存在，如果不存在则创建
    """
    os.makedirs(directory, exist_ok=True)


def print_info(message):
    """
    打印信息
    """
    print(f"[INFO] {message}")


def print_error(message):
    """
    打印错误信息
    """
    print(f"[ERROR] {message}")