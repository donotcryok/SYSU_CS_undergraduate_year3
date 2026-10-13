# -*- coding: utf-8 -*-
"""
图像拼接模块
使用 RANSAC 求解仿射变换矩阵，实现两图拼接

拼接流程:
1. 读取两张图像
2. 使用 Harris 检测器提取关键点
3. 计算 SIFT/HOG 特征描述子
4. 进行特征匹配
5. 使用 RANSAC 估计仿射变换矩阵
6. 对图像进行变换
7. 图像融合和拼接
"""

import numpy as np
import cv2
import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from harris import HarrisCornerDetector
from feature_match import SIFTDescriptor, HOGDescriptor, FeatureMatcher
from ransac import RANSAC, apply_affine_transform, get_transform_bounds
from utils import (
    read_image, save_image, convert_to_grayscale, print_info
)


class ImageStitcher:
    """
    图像拼接器:使用特征匹配和 RANSAC 实现图像拼接
    param:
        feature_type: 特征类型，'sift' 或 'hog'
        ransac_iterations: RANSAC 迭代次数
        ransac_threshold: RANSAC 内点阈值
    """
    
    def __init__(self, feature_type='sift', ransac_iterations=2000, ransac_threshold=8.0):
        self.feature_type = feature_type
        self.ransac_iterations = ransac_iterations
        self.ransac_threshold = ransac_threshold
        
        # 初始化组件
        # HOG需要更多关键点来提高匹配成功率
        max_corners = 1500 if feature_type == 'hog' else 1000
        min_distance = 8 if feature_type == 'hog' else 10
        
        self.harris_detector = HarrisCornerDetector(
            k=0.04,
            threshold=0.008,  # 降低阈值，检测更多角点
            window_size=5,
            sigma=1.0,
            nms_size=7,
            max_corners=max_corners,
            min_distance=min_distance
        )
        
        if feature_type == 'sift':
            self.descriptor = SIFTDescriptor()
        elif feature_type == 'hog':
            # HOG使用更大的窗口和更精细的参数
            self.descriptor = HOGDescriptor(
                cell_size=8,
                block_size=2,
                orientations=9
            )
        else:
            raise ValueError(f"不支持的特征类型: {feature_type}")
        
        # HOG使用更宽松的匹配阈值
        ratio_threshold = 0.85 if feature_type == 'hog' else 0.75
        self.matcher = FeatureMatcher(ratio_threshold=ratio_threshold)
        self.ransac = RANSAC(
            n_iterations=ransac_iterations,
            threshold=ransac_threshold
        )
    
    def stitch(self, img1, img2):
        """
        拼接两张图像
        
        param:
            img1: 第一张图像（参考图像）
            img2: 第二张图像（待变换图像）
        
        return:
            result: 拼接后的图像
            transform_matrix: 仿射变换矩阵
            inliers: 内点掩码
        """
        print_info(f"使用 {self.feature_type.upper()} 特征进行拼接...")
        
        # 1. 转换为灰度图
        gray1 = convert_to_grayscale(img1)
        gray2 = convert_to_grayscale(img2)
        
        # 2. 提取关键点
        print_info("提取关键点...")
        kp1, _ = self.harris_detector.get_keypoints(gray1)
        kp2, _ = self.harris_detector.get_keypoints(gray2)
        
        print_info(f"图像1关键点数量: {len(kp1)}")
        print_info(f"图像2关键点数量: {len(kp2)}")
        
        if len(kp1) < 3 or len(kp2) < 3:
            print_info("错误: 关键点数量不足")
            return None, None, None
        
        # 3. 计算描述子
        print_info("计算特征描述子...")
        desc1 = self.descriptor.compute(gray1, kp1)
        desc2 = self.descriptor.compute(gray2, kp2)
        
        print_info(f"图像1描述子形状: {desc1.shape}")
        print_info(f"图像2描述子形状: {desc2.shape}")
        
        if len(desc1) == 0 or len(desc2) == 0:
            print_info("错误: 描述子计算失败")
            return None, None, None
        
        # 4. 特征匹配
        print_info("进行特征匹配...")
        matches = self.matcher.match(desc1, desc2)
        
        print_info(f"匹配点数量: {len(matches)}")
        
        if len(matches) < 3:
            print_info("错误: 匹配点数量不足")
            return None, None, None
        
        # 5. 提取匹配点坐标
        src_points = []  # 图像2的点（待变换）
        dst_points = []  # 图像1的点（参考）
        
        for idx1, idx2, dist in matches:
            x1, y1 = kp1[idx1].pt
            x2, y2 = kp2[idx2].pt
            dst_points.append([x1, y1])  # 目标点（图像1）
            src_points.append([x2, y2])  # 源点（图像2）
        
        src_points = np.array(src_points, dtype=np.float32)
        dst_points = np.array(dst_points, dtype=np.float32)
        
        # 6. RANSAC 估计变换矩阵
        print_info("使用 RANSAC 估计变换矩阵...")
        transform_matrix, inliers = self.ransac.fit(src_points, dst_points)
        
        if transform_matrix is None:
            print_info("错误: RANSAC 估计失败")
            return None, None, None
        
        print_info(f"变换矩阵:\n{transform_matrix}")
        print_info(f"内点数量: {np.sum(inliers)}")
        
        # 7. 计算拼接后的画布大小
        result = self._blend_images(img1, img2, transform_matrix)
        
        return result, transform_matrix, inliers
    
    def _blend_images(self, img1, img2, transform_matrix):
        """
        图像融合
        
        将 img2 变换后与 img1 进行融合
        
        param:
            img1: 参考图像
            img2: 待变换图像
            transform_matrix: 仿射变换矩阵
        
        return:
            result: 融合后的图像
        """
        h1, w1 = img1.shape[:2]
        h2, w2 = img2.shape[:2]
        
        # 计算 img2 变换后的边界
        corners, min_x, min_y, max_x, max_y = get_transform_bounds(img2, transform_matrix)
        
        # 计算拼接后的画布大小
        canvas_min_x = min(0, min_x)
        canvas_min_y = min(0, min_y)
        canvas_max_x = max(w1, max_x)
        canvas_max_y = max(h1, max_y)
        
        canvas_width = int(canvas_max_x - canvas_min_x)
        canvas_height = int(canvas_max_y - canvas_min_y)
        
        print_info(f"画布大小: {canvas_width} x {canvas_height}")
        
        # 创建画布
        if len(img1.shape) == 3:
            canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
        else:
            canvas = np.zeros((canvas_height, canvas_width), dtype=np.uint8)
        
        # 计算偏移量
        offset_x = -canvas_min_x
        offset_y = -canvas_min_y
        
        # 将 img1 放到画布上
        canvas[offset_y:offset_y+h1, offset_x:offset_x+w1] = img1
        
        # 变换 img2
        # 需要调整变换矩阵以考虑偏移
        adjusted_transform = transform_matrix.copy()
        adjusted_transform[0, 2] += offset_x
        adjusted_transform[1, 2] += offset_y
        
        # 创建 img2 的变换版本
        img2_transformed = cv2.warpAffine(
            img2, adjusted_transform,
            (canvas_width, canvas_height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=0
        )
        
        # 融合图像
        # 创建掩码
        if len(img1.shape) == 3:
            mask1 = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY) > 0
            mask2 = cv2.cvtColor(img2_transformed, cv2.COLOR_BGR2GRAY) > 0
        else:
            mask1 = canvas > 0
            mask2 = img2_transformed > 0
        
        # 重叠区域
        overlap = mask1 & mask2
        
        # 在重叠区域进行平均融合
        result = canvas.copy()
        
        if len(img1.shape) == 3:
            for c in range(3):
                result[:, :, c][overlap] = (
                    canvas[:, :, c][overlap].astype(np.float32) / 2 +
                    img2_transformed[:, :, c][overlap].astype(np.float32) / 2
                ).astype(np.uint8)
        else:
            result[overlap] = (
                canvas[overlap].astype(np.float32) / 2 +
                img2_transformed[overlap].astype(np.float32) / 2
            ).astype(np.uint8)
        
        # 非重叠区域直接使用变换后的图像
        non_overlap = mask2 & ~mask1
        result[non_overlap] = img2_transformed[non_overlap]
        
        return result


