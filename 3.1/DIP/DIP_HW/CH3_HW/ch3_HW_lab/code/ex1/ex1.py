import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

# 设置matplotlib中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def calculate_histogram(image):
    """
    手工计算图像的直方图
    """
    hist = np.zeros(256, dtype=np.int32)
    # 遍历图像每个像素，统计各灰度级出现次数
    for i in range(image.shape[0]):
        for j in range(image.shape[1]):
            hist[image[i, j]] += 1
    return hist

def histogram_equalization(image):
    """
    直方图均衡化算法实现
    基于公式: s = T(r) = (L-1) * CDF(r) / (M*N)
    """
    height, width = image.shape
    total_pixels = height * width
    
    # 步骤1: 计算原始图像直方图
    hist = calculate_histogram(image)
    
    # 步骤2: 计算累积分布函数(CDF)
    cdf = np.zeros(256)
    cdf[0] = hist[0]
    for i in range(1, 256):
        cdf[i] = cdf[i-1] + hist[i]  # 累积求和
    
    # 步骤3: 计算变换函数
    # T(r) = (L-1) * CDF(r) / (M*N)，其中L=256
    mapping_function = np.round((255 * cdf) / total_pixels).astype(np.uint8)
    
    # 步骤4: 应用变换函数到原图像
    equalized_image = np.zeros_like(image)
    for i in range(height):
        for j in range(width):
            # 使用映射函数变换每个像素的灰度值
            equalized_image[i, j] = mapping_function[image[i, j]]
    
    return equalized_image, mapping_function, hist, cdf

