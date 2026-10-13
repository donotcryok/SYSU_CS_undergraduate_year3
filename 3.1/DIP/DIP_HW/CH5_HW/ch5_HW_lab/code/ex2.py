import cv2
import numpy as np
import os

def get_motion_blur_filter(shape, a, b, T=1):
    rows, cols = shape
    u = np.arange(-rows//2, rows//2)
    v = np.arange(-cols//2, cols//2)
    V, U = np.meshgrid(v, u) # V对应列(宽), U对应行(高)
    
    E = np.pi * (U * a + V * b)
    
    H = np.ones_like(E, dtype=np.complex128) * T
    
    mask = np.abs(E) > 1e-6
    H[mask] = (T / E[mask]) * np.sin(E[mask]) * np.exp(-1j * E[mask])
    
    return H

def add_gaussian_noise(image, mean, var):
    sigma = var ** 0.5
    gauss = np.random.normal(mean, sigma, image.shape)
    noisy = image + gauss
    return np.clip(noisy, 0, 255).astype(np.uint8)

def wiener_filter(img_input, H, K):
    # 转换到频域
    f = np.fft.fft2(img_input)
    G = np.fft.fftshift(f)
    
    # 维纳滤波公式 5.85
    
    H_abs_sq = np.abs(H) ** 2
    W = np.conj(H) / (H_abs_sq + K)
    
    F_hat = W * G
    
    # 逆变换回空域
    f_hat = np.fft.ifftshift(F_hat)
    img_back = np.fft.ifft2(f_hat)
    img_back = np.abs(img_back)
    
    return np.clip(img_back, 0, 255).astype(np.uint8)

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(current_dir, 'img', '2b.png')
    
    # 读取图像
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Error: Could not open image at {img_path}")
        return

    rows, cols = img.shape

    # 1. 生成运动模糊
    a = 0.1
    b = 0.1
    T = 1
    H = get_motion_blur_filter((rows, cols), a, b, T)
    
    F = np.fft.fftshift(np.fft.fft2(img))
    G_blur = H * F
    img_blur = np.abs(np.fft.ifft2(np.fft.ifftshift(G_blur)))
    img_blur = np.clip(img_blur, 0, 255).astype(np.uint8)

    # 2. 添加高斯噪声
    img_blur_noisy = add_gaussian_noise(img_blur, 0, 10)

    # 3. 维纳滤波复原
    # K值选取：通常取信噪比倒数或小常数，这里取0.01
    K = 0.01
    img_restored = wiener_filter(img_blur_noisy, H, K)

    output_dir = os.path.dirname(img_path)
    cv2.imwrite(os.path.join(output_dir, '2b_motion_blur.png'), img_blur)
    cv2.imwrite(os.path.join(output_dir, '2b_blur_noisy.png'), img_blur_noisy)
    cv2.imwrite(os.path.join(output_dir, '2b_restored.png'), img_restored)
    print(f"Results saved to {output_dir}")

    cv2.imshow('Original', img)
    cv2.imshow('Blurred & Noisy', img_blur_noisy)
    cv2.imshow('Wiener Restored', img_restored)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
