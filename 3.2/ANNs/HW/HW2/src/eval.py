# src/eval.py
# 中文短新闻主题分类 — 测试集评估与可视化
#
# 核心功能:
#   1. 加载训练好的最佳模型权重
#   2. 在 dev.json (测试集) 上执行推理
#   3. 计算 Accuracy, Macro-F1, 各类别 Precision/Recall/F1
#   4. 生成并保存混淆矩阵 (confusion_matrix.png)
#   5. 生成并保存损失曲线 (loss_curves.png)

import os
import sys
import json
import random
import glob
import argparse
from typing import Dict, List, Tuple, Optional

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_recall_fscore_support,
    confusion_matrix as sklearn_cm,
)
import matplotlib
matplotlib.use('Agg')  # 无 GUI 后端
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib import font_manager

# 将项目 src/ 加入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dataset import build_dataloaders
from models import create_model

# ======================== 全局随机种子 ========================
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed(SEED)

# ======================== 中文字体配置 ========================
def setup_chinese_font():
    """配置 matplotlib 中文字体, 使其支持中文标签显示。

    优先使用 WenQuanYi Micro Hei 字体, 通过直接指定字体文件路径绕过
    matplotlib 字体缓存问题。
    """
    # 删除 matplotlib 字体列表缓存以强制刷新
    cache_dir = matplotlib.get_cachedir()
    for cache_file in glob.glob(os.path.join(cache_dir, 'fontlist-v*.json')):
        try:
            os.remove(cache_file)
        except Exception:
            pass

    font_manager._load_fontmanager(try_read_cache=False)

    # 显式查找 WenQuanYi Micro Hei 字体文件
    wqy_paths = [
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/opentype/wqy/wqy-microhei.ttc',
    ]
    font_path = None
    for p in wqy_paths:
        if os.path.exists(p):
            font_path = p
            break

    if font_path:
        font_manager.fontManager.addfont(font_path)
        prop = font_manager.FontProperties(fname=font_path)
        font_name = prop.get_name()
        plt.rcParams['font.family'] = font_name
        print(f"[eval] 使用字体: {font_name} (path={font_path})")
    else:
        # 回退到 sans-serif
        plt.rcParams['font.family'] = 'sans-serif'
        print("[eval] 警告: 未找到 WenQuanYi字体, 使用 sans-serif")


# ======================== 推理函数 ========================
@torch.no_grad()
def inference(model: nn.Module,
              dataloader: DataLoader,
              device: torch.device) -> Tuple[np.ndarray, np.ndarray]:
    """在 DataLoader 上执行推理, 返回所有预测和标签。

    Args:
        model: 已加载权重的模型
        dataloader: 测试 DataLoader
        device: CUDA/CPU 设备

    Returns:
        (all_preds, all_labels) — numpy 数组
    """
    model.eval()
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

        preds = torch.argmax(logits, dim=-1)
        all_preds.extend(preds.cpu().tolist())
        all_labels.extend(labels.cpu().tolist())

    return np.array(all_preds), np.array(all_labels)


# ======================== 混淆矩阵可视化 ========================
def plot_confusion_matrix(y_true: np.ndarray,
                          y_pred: np.ndarray,
                          idx2label: Dict[int, str],
                          save_path: str,
                          normalize: bool = True):
    """绘制并保存归一化混淆矩阵。

    Args:
        y_true: 真实标签
        y_pred: 预测标签
        idx2label: 索引→类别名称映射
        save_path: 图片保存路径
        normalize: 是否按行归一化显示百分比
    """
    setup_chinese_font()

    num_classes = len(idx2label)
    labels = [idx2label[i] for i in range(num_classes)]

    cm = sklearn_cm(y_true, y_pred, labels=list(range(num_classes)))

    if normalize:
        cm_normalized = cm.astype('float') / cm.sum(axis=1, keepdims=True)
        cm_normalized = np.nan_to_num(cm_normalized, nan=0.0)
    else:
        cm_normalized = cm

    fig, ax = plt.subplots(figsize=(14, 12))

    # 使用 imshow 绘制热力图
    im = ax.imshow(cm_normalized, cmap='Blues', aspect='auto', vmin=0, vmax=1.0)

    # 在单元格中添加文本标注
    thresh = 0.5
    for i in range(num_classes):
        for j in range(num_classes):
            if cm_normalized[i, j] > 0.01:
                ax.text(
                    j, i,
                    f'{cm_normalized[i, j]:.2f}',
                    ha='center', va='center',
                    fontsize=7,
                    color='white' if cm_normalized[i, j] > thresh else 'black',
                )

    # 坐标轴设置
    ax.set_xticks(range(num_classes))
    ax.set_yticks(range(num_classes))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel('预测类别', fontsize=12)
    ax.set_ylabel('真实类别', fontsize=12)
    ax.set_title('中文短新闻主题分类 — 归一化混淆矩阵', fontsize=14, fontweight='bold')

    # 颜色条
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('归一化比例', fontsize=10)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"[eval] 混淆矩阵已保存: {save_path}")


