# src/train.py
# 中文短新闻主题分类 — 训练与验证循环
#
# 核心功能:
#   1. 命令行参数解析 (模型类型、超参数、数据路径)
#   2. 训练/验证循环 with 早停 (Early Stopping)
#   3. 每个 Epoch 计算 Accuracy 和 Macro-F1
#   4. 保存最佳模型权重至 models/ 目录
#   5. 记录训练/验证损失曲线数据
#   6. 全局随机种子固定 (42)

import os
import sys
import json
import time
import random
import argparse
from typing import Dict, List, Tuple, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from sklearn.metrics import accuracy_score, f1_score

# 将项目 src/ 加入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataset import build_dataloaders
from models import create_model

# ======================== 全局随机种子 ========================
SEED = 42


def set_seed(seed: int = SEED):
    """固定所有随机种子以确保可复现性。"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        # 确保 CUDA 卷积等操作确定性 (可能略微降低性能)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


# ======================== 早停管理器 ========================
class EarlyStopping:
    """早停管理器: 监控验证损失, 若连续 patience 次无改善则停止训练。

    同时负责保存最佳模型权重。
    """

    def __init__(self, patience: int = 5, min_delta: float = 0.0,
                 save_path: str = "models/best_model.pt",
                 verbose: bool = True):
        """
        Args:
            patience: 允许的连续无改善 epoch 数
            min_delta: 被视为改善的最小损失变化
            save_path: 最佳模型保存路径
            verbose: 是否打印早停日志
        """
        self.patience = patience
        self.min_delta = min_delta
        self.save_path = save_path
        self.verbose = verbose

        self.counter = 0
        self.best_loss = float('inf')
        self.early_stop = False

        # 确保模型保存目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

    def __call__(self, val_loss: float, model: nn.Module) -> bool:
        """
        Args:
            val_loss: 当前 epoch 的验证损失
            model: 当前模型 (用于保存最佳权重)

        Returns:
            True 表示应停止训练
        """
        if val_loss < self.best_loss - self.min_delta:
            self.best_loss = val_loss
            self.counter = 0
            self._save_checkpoint(model)
            if self.verbose:
                print(f"  [早停] 验证损失改善 → {val_loss:.6f}, 已保存模型")
        else:
            self.counter += 1
            if self.verbose:
                print(f"  [早停] 验证损失未改善 ({self.counter}/{self.patience})")
            if self.counter >= self.patience:
                self.early_stop = True
        return self.early_stop

    def _save_checkpoint(self, model: nn.Module):
        """保存模型权重 (仅 state_dict)。"""
        torch.save(model.state_dict(), self.save_path)


# ======================== 单 Epoch 训练 ========================
def train_epoch(model: nn.Module,
                dataloader: DataLoader,
                criterion: nn.Module,
                optimizer: optim.Optimizer,
                device: torch.device,
                clip_grad: Optional[float] = None) -> Tuple[float, float, float]:
    """执行一个训练 epoch。

    Args:
        model: 分类模型
        dataloader: 训练 DataLoader
        criterion: 损失函数
        optimizer: 优化器
        device: CUDA/CPU 设备
        clip_grad: 梯度裁剪阈值 (None 则不裁剪)

    Returns:
        (avg_loss, accuracy, macro_f1)
    """
    model.train()
    total_loss = 0.0
    all_preds = []
    all_labels = []

    for batch_idx, (inputs, labels) in enumerate(dataloader):
        # 数据转移到 GPU
        inputs = inputs.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        # 前向传播
        optimizer.zero_grad()

        # BiLSTM 模型返回 (logits, attn_weights); Transformer 仅返回 logits
        output = model(inputs)
        if isinstance(output, tuple):
            logits = output[0]
        else:
            logits = output

        # 损失计算
        loss = criterion(logits, labels)

        # 反向传播
        loss.backward()

        # 梯度裁剪 (可选)
        if clip_grad is not None:
            torch.nn.utils.clip_grad_norm_(model.parameters(), clip_grad)

        optimizer.step()

        # 统计
        total_loss += loss.item()
        preds = torch.argmax(logits, dim=-1)
        all_preds.extend(preds.cpu().tolist())
        all_labels.extend(labels.cpu().tolist())

    avg_loss = total_loss / len(dataloader)
    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, average='macro')

    return avg_loss, acc, f1


# ======================== 验证 ========================
@torch.no_grad()
def validate(model: nn.Module,
             dataloader: DataLoader,
             criterion: nn.Module,
             device: torch.device) -> Tuple[float, float, float]:
    """执行验证 (不计算梯度)。

    Args:
        model: 分类模型
        dataloader: 验证 DataLoader
        criterion: 损失函数
        device: CUDA/CPU 设备

    Returns:
        (avg_loss, accuracy, macro_f1)
    """
    model.eval()
    total_loss = 0.0
    all_preds = []
    all_labels = []

    for inputs, labels in dataloader:
        inputs = inputs.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        output = model(inputs)
        if isinstance(output, tuple):
            logits = output[0]
        else:
            logits = output

        loss = criterion(logits, labels)

        total_loss += loss.item()
        preds = torch.argmax(logits, dim=-1)
        all_preds.extend(preds.cpu().tolist())
        all_labels.extend(labels.cpu().tolist())

    avg_loss = total_loss / len(dataloader)
    acc = accuracy_score(all_labels, all_preds)
    f1 = f1_score(all_labels, all_preds, average='macro')

    return avg_loss, acc, f1


# ======================== 主训练流水线 ========================
def train(args: argparse.Namespace):
    """完整训练流水线。

    步骤:
      1. 构建 DataLoader
      2. 创建模型并移至 GPU
      3. 定义损失函数和优化器
      4. 训练循环 (含早停)
      5. 保存训练历史记录
    """
    # ---- 0. 固定随机种子 ----
    set_seed(SEED)

    # ---- 1. 设备检测 ----
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"[train] 运行设备: {device}")
    if device.type == 'cuda':
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # ---- 2. 构建 DataLoader ----
    print("\n[train] 构建数据流水线...")
    train_loader, val_loader, test_loader, metadata = build_dataloaders(
        train_file=args.train_file,
        dev_file=args.dev_file,
        labels_file=args.labels_file,
        batch_size=args.batch_size,
        max_len=args.max_len,
        coverage=args.coverage,
        min_freq=args.min_freq,
        num_workers=args.num_workers,
    )

    # ---- 3. 创建模型 ----
    print(f"\n[train] 创建模型: {args.model_type}")
    model = create_model(
        model_type=args.model_type,
        vocab_size=metadata['vocab_size'],
        num_classes=metadata['num_classes'],
        embed_dim=args.embed_dim,
        hidden_dim=args.hidden_dim,
        attn_dim=args.attn_dim,
        num_layers=args.num_layers,
        dropout=args.dropout,
        d_model=args.d_model,
        nhead=args.nhead,
        num_encoder_layers=args.num_encoder_layers,
        dim_feedforward=args.dim_feedforward,
        max_len=metadata['max_len'],
    )
    model = model.to(device)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  总参数量: {total_params:,}")
    print(f"  可训练参数: {trainable_params:,}")

    # ---- 4. 损失函数 & 优化器 ----
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1).to(device)
    optimizer = optim.AdamW(
        model.parameters(),
        lr=args.lr,
        weight_decay=1e-4,
    )

    # 学习率调度器 (可选)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',
        factor=0.5,
        patience=2,
        verbose=True,
    )

    # ---- 5. 早停 ----
    model_save_path = f"models/{args.model_type}_best.pt"
    early_stopping = EarlyStopping(
        patience=args.patience,
        save_path=model_save_path,
        verbose=True,
    )

    # ---- 6. 训练循环 ----
    print(f"\n{'='*60}")
    print(f"开始训练 | 模型: {args.model_type} | Epochs: {args.epochs}")
    print(f"{'='*60}")

    history = {
        'train_loss': [],
        'train_acc': [],
        'train_f1': [],
        'val_loss': [],
        'val_acc': [],
        'val_f1': [],
    }

    best_val_f1 = 0.0
    best_epoch = 0

    for epoch in range(1, args.epochs + 1):
        epoch_start = time.time()

        # 训练
        train_loss, train_acc, train_f1 = train_epoch(
            model, train_loader, criterion, optimizer, device, args.clip_grad
        )
        # 验证
        val_loss, val_acc, val_f1 = validate(
            model, val_loader, criterion, device
        )

        # 学习率调度
        scheduler.step(val_loss)

        # 记录历史
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['train_f1'].append(train_f1)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        history['val_f1'].append(val_f1)

        # 跟踪最佳 F1
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_epoch = epoch

        epoch_time = time.time() - epoch_start

        # 打印 epoch 统计
        print(f"\nEpoch {epoch:3d}/{args.epochs} | Time: {epoch_time:.1f}s")
        print(f"  Train  | Loss: {train_loss:.4f} | Acc: {train_acc:.4f} | F1: {train_f1:.4f}")
        print(f"  Val    | Loss: {val_loss:.4f} | Acc: {val_acc:.4f} | F1: {val_f1:.4f}")
        print(f"  LR: {optimizer.param_groups[0]['lr']:.2e}")

        # 早停检查
        if early_stopping(val_loss, model):
            print(f"\n[train] 早停触发! 在 Epoch {epoch} 停止训练。")
            break

    print(f"\n{'='*60}")
    print(f"训练完成 | 最佳 Epoch: {best_epoch} | 最佳 Val F1: {best_val_f1:.4f}")
    print(f"最佳模型已保存至: {model_save_path}")
    print(f"{'='*60}")

    # ---- 7. 保存训练历史 ----
    history_path = f"models/{args.model_type}_history.json"
    os.makedirs("models", exist_ok=True)
    with open(history_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print(f"[train] 训练历史已保存至: {history_path}")

    return history, metadata


# ======================== 命令行入口 ========================
def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="中文短新闻主题分类 — 训练脚本"
    )

    # 数据参数
    parser.add_argument('--train_file', type=str, default='data/train.json')
    parser.add_argument('--dev_file', type=str, default='data/dev.json')
    parser.add_argument('--labels_file', type=str, default='data/labels.json')

    # 模型参数
    parser.add_argument('--model_type', type=str, default='bilstm',
                        choices=['bilstm', 'transformer'],
                        help="模型架构: bilstm 或 transformer")

    # BiLSTM 参数
    parser.add_argument('--embed_dim', type=int, default=256)
    parser.add_argument('--hidden_dim', type=int, default=128)
    parser.add_argument('--attn_dim', type=int, default=128)
    parser.add_argument('--num_layers', type=int, default=2)

    # Transformer 参数
    parser.add_argument('--d_model', type=int, default=256)
    parser.add_argument('--nhead', type=int, default=8)
    parser.add_argument('--num_encoder_layers', type=int, default=4)
    parser.add_argument('--dim_feedforward', type=int, default=1024)

    # 通用参数
    parser.add_argument('--dropout', type=float, default=0.5)
    parser.add_argument('--batch_size', type=int, default=64)
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--weight_decay', type=float, default=1e-5)
    parser.add_argument('--clip_grad', type=float, default=1.0)
    parser.add_argument('--patience', type=int, default=5)
    parser.add_argument('--coverage', type=float, default=0.95)
    parser.add_argument('--min_freq', type=int, default=2)
    parser.add_argument('--max_len', type=int, default=None)
    parser.add_argument('--num_workers', type=int, default=4)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(args)
