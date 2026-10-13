# -*- coding: utf-8 -*-
"""
多图拼接模块
对四张 Yosemite 图像进行多图拼接

多图拼接策略:
1. 计算所有图像之间的匹配关系
2. 构建图像匹配图，找到最佳拼接顺序
3. 选择参考图像（通常是匹配最多的图像）
4. 依次将其他图像变换到参考图像坐标系
5. 进行图像融合
"""

import numpy as np
import cv2
import sys
import os
from collections import defaultdict

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from harris import HarrisCornerDetector
from feature_match import SIFTDescriptor, FeatureMatcher
from ransac import RANSAC, get_transform_bounds
from utils import (
    read_image, save_image, convert_to_grayscale, print_info
)


class MultiImageStitcher:
    """
    多图拼接器:   
    使用 SIFT + RANSAC 方法对多张图像进行拼接
    
   param:
        ransac_iterations: RANSAC 迭代次数
        ransac_threshold: RANSAC 内点阈值
    """
    
    def __init__(self, ransac_iterations=1000, ransac_threshold=5.0):
        self.ransac_iterations = ransac_iterations
        self.ransac_threshold = ransac_threshold
        
        # 初始化组件
        self.harris_detector = HarrisCornerDetector(
            k=0.04,
            threshold=0.01,
            window_size=5,
            sigma=1.0,
            nms_size=7,
            max_corners=1500,
            min_distance=8
        )
        
        self.sift_descriptor = SIFTDescriptor()
        self.matcher = FeatureMatcher(ratio_threshold=0.75)
        self.ransac = RANSAC(
            n_iterations=ransac_iterations,
            threshold=ransac_threshold
        )
    
    def compute_pairwise_matches(self, images):
        """
        计算所有图像对之间的匹配关系
        param:
            images: 图像列表
        
        return:
            match_matrix: 匹配矩阵，match_matrix[i][j] 包含 (matches, transform, inliers)
        """
        n = len(images)
        print_info(f"计算 {n} 张图像之间的匹配关系...")
        
        # 存储匹配结果
        match_matrix = [[None for _ in range(n)] for _ in range(n)]
        
        # 计算每对图像的匹配
        for i in range(n):
            for j in range(i + 1, n):
                print_info(f"计算图像 {i} 和 {j} 的匹配...")
                
                result = self._compute_match(images[i], images[j])
                
                if result is not None:
                    matches, transform, inliers, kp1, kp2 = result
                    match_matrix[i][j] = {
                        'matches': matches,
                        'transform': transform,  # 从 j 到 i 的变换
                        'inliers': inliers,
                        'n_inliers': np.sum(inliers) if inliers is not None else 0,
                        'kp1': kp1,
                        'kp2': kp2
                    }
                    # 反向变换
                    if transform is not None:
                        # 计算逆变换
                        # 对于仿射变换，逆变换可以通过求解得到
                        try:
                            # 扩展为 3x3 矩阵
                            T = np.vstack([transform, [0, 0, 1]])
                            T_inv = np.linalg.inv(T)
                            transform_inv = T_inv[:2, :]
                            match_matrix[j][i] = {
                                'matches': [(m[1], m[0], m[2]) for m in matches],
                                'transform': transform_inv,  # 从 i 到 j 的变换
                                'inliers': inliers,
                                'n_inliers': np.sum(inliers) if inliers is not None else 0,
                                'kp1': kp2,
                                'kp2': kp1
                            }
                        except np.linalg.LinAlgError:
                            match_matrix[j][i] = None
        
        return match_matrix
    
    def _compute_match(self, img1, img2):
        """
        计算两张图像之间的匹配
        
        param:
            img1: 第一张图像
            img2: 第二张图像
        
        return:
            matches: 匹配列表
            transform: 变换矩阵（从 img2 到 img1）
            inliers: 内点掩码
            kp1, kp2: 关键点
        """
        # 转换为灰度图
        gray1 = convert_to_grayscale(img1)
        gray2 = convert_to_grayscale(img2)
        
        # 提取关键点
        kp1, _ = self.harris_detector.get_keypoints(gray1)
        kp2, _ = self.harris_detector.get_keypoints(gray2)
        
        if len(kp1) < 3 or len(kp2) < 3:
            return None
        
        # 计算描述子
        desc1 = self.sift_descriptor.compute(gray1, kp1)
        desc2 = self.sift_descriptor.compute(gray2, kp2)
        
        if len(desc1) == 0 or len(desc2) == 0:
            return None
        
        # 匹配
        matches = self.matcher.match(desc1, desc2)
        
        if len(matches) < 3:
            return None
        
        # 提取匹配点坐标
        src_points = []  # img2 的点
        dst_points = []  # img1 的点
        
        for idx1, idx2, dist in matches:
            x1, y1 = kp1[idx1].pt
            x2, y2 = kp2[idx2].pt
            dst_points.append([x1, y1])
            src_points.append([x2, y2])
        
        src_points = np.array(src_points, dtype=np.float32)
        dst_points = np.array(dst_points, dtype=np.float32)
        
        # RANSAC
        transform, inliers = self.ransac.fit(src_points, dst_points)
        
        return matches, transform, inliers, kp1, kp2
    
    def find_stitch_order(self, match_matrix):
        """
        确定拼接顺序,使用贪心策略：
        1. 找到匹配点最多的图像作为参考图像
        2. 按匹配点数量排序其他图像
        3. 依次将相邻图像拼接到参考图像
        
        param:
            match_matrix: 匹配矩阵
        
        return:
            reference_idx: 参考图像索引
            stitch_order: 拼接顺序列表
        """
        n = len(match_matrix)
        
        # 计算每张图像的总匹配点数量
        total_matches = [0] * n
        for i in range(n):
            for j in range(n):
                if match_matrix[i][j] is not None:
                    total_matches[i] += match_matrix[i][j]['n_inliers']
        
        print_info(f"各图像匹配点数量: {total_matches}")
        
        # 选择匹配最多的图像作为参考
        reference_idx = np.argmax(total_matches)
        print_info(f"选择图像 {reference_idx} 作为参考图像")
        
        # 构建拼接顺序
        # 使用 BFS 从参考图像开始，按匹配强度扩展
        visited = [False] * n
        visited[reference_idx] = True
        stitch_order = [reference_idx]
        
        # 构建邻接表
        adjacency = defaultdict(list)
        for i in range(n):
            for j in range(n):
                if match_matrix[i][j] is not None and match_matrix[i][j]['n_inliers'] > 10:
                    adjacency[i].append((j, match_matrix[i][j]['n_inliers']))
        
        # 按匹配强度排序邻居
        for i in range(n):
            adjacency[i].sort(key=lambda x: -x[1])
        
        # BFS 扩展
        queue = [reference_idx]
        while queue:
            current = queue.pop(0)
            for neighbor, n_matches in adjacency[current]:
                if not visited[neighbor]:
                    visited[neighbor] = True
                    stitch_order.append(neighbor)
                    queue.append(neighbor)
        
        # 添加未访问的图像（如果有）
        for i in range(n):
            if not visited[i]:
                stitch_order.append(i)
        
        print_info(f"拼接顺序: {stitch_order}")
        
        return reference_idx, stitch_order
    
    def compute_cumulative_transform(self, match_matrix, stitch_order, reference_idx):
        """
        计算每张图像到参考图像的累积变换
        
        param:
            match_matrix: 匹配矩阵
            stitch_order: 拼接顺序
            reference_idx: 参考图像索引
        
        return:
            transforms: 变换字典，transforms[i] 是图像 i 到参考图像的变换
        """
        n = len(stitch_order)
        transforms = {}
        
        # 参考图像的变换是单位变换
        transforms[reference_idx] = np.array([[1, 0, 0], [0, 1, 0]], dtype=np.float32)
        
        # 计算其他图像的变换
        # 通过拼接路径累积变换
        for i in range(1, n):
            current_idx = stitch_order[i]
            
            # 找到已拼接的图像中与当前图像匹配最好的
            best_prev_idx = None
            best_n_matches = 0
            
            for j in range(i):
                prev_idx = stitch_order[j]
                if match_matrix[current_idx][prev_idx] is not None:
                    n_matches = match_matrix[current_idx][prev_idx]['n_inliers']
                    if n_matches > best_n_matches:
                        best_n_matches = n_matches
                        best_prev_idx = prev_idx
            
            if best_prev_idx is None:
                # 没有找到匹配，尝试反向
                for j in range(i):
                    prev_idx = stitch_order[j]
                    if match_matrix[prev_idx][current_idx] is not None:
                        best_prev_idx = prev_idx
                        break
            
            if best_prev_idx is not None:
                # 获取直接变换
                if match_matrix[current_idx][best_prev_idx] is not None:
                    direct_transform = match_matrix[current_idx][best_prev_idx]['transform']
                else:
                    # 使用反向变换的逆
                    T = np.vstack([match_matrix[best_prev_idx][current_idx]['transform'], [0, 0, 1]])
                    direct_transform = np.linalg.inv(T)[:2, :]
                
                # 累积变换：先变换到 best_prev_idx，再变换到参考图像
                prev_transform = transforms[best_prev_idx]
                
                # 矩阵乘法
                T_direct = np.vstack([direct_transform, [0, 0, 1]])
                T_prev = np.vstack([prev_transform, [0, 0, 1]])
                T_cumulative = T_prev @ T_direct
                
                transforms[current_idx] = T_cumulative[:2, :]
            else:
                # 无法计算变换，使用单位变换
                print_info(f"警告: 图像 {current_idx} 无法找到匹配")
                transforms[current_idx] = np.array([[1, 0, 0], [0, 1, 0]], dtype=np.float32)
        
        return transforms
    
    def stitch_multiple(self, images):
        """
        拼接多张图像
        """
        n = len(images)
        print_info(f"开始拼接 {n} 张图像...")
        
        if n < 2:
            print_info("图像数量不足")
            return images[0] if n == 1 else None
        
        # 1. 计算所有图像对之间的匹配
        match_matrix = self.compute_pairwise_matches(images)
        
        # 2. 确定拼接顺序
        reference_idx, stitch_order = self.find_stitch_order(match_matrix)
        
        # 3. 计算累积变换
        transforms = self.compute_cumulative_transform(match_matrix, stitch_order, reference_idx)
        
        # 4. 计算画布大小
        canvas_bounds = self._compute_canvas_bounds(images, transforms)
        
        # 5. 创建画布并拼接
        result = self._blend_all_images(images, transforms, canvas_bounds, reference_idx)
        
        return result
    
    def _compute_canvas_bounds(self, images, transforms):
        """
        计算画布边界
        """
        all_min_x, all_min_y = float('inf'), float('inf')
        all_max_x, all_max_y = float('-inf'), float('-inf')
        
        for idx, img in enumerate(images):
            if idx in transforms:
                corners, min_x, min_y, max_x, max_y = get_transform_bounds(img, transforms[idx])
                all_min_x = min(all_min_x, min_x)
                all_min_y = min(all_min_y, min_y)
                all_max_x = max(all_max_x, max_x)
                all_max_y = max(all_max_y, max_y)
        
        return int(all_min_x), int(all_min_y), int(all_max_x), int(all_max_y)
    
    def _blend_all_images(self, images, transforms, canvas_bounds, reference_idx):
        """
        融合所有图像
        
        param:
            images: 图像列表
            transforms: 变换字典
            canvas_bounds: 画布边界
            reference_idx: 参考图像索引
        return:
            result: 融合后的图像
        """
        min_x, min_y, max_x, max_y = canvas_bounds
        
        canvas_width = max_x - min_x
        canvas_height = max_y - min_y
        
        print_info(f"画布大小: {canvas_width} x {canvas_height}")
        
        # 创建画布
        # 使用参考图像的颜色通道数
        ref_img = images[reference_idx]
        if len(ref_img.shape) == 3:
            canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.float32)
            weight = np.zeros((canvas_height, canvas_width), dtype=np.float32)
        else:
            canvas = np.zeros((canvas_height, canvas_width), dtype=np.float32)
            weight = np.zeros((canvas_height, canvas_width), dtype=np.float32)
        
        # 偏移量
        offset_x = -min_x
        offset_y = -min_y
        
        # 依次添加每张图像
        for idx, img in enumerate(images):
            if idx not in transforms:
                continue
            
            transform = transforms[idx]
            
            # 调整变换矩阵
            adjusted_transform = transform.copy()
            adjusted_transform[0, 2] += offset_x
            adjusted_transform[1, 2] += offset_y
            
            # 变换图像
            img_transformed = cv2.warpAffine(
                img, adjusted_transform,
                (canvas_width, canvas_height),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0
            )
            
            # 创建权重掩码（中心权重高，边缘权重低）
            h, w = img.shape[:2]
            
            # 使用距离变换创建权重
            if len(img.shape) == 3:
                gray = convert_to_grayscale(img)
            else:
                gray = img
            
            # 创建边缘掩码
            edge_mask = np.ones((h, w), dtype=np.float32)
            edge_margin = 20
            edge_mask[:edge_margin, :] = 0
            edge_mask[-edge_margin:, :] = 0
            edge_mask[:, :edge_margin] = 0
            edge_mask[:, -edge_margin:] = 0
            
            # 变换权重掩码
            weight_mask = cv2.warpAffine(
                edge_mask, adjusted_transform,
                (canvas_width, canvas_height),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=0
            )
            
            # 加权融合
            if len(img.shape) == 3:
                for c in range(3):
                    canvas[:, :, c] += img_transformed[:, :, c] * weight_mask
            else:
                canvas += img_transformed * weight_mask
            
            weight += weight_mask
        
        # 归一化
        weight[weight == 0] = 1  # 避免除零
        if len(ref_img.shape) == 3:
            for c in range(3):
                canvas[:, :, c] = canvas[:, :, c] / weight
        else:
            canvas = canvas / weight
        
        result = canvas.astype(np.uint8)
        
        return result


def main():
    """
    主函数：对四张 Yosemite 图像进行多图拼接
    """
    # 图像路径
    image_paths = [
        "../images/1/yosemite1.jpg",
        "../images/1/yosemite2.jpg",
        "../images/1/yosemite3.jpg",
        "../images/1/yosemite4.jpg"
    ]
    
    save_path = "../results/1/yosemite_stitching.png"
    
    # 读取图像
    print_info("读取 Yosemite 图像...")
    images = []
    for path in image_paths:
        img = read_image(path)
        images.append(img)
        print_info(f"读取: {path}, 大小: {img.shape}")
    
    # 创建多图拼接器
    stitcher = MultiImageStitcher(
        ransac_iterations=1000,
        ransac_threshold=5.0
    )
    
    # 拼接
    print_info("\n开始多图拼接...")
    result = stitcher.stitch_multiple(images)
    
    if result is not None:
        # 保存结果
        save_image(result, save_path)
        print_info(f"多图拼接完成，结果保存至: {save_path}")
    else:
        print_info("多图拼接失败")
    
    return result


if __name__ == "__main__":
    main()