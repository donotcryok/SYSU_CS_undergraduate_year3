"""
独立模型评估模块
----------------
加载指定 checkpoint 并在 CIFAR-10 测试集上计算:
  - Top-1 Accuracy
  - Top-5 Accuracy
  - 每类 Precision / Recall / F1
"""

import os
import argparse
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, accuracy_score

from data.dataset import load_cifar10_numpy, CIFAR10Test
from models.wrn import build_wrn28_2


def evaluate(model: torch.nn.Module, loader: DataLoader,
             device: torch.device) -> dict:
    """在给定 DataLoader 上评估模型, 返回指标字典."""
    model.eval()
    all_preds, all_labels = [], []

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device, non_blocking=True)
            out = model(images)
            # semilearn WRN 的 forward 返回 dict {'logits': ...}，自研返回 tensor
            if isinstance(out, dict):
                logits = out['logits']
            else:
                logits = out
            preds = logits.argmax(dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.numpy())

    acc_top1 = accuracy_score(all_labels, all_preds) * 100.0
    report = classification_report(
        all_labels, all_preds, digits=4, output_dict=True, zero_division=0
    )

    return {
        'top1_acc': acc_top1,
        'per_class': report,
    }


def main():
    parser = argparse.ArgumentParser(description='CIFAR-10 模型评估')
    parser.add_argument('--checkpoint', type=str, required=True,
                        help='模型 checkpoint 路径')
    parser.add_argument('--data_root', type=str, default='.',
                        help='项目根目录')
    parser.add_argument('--batch_size', type=int, default=128,
                        help='评估 batch size')
    parser.add_argument('--num_workers', type=int, default=4)
    parser.add_argument('--device', type=str, default='cuda')
    args = parser.parse_args()

    device = torch.device(args.device if torch.cuda.is_available() else 'cpu')

    # ── 数据 ──
    _, _, test_images, test_labels = load_cifar10_numpy(args.data_root)
    test_set = CIFAR10Test(test_images, test_labels)
    test_loader = DataLoader(test_set, batch_size=args.batch_size,
                             shuffle=False, num_workers=args.num_workers,
                             pin_memory=True)

    ckpt = torch.load(args.checkpoint, map_location=device, weights_only=False)

    # 兼容两种 checkpoint 格式：
    #   - 自研 train.py:     'model_state_dict' → 使用自研 models/wrn.py
    #   - semilearn baseline: 'model'            → 使用 semilearn 内置 WRN 构建器
    if 'model_state_dict' in ckpt:
        state_dict = ckpt['model_state_dict']
        model = build_wrn28_2(num_classes=10, dropout=0.0)
        model.load_state_dict(state_dict, strict=True)
    elif 'model' in ckpt:
        # semilearn checkpoint 同时含 'model' (原始权重) 和 'ema_model' (EMA 权重)
        # 优先使用 EMA 模型（与 semilearn 内部评估一致，准确率更高）
        if 'ema_model' in ckpt:
            state_dict = ckpt['ema_model']
            print('[test] Using EMA model weights (matches semilearn eval accuracy)')
        else:
            state_dict = ckpt['model']
        # semilearn 的 DataParallel 包装会在 key 前加 'module.' 前缀，需要剥离
        if any(k.startswith('module.') for k in state_dict.keys()):
            from collections import OrderedDict
            new_state = OrderedDict()
            for k, v in state_dict.items():
                new_state[k[len('module.'):] if k.startswith('module.') else k] = v
            state_dict = new_state
        # 使用 semilearn 内置 WRN 构建器 (与训练时架构一致)
        from semilearn.nets.wrn import wrn_28_2
        model = wrn_28_2(num_classes=10, drop_rate=0.0)
        model.load_state_dict(state_dict, strict=True)
    else:
        raise KeyError(f"Unrecognized checkpoint format. Keys: {list(ckpt.keys())}")

    model.to(device)

    # ── 评估 ──
    metrics = evaluate(model, test_loader, device)
    print(f'\n{"="*50}')
    print(f'  CIFAR-10 Test Results')
    print(f'{"="*50}')
    print(f'  Top-1 Accuracy : {metrics["top1_acc"]:.2f}%')
    print(f'{"="*50}\n')
    print('Per-class metrics:')
    report = metrics['per_class']
    header = f'{"Class":>6s}  {"Precision":>10s}  {"Recall":>8s}  {"F1":>8s}  {"Support":>8s}'
    print(header)
    print('-' * len(header))
    for cls in sorted([k for k in report.keys() if k.isdigit()],
                      key=lambda x: int(x)):
        m = report[cls]
        print(f'{cls:>6s}  {m["precision"]:>10.4f}  {m["recall"]:>8.4f}  '
              f'{m["f1-score"]:>8.4f}  {m["support"]:>8.0f}')
    print()


if __name__ == '__main__':
    main()
