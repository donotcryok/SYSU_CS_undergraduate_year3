"""
绘图脚本 —— 自研 vs Baseline 对比曲线
========================================
从 src/runs/{exp_name}/history_log.csv 读取训练日志,
生成 Loss / Accuracy 对比曲线图, 保存至 img/ 目录.
支持两阶段使用:
  1) 训练中或训练后手动调用
  2) 在 train.py 末尾自动调用 (可选)
"""

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# 中文字体支持 (如果可用)
try:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
except Exception:
    pass


def load_history(exp_name: str, base_dir: str = None) -> pd.DataFrame:
    """加载指定实验的 CSV 历史记录."""
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, 'runs', exp_name, 'history_log.csv')
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f'CSV not found: {csv_path}')
    df = pd.read_csv(csv_path)
    return df


def plot_comparison(df_ours: pd.DataFrame, df_baseline: pd.DataFrame,
                    save_path: str):
    """绘制四合一对比图: Loss + Mask Ratio + Accuracy."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # ── Subplot 1: Supervised Loss ──
    ax = axes[0][0]
    if 'L_s' in df_ours.columns:
        ax.plot(df_ours['step'], df_ours['L_s'], label='Ours L_s', alpha=0.8, linewidth=1.2)
    if 'L_s' in df_baseline.columns:
        ax.plot(df_baseline['step'], df_baseline['L_s'], label='Baseline L_s', alpha=0.8, linewidth=1.2)
    ax.set_xlabel('Step')
    ax.set_ylabel('Supervised Loss')
    ax.set_title('Supervised Loss (L_s)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # ── Subplot 2: Unsupervised Loss ──
    ax = axes[0][1]
    if 'L_u' in df_ours.columns:
        ax.plot(df_ours['step'], df_ours['L_u'], label='Ours L_u', alpha=0.8, linewidth=1.2)
    if 'L_u' in df_baseline.columns:
        ax.plot(df_baseline['step'], df_baseline['L_u'], label='Baseline L_u', alpha=0.8, linewidth=1.2)
    ax.set_xlabel('Step')
    ax.set_ylabel('Unsupervised Loss')
    ax.set_title('Unsupervised Loss (L_u)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # ── Subplot 3: Mask Ratio ──
    ax = axes[1][0]
    if 'mask_ratio' in df_ours.columns:
        ax.plot(df_ours['step'], df_ours['mask_ratio'], label='Ours mask_ratio', alpha=0.8, linewidth=1.2)
    if 'mask_ratio' in df_baseline.columns:
        ax.plot(df_baseline['step'], df_baseline['mask_ratio'], label='Baseline mask_ratio', alpha=0.8, linewidth=1.2)
    ax.set_xlabel('Step')
    ax.set_ylabel('Mask Ratio')
    ax.set_title('Pseudo-label Mask Ratio')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 1.05)

    # ── Subplot 4: Test Accuracy ──
    ax = axes[1][1]
    if 'test_acc' in df_ours.columns:
        ax.plot(df_ours['step'], df_ours['test_acc'], label='Ours Accuracy', alpha=0.9, linewidth=1.5, marker='o', markersize=2)
    if 'test_acc' in df_baseline.columns:
        ax.plot(df_baseline['step'], df_baseline['test_acc'], label='Baseline Accuracy', alpha=0.9, linewidth=1.5, marker='s', markersize=2)
    ax.set_xlabel('Step')
    ax.set_ylabel('Test Accuracy (%)')
    ax.set_title('CIFAR-10 Test Accuracy')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.suptitle('FixMatch: Ours vs USB Baseline (CIFAR-10, 40 labels/class)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'[Plot] Comparison figure saved to: {save_path}')


def plot_single(df: pd.DataFrame, exp_name: str, save_path: str):
    """单个实验的三合一监控图."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # Loss
    ax = axes[0]
    if 'L_s' in df.columns:
        ax.plot(df['step'], df['L_s'], label='L_s')
    if 'L_u' in df.columns:
        ax.plot(df['step'], df['L_u'], label='L_u')
    ax.set_xlabel('Step'); ax.set_ylabel('Loss')
    ax.set_title(f'{exp_name} - Loss'); ax.legend(); ax.grid(True, alpha=0.3)

    # Mask Ratio
    ax = axes[1]
    if 'mask_ratio' in df.columns:
        ax.plot(df['step'], df['mask_ratio'], color='green')
        ax.set_ylim(0, 1.05)
    ax.set_xlabel('Step'); ax.set_ylabel('Mask Ratio')
    ax.set_title(f'{exp_name} - Mask Ratio'); ax.grid(True, alpha=0.3)

    # Accuracy
    ax = axes[2]
    if 'test_acc' in df.columns:
        ax.plot(df['step'], df['test_acc'], color='red', marker='o', markersize=3)
    ax.set_xlabel('Step'); ax.set_ylabel('Test Acc (%)')
    ax.set_title(f'{exp_name} - Test Accuracy'); ax.grid(True, alpha=0.3)

    plt.suptitle(f'Training Monitor: {exp_name}', fontsize=14, fontweight='bold')
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'[Plot] Single figure saved to: {save_path}')


def main():
    import argparse
    parser = argparse.ArgumentParser(description='FixMatch 训练曲线绘制')
    parser.add_argument('--ours', type=str, default='fixmatch_ours',
                        help='自研实验名称')
    parser.add_argument('--baseline', type=str, default='fixmatch_baseline',
                        help='Baseline 实验名称')
    parser.add_argument('--mode', type=str, default='comparison',
                        choices=['comparison', 'single', 'both'],
                        help='绘图模式')
    parser.add_argument('--output_dir', type=str, default=None,
                        help='输出目录 (默认 img/)')
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    if args.output_dir is None:
        output_dir = os.path.join(os.path.dirname(base_dir), 'img')
    else:
        output_dir = args.output_dir

    try:
        if args.mode in ('comparison', 'both'):
            df_ours = load_history(args.ours)
            df_baseline = load_history(args.baseline)
            plot_comparison(df_ours, df_baseline,
                            os.path.join(output_dir, 'comparison.png'))

        if args.mode in ('single', 'both'):
            df_ours = load_history(args.ours)
            plot_single(df_ours, args.ours,
                        os.path.join(output_dir, f'{args.ours}.png'))

        if args.mode == 'both':
            df_baseline = load_history(args.baseline)
            plot_single(df_baseline, args.baseline,
                        os.path.join(output_dir, f'{args.baseline}.png'))

    except FileNotFoundError as e:
        print(f'[WARN] {e}')
        print('请先运行训练脚本生成 history_log.csv, 然后再执行绘图。')


if __name__ == '__main__':
    main()
