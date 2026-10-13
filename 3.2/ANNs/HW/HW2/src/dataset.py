# src/dataset.py
# 中文短新闻主题分类 — 数据预处理、词表构建、DataLoader 封装
#
# 核心功能:
#   1. JSONL 格式数据读取 (UTF-8 编码)
#   2. 文本清洗: 去除多余空格、不可见字符、控制字符
#   3. jieba 精确模式中文分词
#   4. 基于训练集构建词表 (<PAD>=0, <UNK>=1)
#   5. 序列截断/填充至统一长度
#   6. 标签编码为 0~14 整数
#   7. PyTorch Dataset 与 DataLoader 封装

import json
import re
import random
import os
from typing import List, Dict, Tuple, Optional

import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader

import jieba

# ======================== 全局随机种子 ========================
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)

# ======================== 常量定义 ========================
PAD_TOKEN = "<PAD>"
UNK_TOKEN = "<UNK>"
PAD_IDX = 0
UNK_IDX = 1


# ======================== 文本清洗 ========================
def clean_text(text: str) -> str:
    """清洗中文文本: 去除不可见控制字符, 规范化空白, 去除首尾空格。

    Args:
        text: 原始字符串

    Returns:
        清洗后的字符串
    """
    # 去除控制字符 (保留换行符, 后续会替换为空格)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    # 将换行符、制表符等替换为空格
    text = re.sub(r'[\r\n\t]+', ' ', text)
    # 压缩多个空格为单个
    text = re.sub(r'\s+', ' ', text)
    # 去除首尾空格
    text = text.strip()
    return text


# ======================== 中文分词 ========================
def tokenize(text: str) -> List[str]:
    """使用 jieba 精确模式对中文文本进行词级分词。

    Args:
        text: 待分词的中文文本

    Returns:
        词级 token 列表
    """
    cleaned = clean_text(text)
    tokens = jieba.lcut(cleaned)
    tokens = [t.strip() for t in tokens if t.strip()]
    return tokens


def tokenize_char(text: str) -> List[str]:
    """字符级切分: 将清洗后文本按字符逐个拆分。

    设计动机:
        - 词表从 ~32K (词级) 压缩至 ~3K (字级), 嵌入参数量缩减约 10 倍
        - 字符级切分天然解决 OOV 问题, 且极大削弱模型记忆稀疏 n-gram 的能力,
          从而抑制在 48K 小样本集上的过拟合

    Args:
        text: 待切分的中文文本

    Returns:
        字符级 token 列表
    """
    cleaned = clean_text(text)
    return [ch for ch in cleaned if ch.strip()]


# ======================== 词表构建 ========================
def build_vocab(tokenized_sentences: List[List[str]],
                min_freq: int = 1,
                max_vocab_size: Optional[int] = None) -> Dict[str, int]:
    """仅基于训练集的分词结果构建词表。

    Args:
        tokenized_sentences: 训练集内每条样本的分词列表
        min_freq: 词频最小阈值, 低于此值不纳入词表
        max_vocab_size: 词表最大容量 (None 表示不限制)

    Returns:
        word2idx 映射字典, 已预留 <PAD> 和 <UNK>
    """
    freq = {}
    for tokens in tokenized_sentences:
        for token in tokens:
            freq[token] = freq.get(token, 0) + 1

    # 按频率降序排序
    sorted_tokens = sorted(freq.items(), key=lambda x: -x[1])

    # 过滤低频词
    filtered = [(t, f) for t, f in sorted_tokens if f >= min_freq]

    # 限制词表大小
    if max_vocab_size is not None:
        filtered = filtered[:max_vocab_size - 2]  # 预留 PAD 和 UNK

    word2idx = {PAD_TOKEN: PAD_IDX, UNK_TOKEN: UNK_IDX}
    for idx, (token, _) in enumerate(filtered, start=2):
        word2idx[token] = idx

    return word2idx


