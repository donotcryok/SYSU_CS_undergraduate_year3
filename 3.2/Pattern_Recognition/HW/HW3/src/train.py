"""
FixMatch 自研实现 —— 核心训练脚本
==================================
- 每隔 10 步流式打印训练日志
- 每隔 500 步测试集评估 + CSV 追加
- 支持断点续训 (--resume)
- AMP 混合精度全程启用
"""

import os
import sys
import csv
import time
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.cuda.amp import GradScaler, autocast
import numpy as np

# 将 src/ 加入 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from options.config import parse_args
from data.dataset import build_dataloaders, CIFAR10Test
from models.wrn import build_wrn28_2


# ── 工具函数 ─────────────────────────────────────────────────────────

def set_seed(seed: int):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def cosine_schedule(step: int, total_steps: int, lr_base: float,
                    lr_min: float = 0.0) -> float:
    """Cosine annealing: 从 lr_base 余弦衰减至 lr_min."""
    return lr_min + 0.5 * (lr_base - lr_min) * (1.0 + math.cos(math.pi * step / total_steps))


def save_checkpoint(exp_dir: str, model: nn.Module, optimizer: optim.Optimizer,
                    scaler: GradScaler, step: int, best_acc: float,
                    args, filename: str = 'checkpoint.pth'):
    """保存训练状态."""
    os.makedirs(exp_dir, exist_ok=True)
    path = os.path.join(exp_dir, filename)
    torch.save({
        'step': step,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'scaler_state_dict': scaler.state_dict(),
        'best_acc': best_acc,
        'args': args,
    }, path)
    return path


def load_checkpoint(path: str, model: nn.Module, optimizer: optim.Optimizer,
                    scaler: GradScaler, device: torch.device):
    """加载训练状态, 返回 (step, best_acc)."""
    ckpt = torch.load(path, map_location=device, weights_only=False)
    model.load_state_dict(ckpt['model_state_dict'])
    optimizer.load_state_dict(ckpt['optimizer_state_dict'])
    scaler.load_state_dict(ckpt['scaler_state_dict'])
    return ckpt['step'], ckpt['best_acc']


@torch.no_grad()
def evaluate_test(model: nn.Module, test_loader, device: torch.device) -> float:
    """快速评估 Top-1 Accuracy."""
    model.eval()
    correct, total = 0, 0
    for images, labels in test_loader:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)
        logits = model(images)
        correct += (logits.argmax(1) == labels).sum().item()
        total += labels.size(0)
    model.train()
    return 100.0 * correct / total


# ── 主训练函数 ───────────────────────────────────────────────────────

