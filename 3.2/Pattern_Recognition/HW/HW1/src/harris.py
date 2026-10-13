# -*- coding: utf-8 -*-
"""
Harris 角点检测模块
自己实现 Harris 角点检测算法，包含假阳性点过滤
Harris 角点检测算法原理:
1. 计算图像梯度 Ix, Iy
2. 构建自相关矩阵 M = [Ix²   Ix*Iy]
                    [Ix*Iy  Iy² ]
3. 对 M 进行高斯窗口加权求和
4. 计算角点响应函数 R = det(M) - k * trace(M)²
5. 非极大值抑制
6. 阈值过滤和假阳性去除
"""

import numpy as np
import cv2
from utils import (
    read_image, save_image, draw_keypoints, 
    convert_to_grayscale, apply_gaussian_blur,
    compute_sobel_gradients, normalize_image, print_info
)


class HarrisCornerDetector:
    """
    Harris 角点检测器类
    """
    
    def __init__(self, k=0.04, threshold=0.01, window_size=5, sigma=1.0,
                 nms_size=7, max_corners=500, min_distance=10):
        self.k = k
        self.threshold = threshold
        self.window_size = window_size
        self.sigma = sigma
        self.nms_size = nms_size
        self.max_corners = max_corners
        self.min_distance = min_distance
    
    def compute_gradients(self, image):
        """
        计算图像梯度
        para:
            image: 输入灰度图像
        return:
            Ix: x方向梯度
            Iy: y方向梯度
        """
        # 使用 Sobel 算子计算梯度
        Ix = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        Iy = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        return Ix, Iy
    
    def compute_harris_response(self, Ix, Iy):
        """
        计算 Harris 角点响应函数        
        param:
            Ix: x方向梯度
            Iy: y方向梯度
        return:
            R: Harris 角点响应图
        """
        # 计算梯度的乘积
        Ix2 = Ix ** 2
        Iy2 = Iy ** 2
        IxIy = Ix * Iy
        
        # 使用高斯窗口进行加权求和
        # 这相当于对每个像素周围的梯度乘积进行加权平均
        Ix2 = cv2.GaussianBlur(Ix2, (self.window_size, self.window_size), self.sigma)
        Iy2 = cv2.GaussianBlur(Iy2, (self.window_size, self.window_size), self.sigma)
        IxIy = cv2.GaussianBlur(IxIy, (self.window_size, self.window_size), self.sigma)
        
        # 计算 det(M) = Ix2 * Iy2 - IxIy²
        det_M = Ix2 * Iy2 - IxIy ** 2
        
        # 计算 trace(M) = Ix2 + Iy2
        trace_M = Ix2 + Iy2
        
        # 计算 Harris 角点响应函数
        # R = det(M) - k * trace(M)²
        R = det_M - self.k * (trace_M ** 2)
        
        return R
    
    def non_maximum_suppression(self, response):
        """
        非极大值抑制 (Non-Maximum Suppression, NMS)
        para:
            response: Harris 角点响应图
        return:
            局部极大值掩码
        """
        # 使用膨胀操作找到局部最大值
        kernel = np.ones((self.nms_size, self.nms_size), np.uint8)
        local_max = cv2.dilate(response, kernel)
        
        # 只有等于局部最大值的点才保留
        local_max_mask = (response == local_max)
        
        return local_max_mask
    
    def filter_false_positives(self, corners, response, image_shape):
        """
        去除假阳性角点,可能包括:
        1. 响应值低于阈值的点
        2. 图像边缘附近的点（边缘效应）
        3. 噪声引起的虚假角点
        
        para:
            corners: 初步检测到的角点列表 [(x, y, response), ...]
            response: Harris 角点响应图
            image_shape: 图像形状 (height, width)
        rerturn:
            过滤后的角点列表
        """
        height, width = image_shape
        
        # 设置边缘区域阈值（排除图像边缘的角点）
        edge_margin = 10
        
        filtered_corners = []
        
        for corner in corners:
            x, y, r = corner
            
            # 过滤条件1: 排除图像边缘的点
            if x < edge_margin or x >= width - edge_margin:
                continue
            if y < edge_margin or y >= height - edge_margin:
                continue
            
            # 过滤条件2: 响应值必须大于阈值
            # 阈值设为响应图最大值的某个比例
            threshold = self.threshold * response.max()
            if r < threshold:
                continue
            
            # 过滤条件3: 检查局部一致性
            # 在角点周围小区域内，响应值应该相对均匀
            local_region = response[max(0, y-2):min(height, y+3), 
                                    max(0, x-2):min(width, x+3)]
            if local_region.size > 0:
                local_std = np.std(local_region)
                # 如果局部区域标准差过大，可能是噪声点
                if local_std > 0.5 * r:
                    continue
            
            filtered_corners.append(corner)
        
        return filtered_corners
    
    def enforce_min_distance(self, corners):
        """
        强制执行角点之间的最小距离
        """
        if len(corners) == 0:
            return []
        
        # 按响应值降序排序
        sorted_corners = sorted(corners, key=lambda x: x[2], reverse=True)
        
        selected = []
        
        for corner in sorted_corners:
            x, y, r = corner
            
            # 检查与已选角点的距离
            is_valid = True
            for sx, sy, _ in selected:
                dist = np.sqrt((x - sx) ** 2 + (y - sy) ** 2)
                if dist < self.min_distance:
                    is_valid = False
                    break
            
            if is_valid:
                selected.append(corner)
            
            # 达到最大角点数量
            if len(selected) >= self.max_corners:
                break
        
        return selected
    
    def detect(self, image):
        """
        检测图像中的角点
        完整的 Harris 角点检测流程:
        1. 图像预处理（灰度化、高斯模糊）
        2. 计算梯度
        3. 计算 Harris 响应
        4. 非极大值抑制
        5. 阈值过滤
        6. 假阳性去除
        7. 最小距离约束
        para:
            image: 输入图像（可以是彩色或灰度）
        return:
            corners: 角点列表，格式为 [(x, y, response), ...]
            response: Harris 角点响应图
        """
        print_info("开始 Harris 角点检测...")
        
        # 1. 图像预处理
        if len(image.shape) == 3:
            gray = convert_to_grayscale(image)
        else:
            gray = image.copy()
        
        # 转换为浮点型
        gray = gray.astype(np.float64)
        
        # 高斯模糊去噪
        gray = apply_gaussian_blur(gray, kernel_size=5, sigma=1.0)
        
        # 2. 计算梯度
        Ix, Iy = self.compute_gradients(gray)
        
        # 3. 计算 Harris 响应
        response = self.compute_harris_response(Ix, Iy)
        
        # 4. 非极大值抑制
        local_max_mask = self.non_maximum_suppression(response)
        
        # 5. 获取候选角点
        # 找到所有局部极大值点
        candidate_mask = local_max_mask & (response > 0)
        candidate_points = np.where(candidate_mask)
        
        # 构建角点列表
        corners = []
        for y, x in zip(candidate_points[0], candidate_points[1]):
            r = response[y, x]
            corners.append((x, y, r))
        
        print_info(f"初步检测到 {len(corners)} 个候选角点")
        
        # 6. 假阳性去除
        corners = self.filter_false_positives(corners, response, gray.shape)
        print_info(f"假阳性过滤后剩余 {len(corners)} 个角点")
        
        # 7. 最小距离约束
        corners = self.enforce_min_distance(corners)
        print_info(f"最终保留 {len(corners)} 个角点")
        
        return corners, response
    
    def get_keypoints(self, image):
        """
        获取关键点（兼容 OpenCV KeyPoint 格式）
        para:
            image: 输入图像
        return:
            keypoints: OpenCV KeyPoint 对象列表
            response: Harris 角点响应图
        """
        corners, response = self.detect(image)
        
        # 转换为 KeyPoint 格式
        keypoints = []
        for x, y, r in corners:
            kp = cv2.KeyPoint(x=float(x), y=float(y), size=5, response=r)
            keypoints.append(kp)
        
        return keypoints, response


