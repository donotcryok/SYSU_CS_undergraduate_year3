# -*- coding: utf-8 -*-
"""
RANSAC 算法模块
用于求解仿射变换矩阵

RANSAC (RANdom SAmple Consensus) 算法原理:
1. 随机选择最小样本集（仿射变换需要3对点）
2. 根据样本集计算变换模型
3. 计算所有数据点与模型的误差，统计内点数量
4. 重复迭代，选择内点最多的模型
5. 使用所有内点重新估计最终模型

仿射变换矩阵:
[x']   [a  b  tx] [x]   [a*x + b*y + tx]
[y'] = [c  d  ty] [y] = [c*x + d*y + ty]
[1 ]   [0  0  1 ] [1]   [      1       ]

需要估计6个参数: a, b, c, d, tx, ty
至少需要3对不共线的匹配点
"""

import numpy as np
import cv2
import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import print_info


class RANSAC:
    """
    RANSAC 算法实现:用于从带噪声的匹配点中估计仿射变换矩阵
    param:
        n_iterations: RANSAC 迭代次数
        threshold: 内点判定阈值（像素）
        min_samples: 最小样本数量（仿射变换需要3对点）
    """
    
    def __init__(self, n_iterations=1000, threshold=5.0, min_samples=3):
        self.n_iterations = n_iterations
        self.threshold = threshold
        self.min_samples = min_samples
    
    def compute_affine_transform(self, src_points, dst_points):
        """
        计算仿射变换矩阵
        param:
            src_points: 源点，形状为 (N, 2)
            dst_points: 目标点，形状为 (N, 2)
        
        return:
            transform_matrix: 2x3 仿射变换矩阵
        """
        if len(src_points) < 3 or len(dst_points) < 3:
            raise ValueError("至少需要3对点来计算仿射变换")
        
        # 使用最小二乘法求解
        # 构建方程组 Ax = b
        # 其中 x = [a, b, tx, c, d, ty]^T
        
        n = len(src_points)
        A = np.zeros((2 * n, 6))
        b = np.zeros(2 * n)
        
        for i in range(n):
            x, y = src_points[i]
            x_prime, y_prime = dst_points[i]
            
            # 第一行: a*x + b*y + tx = x'
            A[2*i, 0] = x
            A[2*i, 1] = y
            A[2*i, 2] = 1
            A[2*i, 3] = 0
            A[2*i, 4] = 0
            A[2*i, 5] = 0
            b[2*i] = x_prime
            
            # 第二行: c*x + d*y + ty = y'
            A[2*i+1, 0] = 0
            A[2*i+1, 1] = 0
            A[2*i+1, 2] = 0
            A[2*i+1, 3] = x
            A[2*i+1, 4] = y
            A[2*i+1, 5] = 1
            b[2*i+1] = y_prime
        
        # 使用最小二乘法求解
        # x = (A^T A)^{-1} A^T b
        try:
            params, residuals, rank, s = np.linalg.lstsq(A, b, rcond=None)
        except np.linalg.LinAlgError:
            return None
        
        # 构建 2x3 变换矩阵
        transform_matrix = np.array([
            [params[0], params[1], params[2]],
            [params[3], params[4], params[5]]
        ])
        
        return transform_matrix
    
    def compute_transform_error(self, src_points, dst_points, transform_matrix):
        """
        计算变换误差:对于每对点，计算变换后的源点与目标点之间的欧氏距离
        param:
            src_points: 源点，形状为 (N, 2)
            dst_points: 目标点，形状为 (N, 2)
            transform_matrix: 2x3 仿射变换矩阵
        
        return:
            errors: 每对点的误差，形状为 (N,)
        """
        n = len(src_points)
        errors = np.zeros(n)
        
        for i in range(n):
            x, y = src_points[i]
            x_prime, y_prime = dst_points[i]
            
            # 应用变换
            x_transformed = transform_matrix[0, 0] * x + transform_matrix[0, 1] * y + transform_matrix[0, 2]
            y_transformed = transform_matrix[1, 0] * x + transform_matrix[1, 1] * y + transform_matrix[1, 2]
            
            # 计算欧氏距离
            errors[i] = np.sqrt((x_transformed - x_prime) ** 2 + (y_transformed - y_prime) ** 2)
        
        return errors
    
    def fit(self, src_points, dst_points):
        """
        使用 RANSAC 算法拟合仿射变换矩阵:
        1. 随机选择 min_samples 个样本点
        2. 使用样本点计算变换矩阵
        3. 计算所有点的误差，统计内点数量
        4. 重复 n_iterations 次，选择内点最多的模型
        5. 使用所有内点重新估计最终变换矩阵
        
        param:
            src_points: 源点，形状为 (N, 2)
            dst_points: 目标点，形状为 (N, 2)
        
        return:
            best_transform: 最佳变换矩阵
            best_inliers: 内点掩码（布尔数组）
        """
        n_points = len(src_points)
        
        if n_points < self.min_samples:
            print_info(f"警告: 匹配点数量 {n_points} 小于最小样本数 {self.min_samples}")
            return None, None
        
        best_transform = None
        best_inliers = np.zeros(n_points, dtype=bool)
        best_n_inliers = 0
        
        print_info(f"开始 RANSAC 迭代，共 {self.n_iterations} 次迭代...")
        
        for iteration in range(self.n_iterations):
            # 1. 随机选择样本点
            sample_indices = np.random.choice(n_points, self.min_samples, replace=False)
            
            sample_src = src_points[sample_indices]
            sample_dst = dst_points[sample_indices]
            
            # 检查点是否共线（共线的点无法确定唯一的仿射变换）
            if self._are_collinear(sample_src) or self._are_collinear(sample_dst):
                continue
            
            # 2. 计算变换矩阵
            try:
                transform = self.compute_affine_transform(sample_src, sample_dst)
            except:
                continue
            
            if transform is None:
                continue
            
            # 3. 计算误差并统计内点
            errors = self.compute_transform_error(src_points, dst_points, transform)
            inliers = errors < self.threshold
            n_inliers = np.sum(inliers)
            
            # 4. 更新最佳模型
            if n_inliers > best_n_inliers:
                best_n_inliers = n_inliers
                best_inliers = inliers
                best_transform = transform
        
        # 5. 使用所有内点重新估计变换矩阵
        if best_n_inliers >= self.min_samples:
            inlier_src = src_points[best_inliers]
            inlier_dst = dst_points[best_inliers]
            
            try:
                best_transform = self.compute_affine_transform(inlier_src, inlier_dst)
            except:
                pass
        
        print_info(f"RANSAC 完成，找到 {best_n_inliers} 个内点")
        
        return best_transform, best_inliers
    
    def _are_collinear(self, points):
        """
        检查点是否共线:使用三角形面积法：如果三点共线，则三角形面积为0
        
        param:
            points: 点集，形状为 (3, 2)
        
        return:
            True 如果共线，False 否则
        """
        if len(points) < 3:
            return True
        
        # 计算三角形面积
        x1, y1 = points[0]
        x2, y2 = points[1]
        x3, y3 = points[2]
        
        # 使用叉积计算面积
        area = abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)) / 2
        
        # 如果面积接近0，则共线
        return area < 1.0  # 阈值设为1像素