# ======================== 损失曲线可视化 (4 张独立图) ========================
_COLORS = {
    'bilstm': ('#2196F3', '#64B5F6'),       # 蓝色系: 训练/验证
    'transformer': ('#FF5722', '#FF8A65'),   # 橙红色系: 训练/验证
}


def _make_figure(title: str, xlabel: str = 'Epoch', ylabel: str = '',
                 figsize: Tuple[int, int] = (10, 7)) -> Tuple[plt.Figure, plt.Axes]:
    """创建独立的 matplotlib 图窗。"""
    setup_chinese_font()
    fig, ax = plt.subplots(figsize=figsize)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(xlabel, fontsize=12)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, alpha=0.3)
    return fig, ax


def plot_loss_curves(history_dicts: Dict[str, Dict], prefix: str = "img/loss_curves"):
    """绘制4张独立训练过程图 (不再合成单张 2×2)。

    生成文件:
        {prefix}_train_loss.png  — 训练 + 验证损失
        {prefix}_accuracy.png    — 训练 + 验证准确率
        {prefix}_val_loss.png    — 验证损失对比
        {prefix}_val_f1.png      — 验证 Macro-F1 对比

    Args:
        history_dicts: {模型标识: 训练历史 dict}
        prefix: 输出路径前缀
    """
    os.makedirs(os.path.dirname(prefix), exist_ok=True)

    # ---- 图 1: 训练损失 & 验证损失 ----
    fig, ax = _make_figure('训练与验证损失曲线', ylabel='交叉熵损失')
    for model_name, history in history_dicts.items():
        c_train, c_val = _COLORS.get(model_name, ('#333', '#999'))
        epochs = range(1, len(history['train_loss']) + 1)
        ax.plot(epochs, history['train_loss'], '-o', color=c_train,
                markersize=4, linewidth=2, label=f'{model_name} 训练')
        ax.plot(epochs, history['val_loss'], '-s', color=c_val,
                markersize=4, linewidth=2, label=f'{model_name} 验证')
    ax.legend(fontsize=10)
    path1 = f"{prefix}_loss.png"
    plt.tight_layout(); plt.savefig(path1, dpi=150, bbox_inches='tight'); plt.close()
    print(f"[eval] 已保存: {path1}")

    # ---- 图 2: 训练/验证 Accuracy ----
    fig, ax = _make_figure('训练与验证准确率曲线', ylabel='Accuracy')
    for model_name, history in history_dicts.items():
        c_train, c_val = _COLORS.get(model_name, ('#333', '#999'))
        epochs = range(1, len(history['train_acc']) + 1)
        ax.plot(epochs, history['train_acc'], '-o', color=c_train,
                markersize=4, linewidth=2, label=f'{model_name} 训练')
        ax.plot(epochs, history['val_acc'], '-s', color=c_val,
                markersize=4, linewidth=2, label=f'{model_name} 验证')
    ax.legend(fontsize=10)
    path2 = f"{prefix}_accuracy.png"
    plt.tight_layout(); plt.savefig(path2, dpi=150, bbox_inches='tight'); plt.close()
    print(f"[eval] 已保存: {path2}")

    # ---- 图 3: 验证损失对比 ----
    fig, ax = _make_figure('验证损失对比', ylabel='交叉熵损失')
    for model_name, history in history_dicts.items():
        c_train, _ = _COLORS.get(model_name, ('#333', '#999'))
        epochs = range(1, len(history['val_loss']) + 1)
        ax.plot(epochs, history['val_loss'], '-o', color=c_train,
                markersize=5, linewidth=2.5, label=model_name)
    ax.legend(fontsize=11)
    path3 = f"{prefix}_val_loss.png"
    plt.tight_layout(); plt.savefig(path3, dpi=150, bbox_inches='tight'); plt.close()
    print(f"[eval] 已保存: {path3}")

    # ---- 图 4: 验证 Macro-F1 对比 ----
    fig, ax = _make_figure('验证 Macro-F1 对比', ylabel='Macro-F1')
    for model_name, history in history_dicts.items():
        _, c_val = _COLORS.get(model_name, ('#333', '#999'))
        epochs = range(1, len(history['val_f1']) + 1)
        ax.plot(epochs, history['val_f1'], '-s', color=c_val,
                markersize=5, linewidth=2.5, label=model_name)
    ax.legend(fontsize=11)
    path4 = f"{prefix}_val_f1.png"
    plt.tight_layout(); plt.savefig(path4, dpi=150, bbox_inches='tight'); plt.close()
    print(f"[eval] 已保存: {path4}")