def main():
    """
    主函数：对 sudoku.png、uttower1.jpg 和 uttower2.jpg 进行 Harris 角点检测
    """
    # 创建 Harris 检测器
    # 参数调优：
    # - k: 0.04 是经典值
    # - threshold: 0.01 相对阈值，过滤弱角点
    # - window_size: 5 高斯窗口大小
    # - nms_size: 7 非极大值抑制窗口
    # - max_corners: 500 最大角点数
    # - min_distance: 10 角点最小间距
    detector = HarrisCornerDetector(
        k=0.04,
        threshold=0.01,
        window_size=5,
        sigma=1.0,
        nms_size=7,
        max_corners=500,
        min_distance=10
    )
    
    # ========== Task 1: sudoku.png Harris 角点检测 ==========
    print_info("\n========== Task 1: sudoku.png Harris 角点检测 ==========")
    image_path = "../images/1/sudoku.png"
    save_path = "../results/1/sudoku_keypoints.png"
    
    # 读取图像
    print_info(f"读取图像: {image_path}")
    image = read_image(image_path)
    
    # 检测角点
    corners, response = detector.detect(image)
    
    # 提取角点坐标
    keypoints = [(x, y) for x, y, r in corners]
    
    # 绘制角点
    result_image = draw_keypoints(image, keypoints, color=(0, 255, 0), radius=3)
    
    # 保存结果
    save_image(result_image, save_path)
    
    print_info(f"Harris 角点检测完成，共检测到 {len(corners)} 个角点")
    
    # ========== Task 2: uttower1.jpg Harris 角点检测 ==========
    print_info("\n========== Task 2: uttower1.jpg Harris 角点检测 ==========")
    image_path = "../images/1/uttower1.jpg"
    save_path = "../results/1/uttower1_keypoints.jpg"
    
    # 读取图像
    print_info(f"读取图像: {image_path}")
    image = read_image(image_path)
    
    # 检测角点
    corners, response = detector.detect(image)
    
    # 提取角点坐标
    keypoints = [(x, y) for x, y, r in corners]
    
    # 绘制角点
    result_image = draw_keypoints(image, keypoints, color=(0, 255, 0), radius=3)
    
    # 保存结果
    save_image(result_image, save_path)
    
    print_info(f"Harris 角点检测完成，共检测到 {len(corners)} 个角点")
    
    # ========== Task 3: uttower2.jpg Harris 角点检测 ==========
    print_info("\n========== Task 3: uttower2.jpg Harris 角点检测 ==========")
    image_path = "../images/1/uttower2.jpg"
    save_path = "../results/1/uttower2_keypoints.jpg"
    
    # 读取图像
    print_info(f"读取图像: {image_path}")
    image = read_image(image_path)
    
    # 检测角点
    corners, response = detector.detect(image)
    
    # 提取角点坐标
    keypoints = [(x, y) for x, y, r in corners]
    
    # 绘制角点
    result_image = draw_keypoints(image, keypoints, color=(0, 255, 0), radius=3)
    
    # 保存结果
    save_image(result_image, save_path)
    
    print_info(f"Harris 角点检测完成，共检测到 {len(corners)} 个角点")
    
    print_info("\n========== 所有 Harris 角点检测任务完成 ==========")
    print_info("生成的结果文件:")
    print_info("  - results/1/sudoku_keypoints.png")
    print_info("  - results/1/uttower1_keypoints.jpg")
    print_info("  - results/1/uttower2_keypoints.jpg")


if __name__ == "__main__":
    main()