def estimate_affine_transform_ransac(src_points, dst_points, n_iterations=1000, threshold=5.0):
    """
    使用 RANSAC 估计仿射变换矩阵的便捷函数
    param:
        src_points: 源点，形状为 (N, 2)
        dst_points: 目标点，形状为 (N, 2)
        n_iterations: RANSAC 迭代次数
        threshold: 内点判定阈值（像素）
    return:
        transform_matrix: 2x3 仿射变换矩阵
        inliers: 内点掩码
    """
    ransac = RANSAC(n_iterations=n_iterations, threshold=threshold)
    return ransac.fit(src_points, dst_points)


def apply_affine_transform(image, transform_matrix, output_shape=None):
    """
    对图像应用仿射变换
    param:
        image: 输入图像
        transform_matrix: 2x3 仿射变换矩阵
        output_shape: 输出图像形状 (height, width)，如果为 None 则与输入相同
    return:
        变换后的图像
    """
    if output_shape is None:
        output_shape = image.shape[:2]
    
    # 使用 OpenCV 的 warpAffine 函数
    transformed = cv2.warpAffine(image, transform_matrix, 
                                  (output_shape[1], output_shape[0]),
                                  flags=cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_CONSTANT,
                                  borderValue=0)
    
    return transformed


def get_transform_bounds(image, transform_matrix):
    """
    计算图像变换后的边界
    """
    h, w = image.shape[:2]
    
    # 原始图像的四个角点
    corners = np.array([
        [0, 0],
        [w, 0],
        [w, h],
        [0, h]
    ], dtype=np.float32)
    
    # 变换角点
    transformed_corners = cv2.transform(corners.reshape(1, -1, 2), transform_matrix).reshape(-1, 2)
    
    # 计算边界
    min_x = int(np.floor(transformed_corners[:, 0].min()))
    min_y = int(np.floor(transformed_corners[:, 1].min()))
    max_x = int(np.ceil(transformed_corners[:, 0].max()))
    max_y = int(np.ceil(transformed_corners[:, 1].max()))
    
    return transformed_corners, min_x, min_y, max_x, max_y


if __name__ == "__main__":
    # 测试 RANSAC
    print_info("测试 RANSAC 算法...")
    
    # 生成测试数据
    np.random.seed(42)
    
    # 源点
    src_points = np.array([
        [10, 20],
        [30, 40],
        [50, 60],
        [70, 80],
        [90, 100],
        [110, 120]
    ], dtype=np.float32)
    
    # 真实变换矩阵
    true_transform = np.array([
        [1.1, 0.2, 5],
        [0.3, 0.9, 10]
    ], dtype=np.float32)
    
    # 目标点（应用变换）
    dst_points = np.zeros_like(src_points)
    for i, (x, y) in enumerate(src_points):
        dst_points[i, 0] = true_transform[0, 0] * x + true_transform[0, 1] * y + true_transform[0, 2]
        dst_points[i, 1] = true_transform[1, 0] * x + true_transform[1, 1] * y + true_transform[1, 2]
    
    # 添加噪声
    dst_points += np.random.randn(*dst_points.shape) * 2
    
    # 添加一些外点
    dst_points[4] += [50, 50]  # 外点
    dst_points[5] += [-30, 30]  # 外点
    
    # 使用 RANSAC 估计变换
    ransac = RANSAC(n_iterations=1000, threshold=5.0)
    estimated_transform, inliers = ransac.fit(src_points, dst_points)
    
    print_info(f"真实变换矩阵:\n{true_transform}")
    print_info(f"估计变换矩阵:\n{estimated_transform}")
    print_info(f"内点掩码: {inliers}")
    print_info(f"内点数量: {np.sum(inliers)}")