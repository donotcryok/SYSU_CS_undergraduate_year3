import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

# 设置matplotlib中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def manual_convolution(image, kernel):
    """
    手工实现二维卷积操作
    用于理解卷积滤波的原理和过程
    """
    height, width = image.shape
    k_height, k_width = kernel.shape
    
    # 计算边界填充的大小（保证输出图像与输入同尺寸）
    pad_h = k_height // 2
    pad_w = k_width // 2
    
    # 对图像进行零填充，处理边界问题
    padded_image = np.pad(image, ((pad_h, pad_h), (pad_w, pad_w)), 
                         mode='constant', constant_values=0)
    
    # 初始化输出结果
    result = np.zeros_like(image, dtype=np.float64)
    
    # 对每个像素位置执行卷积操作
    for i in range(height):
        for j in range(width):
            # 提取与卷积核大小相同的图像区域
            region = padded_image[i:i+k_height, j:j+k_width]
            # 计算卷积：对应元素相乘后求和
            result[i, j] = np.sum(region * kernel)
    
    return result

def laplacian_enhancement(image):
    """
    拉普拉斯算子图像锐化增强
    实现公式: g(x,y) = f(x,y) + c*∇²f(x,y)
    """
    # 定义拉普拉斯算子核（8邻域模板）
    # 中心权值为8，8个邻域权值为-1，总和为0
    laplacian_kernel = np.array([
        [-1, -1, -1],
        [-1,  8, -1],
        [-1, -1, -1]
    ], dtype=np.float64)
    
    print("使用的拉普拉斯核:")
    print(laplacian_kernel)
    
    # 手工卷积计算拉普拉斯响应（检测边缘和细节）
    laplacian_response = manual_convolution(image.astype(np.float64), laplacian_kernel)
    
    # 应用增强公式：原图 + 拉普拉斯响应
    # 根据式(3.54): g(x,y) = f(x,y) + c * ∇²f(x,y)，这里c=1
    enhanced_image = image.astype(np.float64) + laplacian_response
    
    # 确保像素值在有效范围[0,255]内
    enhanced_image = np.clip(enhanced_image, 0, 255)
    
    return enhanced_image.astype(np.uint8), laplacian_response

def show_individual_results(original_img, laplacian_response, enhanced_img):
    """单独显示各个处理结果，便于详细观察"""
    # 显示原始图像
    plt.figure(figsize=(8, 6))
    plt.imshow(original_img, cmap='gray')
    plt.title('原始图像')
    plt.axis('off')
    plt.show()
    
    # 显示拉普拉斯响应（需要归一化显示）
    plt.figure(figsize=(8, 6))
    # 将拉普拉斯响应归一化到0-255范围用于显示
    laplacian_display = cv2.convertScaleAbs(laplacian_response)
    plt.imshow(laplacian_display, cmap='gray')
    plt.title('拉普拉斯响应（边缘检测结果）')
    plt.axis('off')
    plt.show()
    
    # 显示增强后图像
    plt.figure(figsize=(8, 6))
    plt.imshow(enhanced_img, cmap='gray')
    plt.title('拉普拉斯锐化后图像')
    plt.axis('off')
    plt.show()

def plot_comprehensive_results(original_img, laplacian_response, enhanced_img, save_path=None):
    """绘制拉普拉斯增强的综合结果对比图"""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # 子图1: 原始图像
    axes[0].imshow(original_img, cmap='gray')
    axes[0].set_title('原始图像')
    axes[0].axis('off')
    
    # 子图2: 拉普拉斯响应
    laplacian_display = cv2.convertScaleAbs(laplacian_response)
    axes[1].imshow(laplacian_display, cmap='gray')
    axes[1].set_title('拉普拉斯响应')
    axes[1].axis('off')
    
    # 子图3: 增强后图像
    axes[2].imshow(enhanced_img, cmap='gray')
    axes[2].set_title('拉普拉斯锐化后图像')
    axes[2].axis('off')
    
    plt.tight_layout()
    
    # 保存综合结果图
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"综合结果图已保存到: {save_path}")
    
    plt.show()