# ======================== 标签映射 ========================
def build_label_map(labels_file: str) -> Tuple[Dict[str, int], Dict[int, str]]:
    """从 labels.json 构建类别名称→索引 和 索引→类别名称 的双向映射。

    Args:
        labels_file: labels.json 文件路径

    Returns:
        (label2idx, idx2label) 双向映射
    """
    label2idx = {}
    idx2label = {}

    with open(labels_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            label_desc = item['label_desc']
            # 按 JSONL 中的出现顺序自增索引
            idx = len(label2idx)
            label2idx[label_desc] = idx
            idx2label[idx] = label_desc

    return label2idx, idx2label


# ======================== 序列填充与截断 ========================
def pad_or_truncate(token_ids: List[int], max_len: int) -> List[int]:
    """对 token ID 序列进行截断或填充至固定长度。

    Args:
        token_ids: token ID 列表
        max_len: 目标长度

    Returns:
        处理后的固定长度序列
    """
    if len(token_ids) >= max_len:
        return token_ids[:max_len]
    else:
        return token_ids + [PAD_IDX] * (max_len - len(token_ids))


# ======================== JSONL 数据加载 ========================
def load_jsonl(file_path: str) -> List[Dict]:
    """读取 JSONL 格式数据文件。

    Args:
        file_path: JSONL 文件路径

    Returns:
        dict 列表, 每个 dict 包含 sentence, label_desc, label 字段
    """
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data.append(json.loads(line))
    return data


# ======================== 从原始数据到 token ID ========================
def texts_to_ids(texts: List[str],
                 word2idx: Dict[str, int],
                 max_len: int) -> List[List[int]]:
    """将原始文本列表转换为 token ID 序列 (字符级切分、ID 映射、填充/截断)。

    Args:
        texts: 原始文本列表
        word2idx: 词表映射
        max_len: 统一序列长度

    Returns:
        token ID 序列列表
    """
    all_ids = []
    for text in texts:
        tokens = tokenize_char(text)
        ids = [word2idx.get(t, UNK_IDX) for t in tokens]
        ids = pad_or_truncate(ids, max_len)
        all_ids.append(ids)
    return all_ids


# ======================== 计算最佳 max_len ========================
def compute_max_len(tokenized_sentences: List[List[str]],
                    coverage: float = 0.95) -> int:
    """根据训练集中分词后序列长度的分位数确定 max_len。

    Args:
        tokenized_sentences: 训练集分词结果
        coverage: 覆盖比例 (默认 95%)

    Returns:
        建议的 max_len 值
    """
    lengths = [len(tokens) for tokens in tokenized_sentences]
    return int(np.percentile(lengths, coverage * 100))


# ======================== PyTorch Dataset ========================
class TNewsDataset(Dataset):
    """TNEWS 中文短新闻主题分类 PyTorch Dataset。

    负责:
      - 存储已转换为 token ID 的样本
      - 返回 (input_ids, label_idx) 张量对
    """

    def __init__(self,
                 input_ids: List[List[int]],
                 labels: List[int]):
        """
        Args:
            input_ids: 已填充/截断的 token ID 序列列表
            labels: 整数标签列表
        """
        self.input_ids = torch.tensor(input_ids, dtype=torch.long)
        self.labels = torch.tensor(labels, dtype=torch.long)

    def __len__(self) -> int:
        return len(self.input_ids)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return self.input_ids[idx], self.labels[idx]


# ======================== 主数据构建流水线 ========================
def build_dataloaders(train_file: str,
                      dev_file: str,
                      labels_file: str,
                      batch_size: int = 64,
                      max_len: Optional[int] = None,
                      coverage: float = 0.95,
                      min_freq: int = 2,
                      num_workers: int = 4) -> Tuple[DataLoader, DataLoader, DataLoader, dict]:
    """一站式数据预处理流水线: 从原始 JSONL 到 PyTorch DataLoader。

    步骤:
      1. 加载原始数据
      2. 文本清洗 + 字符级切分
      3. 构建标签映射
      4. 构建词表 (仅训练集)
      5. 计算/使用 max_len
      6. 文本 → token ID 转换
      7. 训练/验证集 90/10 划分
      8. 创建 Dataset 和 DataLoader

    Args:
        train_file: 训练集 JSONL 路径
        dev_file: 测试集 JSONL 路径 (用作最终测试)
        labels_file: 标签映射 JSONL 路径
        batch_size: 批大小
        max_len: 统一序列长度 (None 则自动计算)
        coverage: 自动计算 max_len 时的覆盖比例
        min_freq: 词表最小词频
        num_workers: DataLoader 工作进程数

    Returns:
        (train_loader, val_loader, test_loader, metadata)
        metadata 包含:
          - word2idx: 词表映射
          - idx2label: 索引→类别名称映射
          - num_classes: 类别数
          - vocab_size: 词表大小
          - max_len: 实际使用的序列长度
    """

    # ---- 1. 加载原始数据 ----
    print("[dataset] 加载原始数据...")
    train_raw = load_jsonl(train_file)
    dev_raw = load_jsonl(dev_file)

    print(f"  train.json: {len(train_raw)} 条")
    print(f"  dev.json (测试): {len(dev_raw)} 条")

    # ---- 2. 构建标签映射 ----
    print("[dataset] 构建标签映射...")
    label2idx, idx2label = build_label_map(labels_file)
    num_classes = len(label2idx)
    print(f"  类别数: {num_classes}")
    for idx, name in sorted(idx2label.items()):
        print(f"    [{idx}] {name}")

    # ---- 3. 训练集分词 (字符级切分) ----
    print("[dataset] 训练集分词 (模式: 字符级)...")
    train_texts = [item['sentence'] for item in train_raw]
    train_tokenized = [tokenize_char(text) for text in train_texts]

    # ---- 4. 构建词表 (仅训练集) ----
    print("[dataset] 构建词表 (仅训练集)...")
    word2idx = build_vocab(train_tokenized, min_freq=min_freq)
    vocab_size = len(word2idx)
    print(f"  词表大小: {vocab_size} (含 <PAD>, <UNK>)")

    # ---- 5. 自动计算 max_len ----
    if max_len is None:
        max_len = compute_max_len(train_tokenized, coverage=coverage)
        print(f"[dataset] 自动计算 max_len = {max_len} (覆盖 {coverage*100:.0f}% 样本)")

    # ---- 6. 文本 → token ID ----
    print("[dataset] 文本 → token ID 转换...")
    train_ids = texts_to_ids(train_texts, word2idx, max_len)
    train_labels = [label2idx[item['label_desc']] for item in train_raw]

    dev_texts = [item['sentence'] for item in dev_raw]
    dev_ids = texts_to_ids(dev_texts, word2idx, max_len)
    dev_labels = [label2idx[item['label_desc']] for item in dev_raw]

    # ---- 7. 训练/验证集 90/10 划分 (固定随机种子) ----
    print("[dataset] 训练/验证集 90/10 划分 (seed=42)...")
    indices = list(range(len(train_ids)))
    rng = random.Random(SEED)
    rng.shuffle(indices)

    split = int(0.9 * len(indices))
    train_indices = indices[:split]
    val_indices = indices[split:]

    print(f"  训练: {len(train_indices)} 条, 验证: {len(val_indices)} 条, 测试: {len(dev_ids)} 条")

    # ---- 8. 创建 Dataset ----
    train_dataset = TNewsDataset(
        [train_ids[i] for i in train_indices],
        [train_labels[i] for i in train_indices]
    )
    val_dataset = TNewsDataset(
        [train_ids[i] for i in val_indices],
        [train_labels[i] for i in val_indices]
    )
    test_dataset = TNewsDataset(dev_ids, dev_labels)

    # ---- 9. 创建 DataLoader ----
    # 检测 CUDA 可用性, 启用 pin_memory 加速数据传输
    use_cuda = torch.cuda.is_available()
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=use_cuda,
        drop_last=False,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=use_cuda,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=use_cuda,
    )

    print(f"[dataset] DataLoader 创建完成 (pin_memory={'GPU' if use_cuda else 'CPU'})")

    metadata = {
        'word2idx': word2idx,
        'idx2label': idx2label,
        'label2idx': label2idx,
        'num_classes': num_classes,
        'vocab_size': vocab_size,
        'max_len': max_len,
    }

    return train_loader, val_loader, test_loader, metadata


# ======================== 模块自检 ========================
if __name__ == "__main__":
    print("=" * 60)
    print("dataset.py 模块自检")
    print("=" * 60)

    train_file = "data/train.json"
    dev_file = "data/dev.json"
    labels_file = "data/labels.json"

    train_loader, val_loader, test_loader, meta = build_dataloaders(
        train_file=train_file,
        dev_file=dev_file,
        labels_file=labels_file,
        batch_size=64,
        min_freq=2,
        num_workers=0,  # Windows/WSL 兼容性
    )

    print("\n[自检] 元数据:")
    print(f"  词表大小: {meta['vocab_size']}")
    print(f"  类别数: {meta['num_classes']}")
    print(f"  max_len: {meta['max_len']}")

    print("\n[自检] 数据批样例:")
    for batch_idx, (inputs, labels) in enumerate(train_loader):
        print(f"  Batch {batch_idx}: inputs shape={inputs.shape}, labels shape={labels.shape}")
        print(f"  前5个标签: {labels[:5].tolist()}")
        print(f"  前3条样本的首10个 token ID: {inputs[:3, :10].tolist()}")
        break

    print("\n[自检] ✅ 所有数据预处理流水线验证通过！")
