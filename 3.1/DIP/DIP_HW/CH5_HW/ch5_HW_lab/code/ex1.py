import cv2
import numpy as np
import random
import os

def add_salt_pepper_noise(image, pa, pb):
    row, col = image.shape
    noisy_image = np.copy(image)
    
    # 椒盐噪声的总数量
    num_salt = np.ceil(pa * image.size * 0.5)
    for i in range(row):
        for j in range(col):
            rdn = random.random()
            if rdn < pa:
                noisy_image[i][j] = 0  # 椒噪声 (Pepper)
            elif rdn > 1 - pb:
                noisy_image[i][j] = 255 # 盐噪声 (Salt)
    
    return noisy_image

def main():
    # 读取图像，以灰度模式读取
    current_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(current_dir, 'img', '1a.png')
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    
    if img is None:
        print(f"Error: Could not open or find the image at {img_path}")
        return

    # 添加椒盐噪声 Pa=0.2, Pb=0.2
    noisy_img = add_salt_pepper_noise(img, 0.2, 0.2)

    # 应用中值滤波
    median_filtered_img = cv2.medianBlur(noisy_img, 3)
    
    # 增加 5x5 中值滤波实验
    median_filtered_img_5 = cv2.medianBlur(noisy_img, 5)
    
    output_dir = os.path.dirname(img_path)
    cv2.imwrite(os.path.join(output_dir, '1a_noisy.png'), noisy_img)
    cv2.imwrite(os.path.join(output_dir, '1a_filtered.png'), median_filtered_img)
    cv2.imwrite(os.path.join(output_dir, '1a_filtered_5x5.png'), median_filtered_img_5)
    print(f"Results saved to {output_dir}")

    cv2.imshow('Original Image', img)
    cv2.imshow('Salt & Pepper Noise (Pa=Pb=0.2)', noisy_img)
    cv2.imshow('Median Filtered Result (3x3)', median_filtered_img)
    cv2.imshow('Median Filtered Result (5x5)', median_filtered_img_5)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
