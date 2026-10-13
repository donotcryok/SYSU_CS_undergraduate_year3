import cv2
import os

def sobel_edge_detection_and_segmentation():
    #读取照片
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    img_path = os.path.join(base_dir, 'img', 'origin.png')
    
    #保存路径
    save_edge_path = os.path.join(base_dir, 'img', 'sobel_edges.png')
    save_seg_path = os.path.join(base_dir, 'img', 'segmented_result.png')

    #读取图像
    gray_img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

    #计算 Sobel 梯度
    sobel_x = cv2.Sobel(gray_img, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gray_img, cv2.CV_64F, 0, 1, ksize=3)

    #绝对值化并转回uint8(0-255标准图像格式)
    abs_sobel_x = cv2.convertScaleAbs(sobel_x)
    abs_sobel_y = cv2.convertScaleAbs(sobel_y)

    # 边缘检测图
    sobel_combined = cv2.addWeighted(abs_sobel_x, 0.5, abs_sobel_y, 0.5, 0)

    # 分割结果图
    _, segmented_img = cv2.threshold(sobel_combined, 100, 255, cv2.THRESH_BINARY)

    cv2.imwrite(save_edge_path, sobel_combined)
    cv2.imwrite(save_seg_path, segmented_img)
    
    cv2.imshow('1 - Original Grayscale', gray_img)
    cv2.imshow('2 - Sobel Edges', sobel_combined)
    cv2.imshow('3 - Segmented Image', segmented_img)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    sobel_edge_detection_and_segmentation()