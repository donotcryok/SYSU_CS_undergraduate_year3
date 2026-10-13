# -*- coding: utf-8 -*-
"""
特征提取与匹配模块
使用 SIFT 和 HOG 特征描述子进行关键点匹配
SIFT (Scale-Invariant Feature Transform):
- 尺度不变特征变换
- 对图像旋转、尺度缩放、亮度变化具有不变性
- 描述子维度：128维
HOG (Histogram of Oriented Gradients):
- 方向梯度直方图
- 统计局部区域的梯度方向分布
- 描述子维度：可配置（通常为 3780 维）
"""

import numpy as np
import cv2
from skimage.feature import hog
from skimage import exposure
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from harris import HarrisCornerDetector
from utils import (
    read_image, save_image, draw_keypoints, 
    convert_to_grayscale, print_info
)


class SIFTDescriptor:
    """
    SIFT 特征描述子提取器
    """
    
    def __init__(self):
        # 创建 SIFT 检测器
        # 注意：OpenCV 4.4.0+ 中 SIFT 已移出专利保护，可以直接使用
        self.sift = cv2.SIFT_create()
    
    def compute(self, image, keypoints):
        """
        计算关键点的 SIFT 描述子
        param:
            image: 输入图像（灰度图）
            keypoints: 关键点列表（OpenCV KeyPoint 格式）
        return:
            descriptors: 描述子矩阵，形状为 (N, 128)，N 为关键点数量
        """
        if len(keypoints) == 0:
            return np.array([])
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = convert_to_grayscale(image)
        else:
            gray = image
        
        # 计算 SIFT 描述子
        keypoints, descriptors = self.sift.compute(gray, keypoints)
        
        return descriptors


class HOGDescriptor:
    """
    HOG 特征描述子提取器
    """
    
    def __init__(self, cell_size=16, block_size=2, orientations=9, window_size=64):
        """
        初始化 HOG 描述子
        
        改进参数设置以提高匹配质量：
        - 增大窗口大小以捕获更多上下文信息
        - 增大cell_size以提高对局部变形的鲁棒性
        
        param:
            cell_size: cell 的大小（像素），默认16
            block_size: block 包含的 cell 数量，默认2
            orientations: 梯度方向直方图的 bin 数量，默认9
            window_size: 描述子窗口大小，默认64像素
        """
        self.cell_size = cell_size
        self.block_size = block_size
        self.orientations = orientations
        # 描述子窗口大小（以像素为单位）
        self.window_size = window_size  # 64x64 像素窗口，捕获更多上下文
    
    def compute(self, image, keypoints):
        """
        计算关键点的 HOG 描述子
        param:
            image: 输入图像
            keypoints: 关键点列表（OpenCV KeyPoint 格式）
        return:
            descriptors: 描述子矩阵，形状为 (N, D)，D 为描述子维度
        """
        if len(keypoints) == 0:
            return np.array([])
        
        # 转换为灰度图
        if len(image.shape) == 3:
            gray = convert_to_grayscale(image)
        else:
            gray = image.copy()
        
        # 归一化到 0-255
        gray = gray.astype(np.float64)
        gray = ((gray - gray.min()) / (gray.max() - gray.min()) * 255).astype(np.uint8)
        
        descriptors = []
        half_size = self.window_size // 2
        
        for kp in keypoints:
            x, y = int(kp.pt[0]), int(kp.pt[1])
            
            # 提取关键点周围的局部区域
            y_start = max(0, y - half_size)
            y_end = min(gray.shape[0], y + half_size)
            x_start = max(0, x - half_size)
            x_end = min(gray.shape[1], x + half_size)
            
            # 如果区域太小，跳过该关键点
            min_required_size = self.cell_size * 2  # 至少需要2个cell
            if y_end - y_start < min_required_size or x_end - x_start < min_required_size:
                continue
            
            patch = gray[y_start:y_end, x_start:x_end]
            
            # 调整patch大小为window_size，确保是cell_size的整数倍
            patch = cv2.resize(patch, (self.window_size, self.window_size))
            
            try:
                # 计算 HOG 特征
                # 使用调整后的参数确保特征计算正确
                actual_pixels_per_cell = (self.cell_size, self.cell_size)
                actual_cells_per_block = (self.block_size, self.block_size)
                
                hog_feature = hog(
                    patch,
                    orientations=self.orientations,
                    pixels_per_cell=actual_pixels_per_cell,
                    cells_per_block=actual_cells_per_block,
                    block_norm='L2-Hys',
                    transform_sqrt=True,  # 使用平方根变换提高对光照变化的鲁棒性
                    feature_vector=True
                )
                descriptors.append(hog_feature)
            except Exception as e:
                # 如果计算失败，跳过该关键点
                continue
        
        if len(descriptors) == 0:
            return np.array([])
        
        return np.array(descriptors)


