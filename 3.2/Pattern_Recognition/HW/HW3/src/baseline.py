"""
FixMatch Baseline —— USB (semilearn) 对照组训练脚本 (终极接管版)
=====================================================
"""

import os
import sys
import argparse
import torch
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from semilearn import get_dataset, get_data_loader, get_net_builder
from semilearn import get_algorithm, get_config
from semilearn.core.hooks.hook import Hook
import csv
import time as time_module


def sl_set_seed(seed: int):
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def parse_args():
    parser = argparse.ArgumentParser(description='USB FixMatch Baseline')
    parser.add_argument('--exp_name', type=str, default='fixmatch_baseline_40')
    parser.add_argument('--data_root', type=str, default='.')
    parser.add_argument('--num_labeled', type=int, default=40)
    parser.add_argument('--total_steps', type=int, default=65536)
    parser.add_argument('--batch_size', type=int, default=64)
    parser.add_argument('--mu', type=int, default=7)
    parser.add_argument('--lr', type=float, default=0.03)
    parser.add_argument('--weight_decay', type=float, default=5e-4)
    parser.add_argument('--momentum', type=float, default=0.9)
    parser.add_argument('--seed', type=int, default=123)
    parser.add_argument('--num_workers', type=int, default=4)
    parser.add_argument('--amp', action='store_true', default=False,
                        help='启用 AMP 混合精度 (use_amp)')
    parser.add_argument('--resume', action='store_true', default=False,
                        help='从 latest checkpoint 恢复训练')
    return parser.parse_args()


# ── 自定义 CSV 日志 Hook：在每次 eval 时将指标写入 history_log.csv ──
class CSVLogHook(Hook):
    def __init__(self, save_dir):
        self.save_dir = save_dir
        self.csv_path = os.path.join(save_dir, 'history_log.csv')
        self.start_time = None
        os.makedirs(save_dir, exist_ok=True)
        # 仅在文件不存在时写入表头（兼容全新训练和断点续训）
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['step', 'lr', 'L_s', 'L_u', 'L_total',
                                 'mask_ratio', 'test_acc', 'epoch_secs'])

    def before_run(self, algorithm):
        self.start_time = time_module.time()

    def after_train_step(self, algorithm):
        if self.every_n_iters(algorithm, algorithm.num_eval_iter):
            lt = getattr(algorithm, 'log_dict', None) or {}
            step = algorithm.it + 1  # semilearn: it 尚未递增, +1 为实际步数
            elapsed = time_module.time() - self.start_time if self.start_time else 0.0
            row = [
                step,
                lt.get('lr', 0.0),
                lt.get('train/sup_loss', 0.0),
                lt.get('train/unsup_loss', 0.0),
                lt.get('train/total_loss', 0.0),
                lt.get('train/util_ratio', 0.0),
                lt.get('eval/top-1-acc', 0.0) * 100.0,  # semilearn 存的是 0~1
                elapsed,
            ]
            with open(self.csv_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)

    def after_run(self, algorithm):
        # 训练结束后追加最终评估行
        # 优先用 log_dict（正常训练流程），回退到 algorithm 对象（提前退出 / resume 即完成）
        lt = getattr(algorithm, 'log_dict', None) or {}
        step = algorithm.it + 1
        elapsed = time_module.time() - self.start_time if self.start_time else 0.0

        if lt:
            test_acc = lt.get('eval/top-1-acc', 0.0) * 100.0
        else:
            test_acc = algorithm.best_eval_acc * 100.0  # 0~1 → %

        row = [
            step,
            lt.get('lr', 0.0) if lt else 0.0,
            lt.get('train/sup_loss', 0.0) if lt else 0.0,
            lt.get('train/unsup_loss', 0.0) if lt else 0.0,
            lt.get('train/total_loss', 0.0) if lt else 0.0,
            lt.get('train/util_ratio', 0.0) if lt else 0.0,
            test_acc,
            elapsed,
        ]
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)


