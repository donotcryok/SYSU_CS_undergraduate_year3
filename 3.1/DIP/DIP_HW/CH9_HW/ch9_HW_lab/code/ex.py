import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

# 设置matplotlib中文字体，避免中文乱码和警告
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False    # 正确显示负号

class MorphologicalOperations:
    def __init__(self, structure_element=None):
        """
        初始化结构元素
        默认使用3x3全1结构元素
        """
        if structure_element is None:
            self.SE = np.ones((3, 3), dtype=np.uint8)
        else:
            self.SE = np.array(structure_element, dtype=np.uint8)
        
        if self.SE.shape != (3, 3):
            raise ValueError("结构元素必须是3x3矩阵")
        
        # 结构元素原点（中心点）
        self.origin = (1, 1)
    
    def _pad_image(self, image, padding_value=0):
        """为图像添加边界填充"""
        h, w = image.shape
        padded = np.full((h+2, w+2), padding_value, dtype=image.dtype)
        padded[1:h+1, 1:w+1] = image
        return padded
    
    def erosion(self, binary_image):
        """
        二值腐蚀运算
        """
        h, w = binary_image.shape
        padded = self._pad_image(binary_image, 0)
        output = np.zeros_like(binary_image)
        
        for i in range(h):
            for j in range(w):
                # 提取当前窗口
                window = padded[i:i+3, j:j+3]
                # 腐蚀条件：结构元素为1的位置，图像对应位置必须全为1
                if np.all(window[self.SE == 1] == 1):
                    output[i, j] = 1
        
        return output
    
    def dilation(self, binary_image):
        """
        二值膨胀运算
        """
        h, w = binary_image.shape
        padded = self._pad_image(binary_image, 0)
        output = np.zeros_like(binary_image)
        
        for i in range(h):
            for j in range(w):
                # 提取当前窗口
                window = padded[i:i+3, j:j+3]
                # 膨胀条件：结构元素为1的位置与图像对应位置有交集
                if np.any((window == 1) & (self.SE == 1)):
                    output[i, j] = 1
        
        return output
    
    def boundary_extraction(self, binary_image):
        """
        形态学边界提取
        使用公式: β(A) = A - (A⊖B)
        """
        # 步骤1: 对图像进行腐蚀
        eroded = self.erosion(binary_image)
        
        # 步骤2: 计算A - (A⊖B)
        boundary = binary_image.astype(int) - eroded.astype(int)
        boundary = np.clip(boundary, 0, 1)  # 确保结果为0或1
        
        return boundary.astype(np.uint8)
    
    def visualize_results(self, original, eroded, boundary, title="边界提取结果"):
        """可视化结果"""
        fig, axes = plt.subplots(1, 3, figsize=(12, 4))
        
        images = [original, eroded, boundary]
        titles = ['原图', '腐蚀结果 (A⊖B)', '边界提取 β(A)']
        
        for ax, img, title_text in zip(axes, images, titles):
            ax.imshow(img, cmap='gray', vmin=0, vmax=1)
            ax.set_title(title_text)
            ax.axis('off')
        
        plt.suptitle(title)
        plt.tight_layout()
        plt.show()
    
    def save_image(self, img, path):
        """保存二值图像到文件（0/1转255/0）"""
        Image.fromarray((img * 255).astype(np.uint8)).save(path)


def process_utk_image(image_path, structure_element, prefix):
    """
    处理UTK字符图片，进行形态学边界提取
    """
    # 加载并预处理图片
    img = Image.open(image_path).convert('L')  # 转为灰度图
    binary_img = np.array(img)
    
    # 二值化（假设白色字符，黑色背景）
    threshold = 128
    binary_img = (binary_img > threshold).astype(np.uint8)
    
    # 创建形态学操作对象
    morph = MorphologicalOperations(structure_element=structure_element)
    
    # 应用边界提取
    eroded = morph.erosion(binary_img)
    boundary = morph.boundary_extraction(binary_img)
    
    # 应用膨胀
    dilated = morph.dilation(binary_img)
    
    # 可视化结果
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    images = [binary_img, eroded, dilated, boundary]
    titles = ['原图', '腐蚀结果', '膨胀结果', '边界提取']
    for ax, img, title_text in zip(axes, images, titles):
        ax.imshow(img, cmap='gray', vmin=0, vmax=1)
        ax.set_title(title_text)
        ax.axis('off')
    plt.suptitle(f"UTK字符形态学运算 ({prefix})")
    plt.tight_layout()
    plt.show()
    
    # 保存结果
    morph.save_image(boundary, f"{prefix}_boundary.png")
    morph.save_image(dilated, f"{prefix}_dilated.png")
    morph.save_image(eroded, f"{prefix}_eroded.png")
    
    return boundary


# ====================== 主程序 ======================
if __name__ == "__main__":
    print("形态学边界提取演示")
    print("=" * 50)
    print("\n处理UTK图片（1.png）:")

    # 第一种结构元素：3x3全1
    se_full = np.ones((3, 3), dtype=np.uint8)
    print("结构元素1：3x3全1")
    process_utk_image("e:/3.1/DIP/DIP_HW/CH9_HW/ch9_HW_lab/code/1.png", se_full, "utk_full")

    # 第二种结构元素：3x3十字形
    se_cross = np.array([[0,1,0],[1,1,1],[0,1,0]], dtype=np.uint8)
    print("结构元素2：3x3十字形")
    process_utk_image("e:/3.1/DIP/DIP_HW/CH9_HW/ch9_HW_lab/code/1.png", se_cross, "utk_cross")

    print("\n程序结束。")