def save_individual_plots(original_img, laplacian_response, enhanced_img):
    """保存单独的图表文件"""
    # 保存原始图像图表
    plt.figure(figsize=(8, 6))
    plt.imshow(original_img, cmap='gray')
    plt.title('原始图像')
    plt.axis('off')
    plt.savefig('result/original_image_plot.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 保存拉普拉斯响应图表
    plt.figure(figsize=(8, 6))
    laplacian_display = cv2.convertScaleAbs(laplacian_response)
    plt.imshow(laplacian_display, cmap='gray')
    plt.title('拉普拉斯响应')
    plt.axis('off')
    plt.savefig('result/laplacian_response_plot.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 保存增强后图像图表
    plt.figure(figsize=(8, 6))
    plt.imshow(enhanced_img, cmap='gray')
    plt.title('拉普拉斯锐化后图像')
    plt.axis('off')
    plt.savefig('result/enhanced_image_plot.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """主函数：执行拉普拉斯增强的完整流程"""
    # 尝试多个可能的图像路径
    possible_paths = [
        '../img/b.jpg',
        'img/b.jpg',
        '../b.jpg',
        'b.jpg'
    ]
    
    original_image = None
    used_path = None
    
    print("正在尝试读取图像...")
    for path in possible_paths:
        print(f"尝试路径: {path}")
        if os.path.exists(path):
            original_image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if original_image is not None:
                used_path = path
                print(f"成功从路径读取图像: {path}")
                break
            else:
                print(f"文件存在但无法读取: {path}")
        else:
            print(f"文件不存在: {path}")
    
    # 错误处理：无法读取图像
    if original_image is None:
        print("\n=== 错误：无法读取图像 ===")
        print("请检查以下事项：")
        print("1. 确保图像文件 'b.jpg' 存在")
        print("2. 将图像文件放在以下任一位置：")
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            print(f"   - {abs_path}")
        print("3. 确保图像文件格式正确且未损坏")
        print("\n当前工作目录:", os.getcwd())
        print("ex2.py 文件位置:", os.path.abspath(__file__))
        return
    
    print(f"成功读取图像，尺寸: {original_image.shape}")
    print(f"使用的路径: {used_path}")
    
    # 执行拉普拉斯增强算法
    enhanced_image, laplacian_response = laplacian_enhancement(original_image)
    
    # 单独显示各个结果
    show_individual_results(original_image, laplacian_response, enhanced_image)
    
    # 显示综合结果并保存
    plot_comprehensive_results(original_image, laplacian_response, enhanced_image, 
                             'result/laplacian_enhancement_results.png')
    
    # 保存图像文件
    cv2.imwrite('result/original_image.jpg', original_image)
    cv2.imwrite('result/enhanced_image.jpg', enhanced_image)
    
    # 保存拉普拉斯响应（归一化后保存）
    laplacian_save = cv2.convertScaleAbs(laplacian_response)
    cv2.imwrite('result/laplacian_response.jpg', laplacian_save)
    
    # 保存单独的图表
    save_individual_plots(original_image, laplacian_response, enhanced_image)
    
    # 输出统计信息
    print("\n=== 拉普拉斯增强结果统计 ===")
    print(f"原始图像灰度范围: [{np.min(original_image)}, {np.max(original_image)}]")
    print(f"增强后灰度范围: [{np.min(enhanced_image)}, {np.max(enhanced_image)}]")
    print(f"原始图像平均灰度: {np.mean(original_image):.2f}")
    print(f"增强后平均灰度: {np.mean(enhanced_image):.2f}")
    print(f"原始图像标准差: {np.std(original_image):.2f}")
    print(f"增强后标准差: {np.std(enhanced_image):.2f}")
    print(f"拉普拉斯响应范围: [{np.min(laplacian_response):.2f}, {np.max(laplacian_response):.2f}]")

if __name__ == "__main__":
    # 创建结果目录
    os.makedirs('result', exist_ok=True)
    
    main()