def stitch_two_images(img1_path, img2_path, feature_type='sift', save_path=None):
    """
    拼接两张图像的便捷函数
    
    param:
        img1_path: 第一张图像路径（参考图像）
        img2_path: 第二张图像路径（待变换图像）
        feature_type: 特征类型，'sift' 或 'hog'
        save_path: 保存路径
    
    return:
        result: 拼接后的图像
        transform_matrix: 变换矩阵
    """
    # 读取图像
    print_info(f"读取图像: {img1_path}")
    img1 = read_image(img1_path)
    print_info(f"读取图像: {img2_path}")
    img2 = read_image(img2_path)
    
    # 创建拼接器
    stitcher = ImageStitcher(feature_type=feature_type)
    
    # 拼接
    result, transform_matrix, inliers = stitcher.stitch(img1, img2)
    
    if result is not None and save_path is not None:
        save_image(result, save_path)
    
    return result, transform_matrix


def main():
    """
    主函数：对 uttower1.jpg 和 uttower2.jpg 进行拼接
    分别使用 SIFT 和 HOG 特征
    """
    # 图像路径
    img1_path = "../images/1/uttower1.jpg"
    img2_path = "../images/1/uttower2.jpg"
    
    # ========== SIFT 特征拼接 ==========
    print_info("\n========== SIFT 特征拼接 ==========")
    
    result_sift, transform_sift = stitch_two_images(
        img1_path, img2_path,
        feature_type='sift',
        save_path="../results/1/uttower_stitching_sift.png"
    )
    
    print_info(f"SIFT 拼接完成，结果保存至: ../results/1/uttower_stitching_sift.png")
    
    # ========== HOG 特征拼接 ==========
    print_info("\n========== HOG 特征拼接 ==========")
    
    result_hog, transform_hog = stitch_two_images(
        img1_path, img2_path,
        feature_type='hog',
        save_path="../results/1/uttower_stitching_hog.png"
    )
    
    print_info(f"HOG 拼接完成，结果保存至: ../results/1/uttower_stitching_hog.png")
    
    print_info("\n图像拼接完成！")
    
    return result_sift, result_hog


if __name__ == "__main__":
    main()