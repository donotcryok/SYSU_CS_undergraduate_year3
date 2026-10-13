#!/usr/bin/env python3
"""
plot_results.py — 实验七 MPI FFT 性能可视化
路径: scripts/plot_results.py
生成:
  - speedup.png: 加速比 vs 进程数
  - time_vs_N.png: 运行时间 vs 问题规模
  - mflops.png: MFLOPS vs 问题规模
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import csv
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(SCRIPT_DIR)
CSV_PATH = os.path.join(PROJ_DIR, 'logs', 'results.csv')
IMG_DIR = os.path.join(PROJ_DIR, 'img')

os.makedirs(IMG_DIR, exist_ok=True)

# ========== 读取数据 ==========
data = {'mpi': {}, 'mpi_opt': {}}
Ns = set()
Ps = set()

with open(CSV_PATH, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        ver = row['version']
        N = int(row['N'])
        P = int(row['P'])
        t = float(row['time_sec'])
        mf = float(row['mflops'])
        err = float(row['error'])
        if N not in data[ver]:
            data[ver][N] = {}
        data[ver][N][P] = {'time': t, 'mflops': mf, 'error': err}
        Ns.add(N)
        Ps.add(P)

Ns = sorted(Ns)
Ps = sorted(Ps)

# ===== 图1: speedup.png — 加速比 vs P =====
fig, axes = plt.subplots(1, len(Ns), figsize=(5 * len(Ns), 4.5))
if len(Ns) == 1:
    axes = [axes]

colors = {'mpi': '#2196F3', 'mpi_opt': '#FF5722'}
markers = {'mpi': 'o-', 'mpi_opt': 's--'}

for idx, N in enumerate(Ns):
    ax = axes[idx]
    N_label = f'$2^{{{int(np.log2(N))}}}$'

    for ver in ['mpi', 'mpi_opt']:
        T1 = data[ver][N][1]['time']  # P=1 基准
        speedups = []
        for P in Ps:
            TP = data[ver][N][P]['time']
            speedups.append(T1 / TP)
        ax.plot(Ps, speedups, markers[ver], color=colors[ver],
                label=ver.replace('_', ' '), linewidth=2, markersize=8)

    ax.plot(Ps, Ps, 'k--', alpha=0.3, linewidth=1, label='Ideal')
    ax.set_xlabel('Processes (P)', fontsize=12)
    ax.set_ylabel('Speedup $S = T_1 / T_P$', fontsize=12)
    ax.set_title(f'N = {N_label}', fontsize=13)
    ax.set_xticks(Ps)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)

fig.suptitle('MPI FFT Speedup', fontsize=15, fontweight='bold')
fig.tight_layout()
fig.savefig(os.path.join(IMG_DIR, 'speedup.png'), dpi=150, bbox_inches='tight')
plt.close(fig)
print('[OK] speedup.png saved')

# ===== 图2: time_vs_N.png — 运行时间 vs N =====
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

for ax_idx, ver in enumerate(['mpi', 'mpi_opt']):
    ax = axes[ax_idx]
    for P in Ps:
        times = [data[ver][N][P]['time'] for N in Ns]
        ax.loglog(Ns, times, 'o-', label=f'P={P}', linewidth=2, markersize=7)

    ax.set_xlabel('Problem Size N', fontsize=12)
    ax.set_ylabel('Time (seconds)', fontsize=12)
    ax.set_title(ver.replace('_', ' '), fontsize=13)
    ax.grid(True, alpha=0.3, which='both')
    ax.legend(fontsize=9)
    ax.set_xticks(Ns)
    ax.set_xticklabels([f'$2^{{{int(np.log2(n))}}}$' for n in Ns])

fig.suptitle('MPI FFT: Time vs Problem Size', fontsize=15, fontweight='bold')
fig.tight_layout()
fig.savefig(os.path.join(IMG_DIR, 'time_vs_N.png'), dpi=150, bbox_inches='tight')
plt.close(fig)
print('[OK] time_vs_N.png saved')

# ===== 图3: mflops.png — MFLOPS vs N =====
fig, ax = plt.subplots(figsize=(9, 5))
for ver in ['mpi', 'mpi_opt']:
    for P in Ps:
        mfs = [data[ver][N][P]['mflops'] for N in Ns]
        ax.semilogx(Ns, mfs, 'o-',
                    label=f'{ver.replace("_"," ")} P={P}', linewidth=1.5, markersize=6)

ax.set_xlabel('Problem Size N', fontsize=12)
ax.set_ylabel('MFLOPS', fontsize=12)
ax.set_title('MPI FFT: Performance (MFLOPS)', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
ax.legend(fontsize=8, ncol=2)
ax.set_xticks(Ns)
ax.set_xticklabels([f'$2^{{{int(np.log2(n))}}}$' for n in Ns])
fig.tight_layout()
fig.savefig(os.path.join(IMG_DIR, 'mflops.png'), dpi=150, bbox_inches='tight')
plt.close(fig)
print('[OK] mflops.png saved')

print()
print('=== 性能摘要 ===')
print(f'{"Version":<10} {"N":>12} {"P":>4} {"Time(s)":>10} {"MFLOPS":>10} {"Error":>12}')
print('-' * 60)
for ver in ['mpi', 'mpi_opt']:
    for N in Ns:
        for P in Ps:
            d = data[ver][N][P]
            print(f'{ver:<10} {N:>12} {P:>4} {d["time"]:>10.4f} {d["mflops"]:>10.1f} {d["error"]:>12.2e}')

# 加速比摘要
print()
print('=== 加速比摘要 (mpi) ===')
for N in Ns:
    T1 = data['mpi'][N][1]['time']
    print(f'N=2^{int(np.log2(N))}:', end=' ')
    for P in Ps:
        Sp = T1 / data['mpi'][N][P]['time']
        print(f'P={P}:{Sp:.2f}x', end='  ')
    print()

print()
print('=== 加速比摘要 (mpi_opt) ===')
for N in Ns:
    T1 = data['mpi_opt'][N][1]['time']
    print(f'N=2^{int(np.log2(N))}:', end=' ')
    for P in Ps:
        Sp = T1 / data['mpi_opt'][N][P]['time']
        print(f'P={P}:{Sp:.2f}x', end='  ')
    print()