class FeatureMatcher:
    """
    特征匹配器
    使用欧氏距离进行特征匹配
    采用最近邻距离比（Lowe's ratio test）进行匹配筛选
    """
    
    def __init__(self, ratio_threshold=0.75):
        """
        初始化匹配器
        para:
            ratio_threshold: 最近邻距离比阈值，默认 0.75
        """
        self.ratio_threshold = ratio_threshold
    
    def compute_euclidean_distance(self, desc1, desc2):
        """
        计算两个描述子之间的欧氏距离        
        para:
            desc1: 第一个描述子
            desc2: 第二个描述子
        return:
            欧氏距离
        """
        return np.sqrt(np.sum((desc1 - desc2) ** 2))
    
    def match(self, descriptors1, descriptors2):
        """
        使用欧氏距离进行特征匹配
        匹配策略:
        1. 对每个描述子，计算与所有目标描述子的欧氏距离
        2. 找到最近邻和次近邻
        3. 应用 Lowe's ratio test: 如果 d1/d2 < threshold，则接受该匹配
        para:
            descriptors1: 第一张图像的描述子
            descriptors2: 第二张图像的描述子
        return:
            matches: 匹配对列表，格式为 [(idx1, idx2, distance), ...]
        """
        if len(descriptors1) == 0 or len(descriptors2) == 0:
            return []
        
        matches = []
        
        # 对每个描述子进行匹配
        for i, desc1 in enumerate(descriptors1):
            # 计算与所有目标描述子的距离
            distances = []
            for j, desc2 in enumerate(descriptors2):
                dist = self.compute_euclidean_distance(desc1, desc2)
                distances.append((j, dist))
            
            # 按距离排序
            distances.sort(key=lambda x: x[1])
            
            # 获取最近邻和次近邻
            if len(distances) >= 2:
                nearest_idx, nearest_dist = distances[0]
                second_nearest_idx, second_nearest_dist = distances[1]
                
                # Lowe's ratio test
                # 只有当最近邻距离明显小于次近邻距离时才接受匹配
                if nearest_dist < self.ratio_threshold * second_nearest_dist:
                    matches.append((i, nearest_idx, nearest_dist))
            elif len(distances) == 1:
                # 只有一个候选匹配
                nearest_idx, nearest_dist = distances[0]
                matches.append((i, nearest_idx, nearest_dist))
        
        return matches
    
    def match_with_bfmatcher(self, descriptors1, descriptors2):
        """
        使用 OpenCV 的 BFMatcher 进行匹配（备用方法）
        para:
            descriptors1: 第一张图像的描述子
            descriptors2: 第二张图像的描述子
        
        return:
            matches: OpenCV DMatch 对象列表
        """
        if len(descriptors1) == 0 or len(descriptors2) == 0:
            return []
        
        # 确保描述子是正确的数据类型
        desc1 = np.array(descriptors1, dtype=np.float32)
        desc2 = np.array(descriptors2, dtype=np.float32)
        
        # 创建 BFMatcher
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=False)
        
        # KNN 匹配
        knn_matches = bf.knnMatch(desc1, desc2, k=2)
        
        # 应用 ratio test
        good_matches = []
        for m, n in knn_matches:
            if m.distance < self.ratio_threshold * n.distance:
                good_matches.append(m)
        
        return good_matches


