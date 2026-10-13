# -*- coding: utf-8 -*-
"""
电影评论情感分类实验
包含：TF-IDF + LR/SVM 传统模型，以及 RNN/LSTM 深度模型
使用直接下载方式加载 IMDB 数据集
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tqdm import tqdm
import urllib.request
import tarfile
import re


# 获取 main.py 所在目录 (src)
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
# 向上退一级获取项目根目录
ROOT_DIR = os.path.abspath(os.path.join(SRC_DIR, '..'))

DATA_DIR = os.path.join(ROOT_DIR, 'data')
IMG_DIR = os.path.join(ROOT_DIR, 'img')

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# PyTorch
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# Scikit-learn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score

print("=" * 60)
print("电影评论情感分类实验")
print("=" * 60)

# ============================================================
# 第一部分：数据加载
# ============================================================
print("\n[1/5] 加载IMDB数据集...")

def read_imdb_data(data_dir):
    """读取IMDB数据 - 简化输出，不使用tqdm"""
    train_texts, train_labels = [], []
    test_texts, test_labels = [], []
    
    # 读取训练数据
    for label_type in ['pos', 'neg']:
        dir_path = os.path.join(data_dir, 'train', label_type)
        label = 1 if label_type == 'pos' else 0
        files = os.listdir(dir_path)
        print(f"  正在读取训练集 {label_type} ({len(files)} 文件)...")
        for file_name in files:
            file_path = os.path.join(dir_path, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                train_texts.append(f.read())
                train_labels.append(label)
        print(f"  训练集 {label_type} 读取完成")
    
    # 读取测试数据
    for label_type in ['pos', 'neg']:
        dir_path = os.path.join(data_dir, 'test', label_type)
        label = 1 if label_type == 'pos' else 0
        files = os.listdir(dir_path)
        print(f"  正在读取测试集 {label_type} ({len(files)} 文件)...")
        for file_name in files:
            file_path = os.path.join(dir_path, file_name)
            with open(file_path, 'r', encoding='utf-8') as f:
                test_texts.append(f.read())
                test_labels.append(label)
        print(f"  测试集 {label_type} 读取完成")
    
    return train_texts, train_labels, test_texts, test_labels

# 定位到数据目录
aclImdb_dir = os.path.join(DATA_DIR, 'aclImdb')

print(f"尝试从本地加载数据: {aclImdb_dir}")
if os.path.exists(aclImdb_dir):
    train_texts, train_labels, test_texts, test_labels = read_imdb_data(aclImdb_dir)
    print("本地数据加载成功！")
else:
    raise FileNotFoundError(f"找不到数据文件夹：{aclImdb_dir}，请检查目录结构！")

# 打乱数据
np.random.seed(42)
indices = np.random.permutation(len(train_texts))
train_texts = [train_texts[i] for i in indices]
train_labels = [train_labels[i] for i in indices]

indices = np.random.permutation(len(test_texts))
test_texts = [test_texts[i] for i in indices]
test_labels = [test_labels[i] for i in indices]

# 采样以加快训练速度
train_size = min(10000, len(train_texts))
test_size = min(5000, len(test_texts))

train_texts = train_texts[:train_size]
train_labels = train_labels[:train_size]
test_texts = test_texts[:test_size]
test_labels = test_labels[:test_size]

train_labels = np.array(train_labels)
test_labels = np.array(test_labels)

print(f"训练集大小: {len(train_texts)}")
print(f"测试集大小: {len(test_texts)}")
print(f"正样本比例 - 训练: {sum(train_labels)/len(train_labels):.2%}, 测试: {sum(test_labels)/len(test_labels):.2%}")

# ============================================================
# 第二部分：传统模型 - TF-IDF + LR/SVM
# ============================================================
print("\n[2/5] 传统模型训练 (TF-IDF + LR/SVM)...")

# TF-IDF 特征提取
print("提取TF-IDF特征...")
tfidf_vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
X_train_tfidf = tfidf_vectorizer.fit_transform(train_texts)
X_test_tfidf = tfidf_vectorizer.transform(test_texts)

print(f"TF-IDF特征维度: {X_train_tfidf.shape[1]}")

# 逻辑回归
print("训练逻辑回归模型...")
lr_model = LogisticRegression(max_iter=1000, random_state=42)
lr_model.fit(X_train_tfidf, train_labels)
lr_pred = lr_model.predict(X_test_tfidf)
lr_acc = accuracy_score(test_labels, lr_pred)
print(f"逻辑回归准确率: {lr_acc:.4f}")

# 支持向量机
print("训练SVM模型...")
svm_model = SVC(kernel='linear', random_state=42)
svm_model.fit(X_train_tfidf, train_labels)
svm_pred = svm_model.predict(X_test_tfidf)
svm_acc = accuracy_score(test_labels, svm_pred)
print(f"SVM准确率: {svm_acc:.4f}")

# ============================================================
# 第三部分：深度模型 - RNN/LSTM
# ============================================================
print("\n[3/5] 深度模型训练 (RNN/LSTM)...")

# 构建词汇表
print("构建词汇表...")
from collections import Counter

def clean_text(text):
    """清理文本"""
    text = text.lower()
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return text

def build_vocab(texts, min_freq=2):
    """构建词汇表"""
    counter = Counter()
    for text in texts:
        words = clean_text(text).split()
        counter.update(words)
    
    vocab = {'<pad>': 0, '<unk>': 1}
    for word, freq in counter.items():
        if freq >= min_freq:
            vocab[word] = len(vocab)
    return vocab

vocab = build_vocab(train_texts, min_freq=2)
vocab_size = len(vocab)
print(f"词汇表大小: {vocab_size}")

def text_to_sequence(texts, vocab, max_len=200):
    """将文本转换为词索引序列"""
    sequences = []
    for text in texts:
        words = clean_text(text).split()
        seq = [vocab.get(w, vocab['<unk>']) for w in words[:max_len]]
        if len(seq) < max_len:
            seq += [vocab['<pad>']] * (max_len - len(seq))
        sequences.append(seq)
    return np.array(sequences)

# 文本序列化
print("文本序列化...")
max_len = 200
X_train_seq = text_to_sequence(train_texts, vocab, max_len)
X_test_seq = text_to_sequence(test_texts, vocab, max_len)

# 转换为PyTorch张量
X_train_tensor = torch.LongTensor(X_train_seq)
y_train_tensor = torch.LongTensor(train_labels)
X_test_tensor = torch.LongTensor(X_test_seq)
y_test_tensor = torch.LongTensor(test_labels)

# 创建数据加载器
batch_size = 64
train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
test_dataset = TensorDataset(X_test_tensor, y_test_tensor)
train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

# 定义LSTM模型
class SentimentLSTM(nn.Module):
    """
    情感分析LSTM模型
    结构：Embedding -> LSTM -> 全连接 -> 输出
    """
    def __init__(self, vocab_size, embed_dim, hidden_dim, output_dim, n_layers=2, dropout=0.3):
        super(SentimentLSTM, self).__init__()
        
        # 词嵌入层：将词索引转换为稠密向量
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        
        # LSTM层：捕捉序列信息
        self.lstm = nn.LSTM(
            embed_dim, 
            hidden_dim, 
            num_layers=n_layers, 
            batch_first=True, 
            dropout=dropout,
            bidirectional=True
        )
        
        # 全连接层
        self.fc = nn.Linear(hidden_dim * 2, output_dim)
        self.dropout = nn.Dropout(dropout)
        
    def forward(self, x):
        # x: [batch_size, seq_len]
        embedded = self.dropout(self.embedding(x))  # [batch_size, seq_len, embed_dim]
        
        # LSTM输出
        lstm_out, (hidden, cell) = self.lstm(embedded)
        
        # 取最后一层的双向隐藏状态
        hidden_cat = torch.cat((hidden[-2], hidden[-1]), dim=1)  # [batch_size, hidden_dim*2]
        
        # 全连接输出
        out = self.fc(self.dropout(hidden_cat))
        return out

# 模型参数
embed_dim = 128
hidden_dim = 128
output_dim = 2
n_layers = 2
dropout = 0.3
learning_rate = 0.001

# 初始化模型
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"使用设备: {device}")

model = SentimentLSTM(vocab_size, embed_dim, hidden_dim, output_dim, n_layers, dropout)
model = model.to(device)

# 损失函数和优化器
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate)

# 训练函数 - 简化输出，禁用batch级别tqdm
def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    
    for batch_x, batch_y in loader:  # 移除tqdm，静默训练
        batch_x, batch_y = batch_x.to(device), batch_y.to(device)
        
        optimizer.zero_grad()
        outputs = model(batch_x)
        loss = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        _, predicted = outputs.max(1)
        total += batch_y.size(0)
        correct += predicted.eq(batch_y).sum().item()
    
    return total_loss / len(loader), correct / total

# 评估函数
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for batch_x, batch_y in loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            
            total_loss += loss.item()
            _, predicted = outputs.max(1)
            total += batch_y.size(0)
            correct += predicted.eq(batch_y).sum().item()
    
    return total_loss / len(loader), correct / total

# 训练循环
print("开始训练LSTM模型...")
n_epochs = 10
train_losses = []
train_accs = []
val_losses = []
val_accs = []

for epoch in range(n_epochs):
    train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
    val_loss, val_acc = evaluate(model, test_loader, criterion, device)
    
    train_losses.append(train_loss)
    train_accs.append(train_acc)
    val_losses.append(val_loss)
    val_accs.append(val_acc)
    
    # 每个Epoch只打印一行汇总信息
    print(f"Epoch [{epoch+1}/{n_epochs}] | Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f} | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}")

# 最终测试准确率
lstm_acc = val_accs[-1]
print(f"\nLSTM最终测试准确率: {lstm_acc:.4f}")

# ============================================================
# 第四部分：结果可视化
# ============================================================
print("\n[4/5] 生成可视化图表...")

# 图1：模型准确率对比柱状图
plt.figure(figsize=(10, 6))
models = ['Logistic Regression', 'SVM', 'LSTM']
accuracies = [lr_acc, svm_acc, lstm_acc]
colors = ['#3498db', '#2ecc71', '#e74c3c']

bars = plt.bar(models, accuracies, color=colors, width=0.6, edgecolor='black', linewidth=1.2)

# 添加数值标签
for bar, acc in zip(bars, accuracies):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
             f'{acc:.4f}', ha='center', va='bottom', fontsize=12, fontweight='bold')

plt.xlabel('模型', fontsize=12)
plt.ylabel('准确率', fontsize=12)
plt.title('三种模型在IMDB情感分类任务上的准确率对比', fontsize=14)
plt.ylim(0, 1.0)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'accuracy_comparison.png'), dpi=150, bbox_inches='tight')
plt.close()
print(f"已保存: {os.path.join(IMG_DIR, 'accuracy_comparison.png')}")

# 图2：LSTM训练过程曲线
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Loss曲线
ax1.plot(range(1, n_epochs+1), train_losses, 'b-', label='训练损失', linewidth=2, marker='o')
ax1.plot(range(1, n_epochs+1), val_losses, 'r-', label='验证损失', linewidth=2, marker='s')
ax1.set_xlabel('Epoch', fontsize=12)
ax1.set_ylabel('Loss', fontsize=12)
ax1.set_title('LSTM训练过程 - 损失曲线', fontsize=14)
ax1.legend(fontsize=10)
ax1.grid(True, linestyle='--', alpha=0.7)

# Accuracy曲线
ax2.plot(range(1, n_epochs+1), train_accs, 'b-', label='训练准确率', linewidth=2, marker='o')
ax2.plot(range(1, n_epochs+1), val_accs, 'r-', label='验证准确率', linewidth=2, marker='s')
ax2.set_xlabel('Epoch', fontsize=12)
ax2.set_ylabel('Accuracy', fontsize=12)
ax2.set_title('LSTM训练过程 - 准确率曲线', fontsize=14)
ax2.legend(fontsize=10)
ax2.grid(True, linestyle='--', alpha=0.7)

plt.tight_layout()
plt.savefig(os.path.join(IMG_DIR, 'lstm_training_curves.png'), dpi=150, bbox_inches='tight')
plt.close()
print(f"已保存: {os.path.join(IMG_DIR, 'lstm_training_curves.png')}")

# ============================================================
# 第五部分：结果汇总
# ============================================================
print("\n[5/5] 实验结果汇总")
print("=" * 60)
print(f"{'模型':<25} {'准确率':<10}")
print("-" * 40)
print(f"{'逻辑回归 (TF-IDF)':<25} {lr_acc:.4f}")
print(f"{'SVM (TF-IDF)':<25} {svm_acc:.4f}")
print(f"{'LSTM (Embedding)':<25} {lstm_acc:.4f}")
print("=" * 60)

# 保存详细结果
results_path = os.path.join(IMG_DIR, 'results.txt')
with open(results_path, 'w', encoding='utf-8') as f:
    f.write("=" * 60 + "\n")
    f.write("IMDB 电影评论情感分类实验结果报告\n")
    f.write("=" * 60 + "\n\n")
    
    # 写入最终准确率
    f.write("[最终准确率对比]\n")
    f.write("-" * 40 + "\n")
    f.write(f"逻辑回归 (LR with TF-IDF): {lr_acc:.4f}\n")
    f.write(f"支持向量机 (SVM with TF-IDF): {svm_acc:.4f}\n")
    f.write(f"长短期记忆网络 (LSTM): {lstm_acc:.4f}\n")
    f.write("-" * 40 + "\n\n")
    
    # 写入LSTM超参数
    f.write("[LSTM 模型超参数配置]\n")
    f.write("-" * 40 + "\n")
    f.write(f"词汇表大小 (vocab_size): {vocab_size}\n")
    f.write(f"词嵌入维度 (embed_dim): {embed_dim}\n")
    f.write(f"隐藏层维度 (hidden_dim): {hidden_dim}\n")
    f.write(f"输出维度 (output_dim): {output_dim}\n")
    f.write(f"LSTM层数 (n_layers): {n_layers}\n")
    f.write(f"Dropout率: {dropout}\n")
    f.write(f"批大小 (batch_size): {batch_size}\n")
    f.write(f"学习率 (learning_rate): {learning_rate}\n")
    f.write(f"训练轮数 (epochs): {n_epochs}\n")
    f.write(f"最大序列长度 (max_len): {max_len}\n")
    f.write(f"训练集样本数: {train_size}\n")
    f.write(f"测试集样本数: {test_size}\n")
    f.write("-" * 40 + "\n\n")
    
    # 写入每个Epoch的训练详情
    f.write("[LSTM 训练过程详细记录]\n")
    f.write("-" * 60 + "\n")
    f.write(f"{'Epoch':<8} {'Train Loss':<12} {'Train Acc':<12} {'Val Loss':<12} {'Val Acc':<12}\n")
    f.write("-" * 60 + "\n")
    for i in range(n_epochs):
        f.write(f"{i+1:<8} {train_losses[i]:<12.4f} {train_accs[i]:<12.4f} {val_losses[i]:<12.4f} {val_accs[i]:<12.4f}\n")
    f.write("-" * 60 + "\n\n")
    
print(f"\n详细结果已保存至: {results_path}")
print("\n实验完成！图表已保存到 img/ 目录。")