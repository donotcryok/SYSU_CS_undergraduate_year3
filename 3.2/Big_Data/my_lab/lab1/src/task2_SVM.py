# src/task2_svm.py
import os
import time
import torch
from torchvision import datasets, transforms
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score

def run_svm_classification():
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')

    #transforms.ToTensor() 会将像素值从 0-255 归一化到 0.0-1.0 之间
    train_dataset = datasets.MNIST(root=data_dir, train=True, download=True, transform=transforms.ToTensor())
    test_dataset = datasets.MNIST(root=data_dir, train=False, download=True, transform=transforms.ToTensor())

    #数据预处理与降采样
    num_train = 10000  # 只取前 10000 张训练
    num_test = 2000    # 只取前 2000 张测试
    
    # 提取 Tensor 数据并转换为 numpy 数组
    X_train = train_dataset.data[:num_train].numpy()
    y_train = train_dataset.targets[:num_train].numpy()
    X_test = test_dataset.data[:num_test].numpy()
    y_test = test_dataset.targets[:num_test].numpy()

    # 把 28x28 的二维图像展平为 784 的一维向量
    X_train_flat = X_train.reshape(num_train, -1) / 255.0  # 再次确保归一化
    X_test_flat = X_test.reshape(num_test, -1) / 255.0

    print(f"训练集大小: {X_train_flat.shape}, 测试集大小: {X_test_flat.shape}")

    #初始化 SVM 模型 (使用 RBF 核函数)
    svm_model = SVC(kernel='rbf', gamma='scale')

    #训练模型并计时
    print("\n正在训练 SVM 模型，请耐心等待 (约需几十秒到一两分钟)...")
    start_time = time.time()
    svm_model.fit(X_train_flat, y_train)
    train_time = time.time() - start_time
    print(f"训练完成！耗时: {train_time:.2f} 秒")

    #测试模型并计时
    print("\n⏳ 正在进行测试集推理...")
    start_time = time.time()
    predictions = svm_model.predict(X_test_flat)
    infer_time = time.time() - start_time
    print(f"推理完成！耗时: {infer_time:.2f} 秒")

    #计算准确率
    accuracy = accuracy_score(y_test, predictions)
    print("\n" + "="*30)
    print("SVM 实验结果")
    print("="*30)
    print(f"准确率 (Accuracy): {accuracy * 100:.2f}%")
    print(f"训练耗时: {train_time:.2f} 秒")
    print(f"推理耗时: {infer_time:.2f} 秒")
    print("="*30)

if __name__ == "__main__":
    run_svm_classification()