def main():
    args = parse_args()
    set_seed(args.seed)

    device = torch.device(args.device if torch.cuda.is_available() else 'cpu')
    print(f'[FixMatch Ours] Device: {device}')
    if device.type == 'cuda':
        print(f'[FixMatch Ours] GPU: {torch.cuda.get_device_name(0)}')
        print(f'[FixMatch Ours] CUDA capability: {torch.cuda.get_device_capability(0)}')

    # ── DataLoaders ──
    loader_labeled, loader_unlabeled, loader_test = build_dataloaders(
        data_root=args.data_root,
        batch_size=args.batch_size,
        mu=args.mu,
        num_labeled=args.num_labeled,
        num_workers=args.num_workers,
        seed=args.seed,
    )

    # ── 模型 / 优化器 / 混合精度 ──
    model = build_wrn28_2(num_classes=args.num_classes, dropout=0.0)
    model.to(device)

    optimizer = optim.SGD(
        model.parameters(), lr=args.lr,
        momentum=args.momentum, weight_decay=args.weight_decay,
        nesterov=args.nesterov,
    )
    scaler = GradScaler(enabled=args.amp)

    # ── 断点续训 ──
    start_step = 0
    best_acc = 0.0
    ckpt_path = os.path.join(args.exp_dir, 'checkpoint.pth')
    if args.resume and os.path.exists(ckpt_path):
        start_step, best_acc = load_checkpoint(
            ckpt_path, model, optimizer, scaler, device
        )
        print(f'[FixMatch Ours] Resumed from step {start_step}, best_acc={best_acc:.2f}%')

    # ── CSV Logger ──
    csv_path = os.path.join(args.exp_dir, 'history_log.csv')
    os.makedirs(args.exp_dir, exist_ok=True)
    csv_file = open(csv_path, 'a', newline='')
    csv_writer = csv.writer(csv_file)
    if start_step == 0:
        csv_writer.writerow(['step', 'lr', 'L_s', 'L_u', 'L_total', 'mask_ratio', 'test_acc', 'epoch_secs'])

    # ── 训练循环 ──
    labeled_iter = iter(loader_labeled)
    unlabeled_iter = iter(loader_unlabeled)
    criterion = nn.CrossEntropyLoss()

    model.train()
    t0 = time.time()
    step = start_step

    while step < args.total_steps:
        # 取下一批数据 (循环迭代器)
        try:
            x_l, y_l = next(labeled_iter)
        except StopIteration:
            labeled_iter = iter(loader_labeled)
            x_l, y_l = next(labeled_iter)
        try:
            (x_u_weak, x_u_strong) = next(unlabeled_iter)
        except StopIteration:
            unlabeled_iter = iter(loader_unlabeled)
            (x_u_weak, x_u_strong) = next(unlabeled_iter)

        x_l = x_l.to(device, non_blocking=True)
        y_l = y_l.to(device, non_blocking=True)
        x_u_weak = x_u_weak.to(device, non_blocking=True)
        x_u_strong = x_u_strong.to(device, non_blocking=True)

        # ── 学习率更新 ──
        lr_now = cosine_schedule(step, args.total_steps, args.lr)
        for pg in optimizer.param_groups:
            pg['lr'] = lr_now

        optimizer.zero_grad()

        with autocast(enabled=args.amp):
            # 有监督损失
            logits_l = model(x_l)
            L_s = criterion(logits_l, y_l)

            # 无监督损失 (伪标签 + 置信度阈值)
            logits_u_weak = model(x_u_weak)
            probs = torch.softmax(logits_u_weak, dim=1)
            max_probs, pseudo_labels = probs.max(dim=1)
            mask = (max_probs >= args.conf_threshold)

            logits_u_strong = model(x_u_strong)
            L_u = (F.cross_entropy(logits_u_strong, pseudo_labels, reduction='none')
                   * mask.float()).mean() if mask.any() else torch.tensor(0.0, device=device)

            total_loss = L_s + args.lambda_u * L_u

        scaler.scale(total_loss).backward()
        scaler.step(optimizer)
        scaler.update()

        mask_ratio = mask.float().mean().item()
        step += 1

        # ── 每 10 步流式日志 ──
        if step % args.log_interval == 0:
            elapsed = time.time() - t0
            steps_done = step - start_step
            sps = elapsed / max(steps_done, 1)
            print(f'[Step {step:>5d}/{args.total_steps}] lr={lr_now:.6f} '
                  f'L_s={L_s.item():.4f} L_u={L_u.item():.4f} '
                  f'mask_ratio={mask_ratio:.3f} | {sps:.2f}s/step')

        # ── 每 500 步评估 + 保存 ──
        if step % args.eval_interval == 0 or step == args.total_steps:
            test_acc = evaluate_test(model, loader_test, device)
            best_acc = max(best_acc, test_acc)
            epoch_secs = time.time() - t0
            print(f'{"="*55}')
            print(f'[Eval  Step {step}/{args.total_steps}] '
                  f'Test Acc = {test_acc:.2f}% | Best Acc = {best_acc:.2f}%')
            print(f'{"="*55}')

            csv_writer.writerow([step, lr_now, L_s.item(), L_u.item(),
                                 total_loss.item(), mask_ratio, test_acc,
                                 epoch_secs])
            csv_file.flush()

            save_checkpoint(args.exp_dir, model, optimizer, scaler,
                            step, best_acc, args)

        # 最终一步也做一次保存
        if step == args.total_steps:
            save_checkpoint(args.exp_dir, model, optimizer, scaler,
                            step, best_acc, args, filename='checkpoint_final.pth')
            test_acc = evaluate_test(model, loader_test, device)
            csv_writer.writerow([step, lr_now, 0.0, 0.0, 0.0, 0.0, test_acc, time.time() - t0])
            csv_file.flush()

    csv_file.close()
    print(f'\n[FixMatch Ours] Training Done. Best Acc = {best_acc:.2f}%')


if __name__ == '__main__':
    main()