def draw_matches_custom(img1, kp1, img2, kp2, matches, save_path=None):
    """
    绘制特征匹配结果
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
    np.random.seed(42)  # 固定随机种子，使颜色可重复
    for i, (idx1, idx2, dist) in enumerate(matches):
        pt1 = kp1[idx1]
        pt2 = kp2[idx2]
        
        if isinstance(pt1, cv2.KeyPoint):
            x1, y1 = int(pt1.pt[0]), int(pt1.pt[1])
        else:
            x1, y1 = int(pt1[0]), int(pt1[1])
        
        if isinstance(pt2, cv2.KeyPoint):
            x2, y2 = int(pt2.pt[0]), int(pt2.pt[1])
        else:
            x2, y2 = int(pt2[0]), int(pt2[1])
        
        # 随机颜色
        color = tuple(np.random.randint(0, 255, 3).tolist())
        
        # 绘制关键点
        cv2.circle(result, (x1, y1), 4, color, -1)
        cv2.circle(result, (x2 + w1, y2), 4, color, -1)
        
        # 绘制连接线
        cv2.line(result, (x1, y1), (x2 + w1, y2), color, 1)
    
    if save_path:
        save_image(result, save_path)
    
    return result


def main():
    """
    主函数：对 uttower1.jpg 和 uttower2.jpg 进行特征提取与匹配
    """
    # 图像路径
    image1_path = "../images/1/uttower1.jpg"
    image2_path = "../images/1/uttower2.jpg"
    save_path = "../results/1/uttower_match.png"
    
    # 读取图像
    print_info(f"读取图像: {image1_path}")
    img1 = read_image(image1_path)
    print_info(f"读取图像: {image2_path}")
    img2 = read_image(image2_path)
    
    # 转换为灰度图
    gray1 = convert_to_grayscale(img1)
    gray2 = convert_to_grayscale(img2)
    
    # 使用 Harris 检测器提取关键点
    print_info("使用 Harris 检测器提取关键点...")
    detector = HarrisCornerDetector(
        k=0.04,
        threshold=0.01,
        window_size=5,
        sigma=1.0,
        nms_size=7,
        max_corners=1000,
        min_distance=10
    )
    
    kp1, response1 = detector.get_keypoints(gray1)
    kp2, response2 = detector.get_keypoints(gray2)
    
    print_info(f"图像1检测到 {len(kp1)} 个关键点")
    print_info(f"图像2检测到 {len(kp2)} 个关键点")
    
    # ========== SIFT 特征匹配 ==========
    print_info("\n========== SIFT 特征匹配 ==========")
    
    # 创建 SIFT 描述子提取器
    sift_descriptor = SIFTDescriptor()
    
    # 计算 SIFT 描述子
    print_info("计算 SIFT 描述子...")
    desc1_sift = sift_descriptor.compute(gray1, kp1)
    desc2_sift = sift_descriptor.compute(gray2, kp2)
    
    print_info(f"图像1 SIFT 描述子形状: {desc1_sift.shape}")
    print_info(f"图像2 SIFT 描述子形状: {desc2_sift.shape}")
    
    # 特征匹配
    print_info("进行 SIFT 特征匹配...")
    matcher = FeatureMatcher(ratio_threshold=0.75)
    matches_sift = matcher.match(desc1_sift, desc2_sift)
    
    print_info(f"SIFT 匹配点数量: {len(matches_sift)}")
    
    # 绘制 SIFT 匹配结果
    result_sift = draw_matches_custom(img1, kp1, img2, kp2, matches_sift, 
                                       "../results/1/uttower_match_sift.png")
    
    # ========== HOG 特征匹配 ==========
    print_info("\n========== HOG 特征匹配 ==========")
    
    # 创建 HOG 描述子提取器
    hog_descriptor = HOGDescriptor(cell_size=8, block_size=2, orientations=9)
    
    # 计算 HOG 描述子
    print_info("计算 HOG 描述子...")
    desc1_hog = hog_descriptor.compute(gray1, kp1)
    desc2_hog = hog_descriptor.compute(gray2, kp2)
    
    print_info(f"图像1 HOG 描述子形状: {desc1_hog.shape}")
    print_info(f"图像2 HOG 描述子形状: {desc2_hog.shape}")
    
    # 特征匹配
    print_info("进行 HOG 特征匹配...")
    matches_hog = matcher.match(desc1_hog, desc2_hog)
    
    print_info(f"HOG 匹配点数量: {len(matches_hog)}")
    
    # 绘制 HOG 匹配结果
    result_hog = draw_matches_custom(img1, kp1, img2, kp2, matches_hog,
                                      "../results/1/uttower_match_hog.png")
    
    # ========== 综合匹配结果 ==========
    # 将 SIFT 和 HOG 匹配结果并排显示
    h1, w1 = result_sift.shape[:2]
    h2, w2 = result_hog.shape[:2]
    
    # 创建综合结果图
    combined = np.zeros((max(h1, h2), w1 + w2 + 50, 3), dtype=np.uint8)
    combined[:h1, :w1] = result_sift
    combined[:h2, w1+50:] = result_hog
    
    # 添加标签
    cv2.putText(combined, "SIFT Matching", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(combined, "HOG Matching", (w1+60, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # 保存综合结果
    save_image(combined, save_path)
    
    print_info(f"\n特征匹配完成！")
    print_info(f"SIFT 匹配结果: ../results/1/uttower_match_sift.png")
    print_info(f"HOG 匹配结果: ../results/1/uttower_match_hog.png")
    print_info(f"综合匹配结果: {save_path}")
    
    return matches_sift, matches_hog, kp1, kp2


if __name__ == "__main__":
    main()