# ======================== 错误分析 ========================
def top_error_analysis(y_true: np.ndarray,
                       y_pred: np.ndarray,
                       idx2label: Dict[int, str],
                       top_k: int = 5):
    """分析最容易预测错误的类别对。

    Args:
        y_true: 真实标签
        y_pred: 预测标签
        idx2label: 索引→类别名称映射
        top_k: 返回前 k 个混淆对

    Returns:
        List[(true_label, pred_label, count)] 混淆对列表
    """
    # 找出所有错误预测的索引
    error_mask = (y_true != y_pred)
    error_true = y_true[error_mask]
    error_pred = y_pred[error_mask]

    # 统计混淆对
    confusion_pairs = {}
    for t, p in zip(error_true, error_pred):
        pair = (int(t), int(p))
        confusion_pairs[pair] = confusion_pairs.get(pair, 0) + 1

    # 排序并返回 top_k
    sorted_pairs = sorted(confusion_pairs.items(), key=lambda x: -x[1])

    results = []
    for (t, p), count in sorted_pairs[:top_k]:
        results.append({
            'true_label': idx2label[t],
            'pred_label': idx2label[p],
            'count': count,
            'true_idx': t,
            'pred_idx': p,
        })

    return results


# ======================== 主评估流水线 ========================
def evaluate(args: argparse.Namespace):
    """加载多个模型, 在测试集上评估, 生成所有可视化图表。"""

    # ---- 0. 设备 ----
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"[eval] 运行设备: {device}")

    # ---- 1. 构建 DataLoader ----
    print("[eval] 构建数据流水线...")
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

    idx2label = metadata['idx2label']
    num_classes = metadata['num_classes']

    # ---- 2. 加载多个模型并评估 ----
    os.makedirs('img', exist_ok=True)

    history_dicts = {}
    results_table = []

    model_configs = [
        {
            'name': 'BiLSTM+Attention',
            'type': 'bilstm',
            'ckpt': 'models/bilstm_best.pt',
            'history': 'models/bilstm_history.json',
        },
        {
            'name': 'Transformer',
            'type': 'transformer',
            'ckpt': 'models/transformer_best.pt',
            'history': 'models/transformer_history.json',
        },
    ]

    for config in model_configs:
        model_name = config['name']
        print(f"\n{'='*60}")
        print(f"评估模型: {model_name}")
        print(f"{'='*60}")

        # 检查模型文件是否存在
        if not os.path.exists(config['ckpt']):
            print(f"[eval] 警告: 未找到模型权重 {config['ckpt']}, 跳过。")
            continue

        # 创建模型并加载权重
        model = create_model(
            model_type=config['type'],
            vocab_size=metadata['vocab_size'],
            num_classes=num_classes,
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
        model.load_state_dict(torch.load(config['ckpt'], map_location=device))
        model = model.to(device)

        # 推理
        y_pred, y_true = inference(model, test_loader, device)

        # 计算指标
        acc = accuracy_score(y_true, y_pred)
        macro_f1 = f1_score(y_true, y_pred, average='macro')
        precision, recall, f1_per_class, _ = precision_recall_fscore_support(
            y_true, y_pred, labels=list(range(num_classes)), zero_division=0
        )

        # 打印结果
        print(f"  Accuracy:  {acc:.4f}")
        print(f"  Macro-F1:  {macro_f1:.4f}")

        print(f"\n  {'类别':<20s} {'Precision':>10s} {'Recall':>10s} {'F1':>10s}")
        print(f"  {'-'*50}")
        for i in range(num_classes):
            print(f"  {idx2label[i]:<20s} {precision[i]:>10.4f} {recall[i]:>10.4f} {f1_per_class[i]:>10.4f}")

        # 保存混淆矩阵 (每个模型单独一张)
        cm_path = f"img/confusion_matrix_{config['type']}.png"
        plot_confusion_matrix(y_true, y_pred, idx2label, cm_path)

        # 错误分析
        errors = top_error_analysis(y_true, y_pred, idx2label, top_k=5)
        print(f"\n  Top-5 易混淆类别对:")
        for i, e in enumerate(errors):
            print(f"    {i+1}. '{e['true_label']}' → '{e['pred_label']}': {e['count']} 次")

        # 记录结果
        results_table.append({
            'name': model_name,
            'acc': acc,
            'macro_f1': macro_f1,
            'precision_per_class': precision.tolist(),
            'recall_per_class': recall.tolist(),
            'f1_per_class': f1_per_class.tolist(),
            'top_errors': errors,
        })

        # 加载训练历史
        if os.path.exists(config['history']):
            with open(config['history'], 'r', encoding='utf-8') as f:
                history = json.load(f)
            history_dicts[config['type']] = history

    # ---- 3. 绘制损失曲线 (4 张独立图) ----
    if history_dicts:
        plot_loss_curves(history_dicts, prefix="img/loss_curves")

    # ---- 4. 保存评估结果 JSON ----
    results_path = "models/eval_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results_table, f, indent=2, ensure_ascii=False)
    print(f"\n[eval] 评估结果已保存: {results_path}")

    # ---- 5. 总结表格 ----
    print(f"\n{'='*60}")
    print(f"最终对比总结")
    print(f"{'='*60}")
    print(f"  {'模型':<20s} {'Accuracy':>10s} {'Macro-F1':>10s}")
    print(f"  {'-'*40}")
    for r in results_table:
        print(f"  {r['name']:<20s} {r['acc']:>10.4f} {r['macro_f1']:>10.4f}")

    return results_table


# ======================== 命令行入口 ========================
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="中文短新闻主题分类 — 评估脚本"
    )
    parser.add_argument('--train_file', type=str, default='data/train.json')
    parser.add_argument('--dev_file', type=str, default='data/dev.json')
    parser.add_argument('--labels_file', type=str, default='data/labels.json')

    # 模型参数 (与训练保持一致)
    parser.add_argument('--embed_dim', type=int, default=256)
    parser.add_argument('--hidden_dim', type=int, default=128)
    parser.add_argument('--attn_dim', type=int, default=128)
    parser.add_argument('--num_layers', type=int, default=2)
    parser.add_argument('--d_model', type=int, default=256)
    parser.add_argument('--nhead', type=int, default=8)
    parser.add_argument('--num_encoder_layers', type=int, default=4)
    parser.add_argument('--dim_feedforward', type=int, default=1024)
    parser.add_argument('--dropout', type=float, default=0.5)

    parser.add_argument('--batch_size', type=int, default=64)
    parser.add_argument('--coverage', type=float, default=0.95)
    parser.add_argument('--min_freq', type=int, default=2)
    parser.add_argument('--max_len', type=int, default=None)
    parser.add_argument('--num_workers', type=int, default=4)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    evaluate(args)
