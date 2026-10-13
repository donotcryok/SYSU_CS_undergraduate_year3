"""
FixMatch 超参数配置 (argparse)
-------------------------------
所有默认值严格按照项目规范统一设定:
- total_steps = 65536
- batch_size  = 64
- mu          = 7
- lr          = 0.03
- amp         = True
"""

import argparse
import os


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='FixMatch on CIFAR-10 — 自研实现',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # ── 实验标识 ─────────────────────────────────────────────
    parser.add_argument('--exp_name', type=str, default='fixmatch_ours',
                        help='实验名称, 用于创建 runs/{exp_name} 目录')

    # ── 数据 ─────────────────────────────────────────────────
    parser.add_argument('--data_root', type=str, default='.',
                        help='项目根目录 (内含 data/cifar-10-batches-py/)')
    parser.add_argument('--num_labeled', type=int, default=40,
                        help='每类有标签样本数 (40 → 400 total)')

    # ── 模型 ─────────────────────────────────────────────────
    parser.add_argument('--arch', type=str, default='wrn28_2',
                        choices=['wrn28_2'],
                        help='骨干网络架构')
    parser.add_argument('--num_classes', type=int, default=10,
                        help='分类数')

    # ── 训练超参 ─────────────────────────────────────────────
    parser.add_argument('--total_steps', type=int, default=65536,
                        help='总训练步数 (2^16)')
    parser.add_argument('--batch_size', type=int, default=64,
                        help='有标签 batch size')
    parser.add_argument('--mu', type=int, default=7,
                        help='无标签数据采样倍数 (U = batch_size * mu)')
    parser.add_argument('--lr', type=float, default=0.03,
                        help='初始学习率 (SGD)')
    parser.add_argument('--weight_decay', type=float, default=5e-4,
                        help='权重衰减系数')
    parser.add_argument('--momentum', type=float, default=0.9,
                        help='SGD momentum')
    parser.add_argument('--nesterov', action='store_true', default=True,
                        help='SGD Nesterov 动量')

    # ── FixMatch 特有参数 ────────────────────────────────────
    parser.add_argument('--conf_threshold', type=float, default=0.95,
                        help='伪标签置信度阈值 τ')
    parser.add_argument('--lambda_u', type=float, default=1.0,
                        help='无监督损失权重 λ_u')

    # ── 混合精度 & 设备 ──────────────────────────────────────
    parser.add_argument('--amp', action='store_true', default=True,
                        help='启用 Automatic Mixed Precision (AMP)')
    parser.add_argument('--device', type=str, default='cuda',
                        choices=['cuda', 'cpu'],
                        help='训练设备')

    # ── 日志 & 评估 ─────────────────────────────────────────
    parser.add_argument('--log_interval', type=int, default=10,
                        help='终端流式日志打印间隔 (步)')
    parser.add_argument('--eval_interval', type=int, default=500,
                        help='测试集评估间隔 (步)')

    # ── 断点续训 ─────────────────────────────────────────────
    parser.add_argument('--resume', action='store_true', default=False,
                        help='从 checkpoint 恢复训练')

    # ── 分布式 / 线程 ────────────────────────────────────────
    parser.add_argument('--num_workers', type=int, default=4,
                        help='DataLoader 并发线程数')
    parser.add_argument('--seed', type=int, default=42,
                        help='全局随机种子')

    args = parser.parse_args()
    args.exp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'runs', args.exp_name)
    return args