def main():
    args = parse_args()

    config = {
        'algorithm': 'fixmatch',
        'dataset': 'cifar10',
        'data_dir': os.path.join(args.data_root, 'data'),
        'net': 'wrn_28_2',
        'net_from_name': False,
        'num_classes': 10,
        'num_labels': args.num_labeled * 10,
        'epoch': 1,
        'num_train_iter': args.total_steps,
        'num_eval_iter': 500,
        'num_log_iter': 10,
        'num_warmup_iter': 0,
        'optim': 'SGD',
        'lr': args.lr,
        'momentum': args.momentum,
        'weight_decay': args.weight_decay,
        'nesterov': True,
        'layer_decay': 1.0,
        'batch_size': args.batch_size,
        'uratio': args.mu,
        'eval_batch_size': 128,
        'T': 0.5,
        'p_cutoff': 0.95,
        'ulb_loss_ratio': 1.0,
        'hard_label': True,
        'use_cat': False,
        'use_amp': args.amp,
        'clip_grad': 0,
        'ema_m': 0.999,
        'distributed': False,
        'gpu': 0,
        'rank': 0,
        'world_size': 1,
        'multiprocessing_distributed': False,
        'dist_url': 'tcp://127.0.0.1:10001',
        'dist_backend': 'nccl',
        'num_workers': args.num_workers,
        'train_sampler': 'RandomSampler',
        'seed': args.seed,
        'save_dir': os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'runs', args.exp_name),
        'save_name': '',
        'resume': args.resume,
        'overwrite': not args.resume,
        'use_tensorboard': False,
        'use_pretrain': False,
        'pretrain_path': '',
        'img_size': 32,
        'crop_ratio': 0.95,
        'lb_imb_ratio': 1,
        'ulb_imb_ratio': 1,
        'ulb_num_labels': 50000 - args.num_labeled * 10,
        'imb_algorithm': None,
        'c': '',
        'load_path': '',
    }

    sl_set_seed(args.seed)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f'[USB FixMatch Baseline] Device: {device}')

    config_obj = get_config(config)

    # 强制配置单卡模式
    config_obj.gpu = 0
    config_obj.distributed = False
    config_obj.multiprocessing_distributed = False

    net_builder = get_net_builder(config['net'], config['net_from_name'])

    print(f'[USB FixMatch Baseline] Building USB FixMatch algorithm...')
    algorithm = get_algorithm(config_obj, net_builder=net_builder,
                              tb_log=None, logger=None)

    # =====================================================================
    # 终极防御：在训练开始前，手动强制将所有的模型和优化器状态推送到 GPU！
    # =====================================================================
    print(f'[USB FixMatch Baseline] Forcing models and optimizer states to CUDA...')

    # 1. 强制迁移主干网络
    if hasattr(algorithm, 'model') and algorithm.model is not None:
        algorithm.model.cuda()

    # 2. 强制迁移 EMA 模型 (semilearn 的 ModelEMA 类实际网络存储在 .ema 属性中)
    if hasattr(algorithm, 'ema_model') and algorithm.ema_model is not None:
        if hasattr(algorithm.ema_model, 'ema'):
            algorithm.ema_model.ema.cuda()
        else:
            algorithm.ema_model.cuda()

    # 3. 强制迁移优化器内部状态 (防止优化器此时仍追踪 CPU 张量)
    if hasattr(algorithm, 'optimizer') and algorithm.optimizer is not None:
        for state in algorithm.optimizer.state.values():
            for k, v in state.items():
                if isinstance(v, torch.Tensor):
                    state[k] = v.cuda()
    # =====================================================================

    # ── 断点续训：若 --resume 且 checkpoint 存在，加载状态 ──
    ckpt_file = os.path.join(config['save_dir'], 'latest_model.pth')
    if args.resume and os.path.exists(ckpt_file):
        print(f'[USB FixMatch Baseline] Resuming from {ckpt_file}...')
        algorithm.load_model(ckpt_file)
        # 加载后需重新强制执行 GPU 迁移（load_model 默认 map_location='cpu'）
        print(f'[USB FixMatch Baseline] Re-forcing models and optimizer states to CUDA after resume...')
        if hasattr(algorithm, 'model') and algorithm.model is not None:
            algorithm.model.cuda()
        if hasattr(algorithm, 'ema_model') and algorithm.ema_model is not None:
            if hasattr(algorithm.ema_model, 'ema'):
                algorithm.ema_model.ema.cuda()
            else:
                algorithm.ema_model.cuda()
        if hasattr(algorithm, 'optimizer') and algorithm.optimizer is not None:
            for state in algorithm.optimizer.state.values():
                for k, v in state.items():
                    if isinstance(v, torch.Tensor):
                        state[k] = v.cuda()
        print(f'[USB FixMatch Baseline] Resumed at iteration {algorithm.it}')
    elif args.resume:
        print(f'[USB FixMatch Baseline] --resume specified but checkpoint not found at {ckpt_file}, training from scratch.')
    else:
        print(f'[USB FixMatch Baseline] Training from scratch.')

    # ── 注册 CSV 日志 Hook ──
    csv_hook = CSVLogHook(config['save_dir'])
    algorithm.register_hook(csv_hook, 'CSVLogHook', 'LOWEST')
    print(f'[USB FixMatch Baseline] CSV log: {csv_hook.csv_path}')

    print(f'[USB FixMatch Baseline] Starting training ({args.total_steps} steps)...')
    algorithm.train()
    print(f'[USB FixMatch Baseline] Training completed.')


if __name__ == '__main__':
    main()