def plot_results(original_img, equalized_img, original_hist, equalized_hist, mapping_func, save_path=None):
    """
    绘制直方图均衡化的所有结果
    包括原图、均衡化图、直方图对比、变换函数等
    """
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # 子图1: 原始图像
    axes[0, 0].imshow(original_img, cmap='gray')
    axes[0, 0].set_title('原始图像')
    axes[0, 0].axis('off')
    
    # 子图2: 原始图像直方图
    axes[0, 1].bar(range(256), original_hist, color='blue', alpha=0.7)
    axes[0, 1].set_title('原始图像直方图')
    axes[0, 1].set_xlabel('灰度值')
    axes[0, 1].set_ylabel('像素数量')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 子图3: 变换函数T(r)
    axes[0, 2].plot(range(256), mapping_func, 'r-', linewidth=2)
    axes[0, 2].set_title('直方图均衡化变换函数 T(r)')
    axes[0, 2].set_xlabel('输入灰度值 r')
    axes[0, 2].set_ylabel('输出灰度值 s')
    axes[0, 2].grid(True, alpha=0.3)
    axes[0, 2].set_xlim([0, 255])
    axes[0, 2].set_ylim([0, 255])
    
    # 子图4: 均衡化后图像
    axes[1, 0].imshow(equalized_img, cmap='gray')
    axes[1, 0].set_title('直方图均衡化后图像')
    axes[1, 0].axis('off')
    
    # 子图5: 均衡化后直方图
    axes[1, 1].bar(range(256), equalized_hist, color='green', alpha=0.7)
    axes[1, 1].set_title('均衡化后图像直方图')
    axes[1, 1].set_xlabel('灰度值')
    axes[1, 1].set_ylabel('像素数量')
    axes[1, 1].grid(True, alpha=0.3)
    
    # 子图6: 归一化直方图对比
    axes[1, 2].plot(range(256), original_hist / np.sum(original_hist), 'b-', 
                    label='原始图像', alpha=0.7, linewidth=2)
    axes[1, 2].plot(range(256), equalized_hist / np.sum(equalized_hist), 'g-', 
                    label='均衡化后', alpha=0.7, linewidth=2)
    axes[1, 2].set_title('归一化直方图对比')
    axes[1, 2].set_xlabel('灰度值')
    axes[1, 2].set_ylabel('概率密度')
    axes[1, 2].legend()
    axes[1, 2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存综合结果图
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {save_path}")
    
    plt.show()

def save_individual_plots(original_img, equalized_img, original_hist, equalized_hist, mapping_func):
    """保存单独的图表文件"""
    # 保存原始图像直方图
    plt.figure(figsize=(8, 6))
    plt.bar(range(256), original_hist, color='blue', alpha=0.7)
    plt.title('原始图像直方图')
    plt.xlabel('灰度值')
    plt.ylabel('像素数量')
    plt.grid(True, alpha=0.3)
    plt.savefig('result/original_histogram.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 保存变换函数图
    plt.figure(figsize=(8, 6))
    plt.plot(range(256), mapping_func, 'r-', linewidth=2)
    plt.title('直方图均衡化变换函数 T(r)')
    plt.xlabel('输入灰度值 r')
    plt.ylabel('输出灰度值 s')
    plt.grid(True, alpha=0.3)
    plt.xlim([0, 255])
    plt.ylim([0, 255])
    plt.savefig('result/transformation_function.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 保存均衡化后图像直方图
    plt.figure(figsize=(8, 6))
    plt.bar(range(256), equalized_hist, color='green', alpha=0.7)
    plt.title('均衡化后图像直方图')
    plt.xlabel('灰度值')
    plt.ylabel('像素数量')
    plt.grid(True, alpha=0.3)
    plt.savefig('result/equalized_histogram.png', dpi=300, bbox_inches='tight')
    plt.close()

def show_individual_plots(original_img, equalized_img, original_hist, equalized_hist, mapping_func):
    """单独显示各个图表，便于观察细节"""
    # 显示原始图像
    plt.figure(figsize=(8, 6))
    plt.imshow(original_img, cmap='gray')
    plt.title('原始图像')
    plt.axis('off')
    plt.show()
    
    # 显示原始图像直方图
    plt.figure(figsize=(8, 6))
    plt.bar(range(256), original_hist, color='blue', alpha=0.7)
    plt.title('原始图像直方图')
    plt.xlabel('灰度值')
    plt.ylabel('像素数量')
    plt.grid(True, alpha=0.3)
    plt.show()
    
    # 显示变换函数图
    plt.figure(figsize=(8, 6))
    plt.plot(range(256), mapping_func, 'r-', linewidth=2)
    plt.title('直方图均衡化变换函数 T(r)')
    plt.xlabel('输入灰度值 r')
    plt.ylabel('输出灰度值 s')
    plt.grid(True, alpha=0.3)
    plt.xlim([0, 255])
    plt.ylim([0, 255])
    plt.show()
    
    # 显示均衡化后图像
    plt.figure(figsize=(8, 6))
    plt.imshow(equalized_img, cmap='gray')
    plt.title('直方图均衡化后图像')
    plt.axis('off')
    plt.show()
    
    # 显示均衡化后图像直方图
    plt.figure(figsize=(8, 6))
    plt.bar(range(256), equalized_hist, color='green', alpha=0.7)
    plt.title('均衡化后图像直方图')
    plt.xlabel('灰度值')
    plt.ylabel('像素数量')
    plt.grid(True, alpha=0.3)
    plt.show()

def main():
    """主函数：执行直方图均衡化的完整流程"""
    # 读取图像
    try:
        image_path = '../img/a.jpg'
        original_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        
        if original_image is None:
            print(f"无法读取图像: {image_path}")
            print("请确保图像文件存在于指定路径")
            return
        
        print(f"成功读取图像，尺寸: {original_image.shape}")
        
        # 执行直方图均衡化算法
        equalized_image, mapping_function, original_hist, cdf = histogram_equalization(original_image)
        
        # 计算均衡化后的直方图用于对比
        equalized_hist = calculate_histogram(equalized_image)
        
        # 单独显示各个图表
        show_individual_plots(original_image, equalized_image, original_hist, 
                            equalized_hist, mapping_function)
        
        # 显示综合结果并保存
        plot_results(original_image, equalized_image, original_hist, 
                    equalized_hist, mapping_function, 'result/histogram_equalization_results.png')
        
        # 保存处理后的图像文件
        cv2.imwrite('result/original_image.jpg', original_image)
        cv2.imwrite('result/equalized_image.jpg', equalized_image)
        
        # 保存单独的图表文件
        save_individual_plots(original_image, equalized_image, original_hist, 
                            equalized_hist, mapping_function)
        
        # 输出统计信息
        print("\n=== 直方图均衡化结果统计 ===")
        print(f"原始图像灰度范围: [{np.min(original_image)}, {np.max(original_image)}]")
        print(f"均衡化后灰度范围: [{np.min(equalized_image)}, {np.max(equalized_image)}]")
        print(f"原始图像平均灰度: {np.mean(original_image):.2f}")
        print(f"均衡化后平均灰度: {np.mean(equalized_image):.2f}")
        print(f"原始图像标准差: {np.std(original_image):.2f}")
        print(f"均衡化后标准差: {np.std(equalized_image):.2f}")
        
        print("\n=== 保存的文件 ===")
        print("图像文件:")
        print("- result/original_image.jpg (原始图像)")
        print("- result/equalized_image.jpg (均衡化后图像)")
        print("图表文件:")
        print("- result/histogram_equalization_results.png (综合结果图)")
        print("- result/original_histogram.png (原始图像直方图)")
        print("- result/transformation_function.png (变换函数图)")
        print("- result/equalized_histogram.png (均衡化后直方图)")
        
    except Exception as e:
        print(f"处理过程中发生错误: {e}")

if __name__ == "__main__":
    # 创建结果目录
    import os
    os.makedirs('result', exist_ok=True)
    
    main()
