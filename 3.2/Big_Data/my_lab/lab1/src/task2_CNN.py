import os
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader

class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        #第一层卷积: 输入 1 通道(灰度图)，输出 16 个特征图，卷积核大小 3x3
        self.conv1 = nn.Conv2d(1, 16, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        #最大池化层: 缩小图像尺寸 (28x28 变成 14x14)
        self.pool = nn.MaxPool2d(2, 2)
        #全连接层: 16通道 * 14高 * 14宽 -> 10个类别 (0-9)
        self.fc = nn.Linear(16 * 14 * 14, 10)

    def forward(self, x):
        x = self.conv1(x)   
        x = self.relu(x)   
        x = self.pool(x)   
        x = x.view(x.size(0), -1)
        x = self.fc(x)   
        return x

def run_cnn_classification():
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"当前使用的计算设备: {device}")

    #加载数据
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')

    transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))])
    
    #加载全部 60000 张图，并使用 DataLoader 进行分批处理 (Batching)
    train_dataset = datasets.MNIST(root=data_dir, train=True, download=True, transform=transform)
    test_dataset = datasets.MNIST(root=data_dir, train=False, download=True, transform=transform)
    
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=1000, shuffle=False)

    #初始化模型、损失函数和优化器
    model = SimpleCNN().to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    #训练模型并计时
    epochs = 1
    print(f"\n正在训练 CNN 模型 (共 {epochs} 轮)...")
    start_time = time.time()
    
    model.train()
    for epoch in range(epochs):
        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(device), target.to(device)
            
            optimizer.zero_grad()   # 梯度清零
            output = model(data)    # 前向传播
            loss = criterion(output, target) # 计算损失
            loss.backward()         # 反向传播
            optimizer.step()        # 更新权重
            
            if batch_idx % 200 == 0:
                print(f"   Epoch {epoch+1} | Batch {batch_idx}/{len(train_loader)} | Loss: {loss.item():.4f}")
                
    train_time = time.time() - start_time
    print(f"训练完成！耗时: {train_time:.2f} 秒")

    # 5. 测试模型并计时
    print("\n正在进行测试集推理...")
    model.eval()
    correct = 0
    total = 0
    start_time = time.time()
    
    with torch.no_grad(): # 推理时不需要计算梯度
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            outputs = model(data)
            _, predicted = torch.max(outputs.data, 1)
            total += target.size(0)
            correct += (predicted == target).sum().item()
            
    infer_time = time.time() - start_time
    accuracy = correct / total
    print(f"推理完成！耗时: {infer_time:.2f} 秒")

    # 6. 输出对比报告
    print("\n" + "="*30)
    print("CNN 实验结果报告")
    print("="*30)
    print(f"准确率 (Accuracy): {accuracy * 100:.2f}%")
    print(f"训练耗时: {train_time:.2f} 秒")
    print(f"推理耗时: {infer_time:.2f} 秒")
    print("="*30)

if __name__ == "__main__":
    run_cnn_classification()
    