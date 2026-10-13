#!/usr/bin/env python3
"""从 memory.md 读取已有数据，重新生成图表"""

import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

IMG_DIR = Path(__file__).parent.parent / 'img'
MEMORY_FILE = Path(__file__).parent.parent / 'memory.md'

SIZES = [128, 256, 512, 1024, 2048]
THREADS = [1, 2, 4, 8, 16]
SCHEDULES = ['static', 'dynamic', 'guided']

# 从 memory.md 读取 JSON 数据
with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

json_start = content.index('```json') + len('```json')
json_end = content.index('```', json_start)
metrics = json.loads(content[json_start:json_end])

print(f'Loaded {len(metrics)} data points')

# 1. Speedup comparison
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
for idx, schedule in enumerate(SCHEDULES):
    ax = axes[idx]
    for size in SIZES:
        data = [m for m in metrics if m['schedule'] == schedule and m['size'] == size]
        if not data:
            continue
        data.sort(key=lambda x: x['threads'])
        threads = [m['threads'] for m in data]
        speedups = [m['speedup'] for m in data]
        ax.plot(threads, speedups, marker='o', linewidth=2, label=f'N={size}')
    ax.plot(THREADS, THREADS, 'k--', alpha=0.5, label='Ideal')
    ax.set_xlabel('Threads', fontsize=12)
    ax.set_ylabel('Speedup', fontsize=12)
    ax.set_title(f'{schedule.capitalize()} Schedule', fontsize=13)
    ax.set_xticks(THREADS)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig(IMG_DIR / 'speedup_comparison.pdf', bbox_inches='tight')
plt.savefig(IMG_DIR / 'speedup_comparison.png', dpi=300)
print('Saved: speedup_comparison')

# 2. Efficiency comparison
fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
for idx, schedule in enumerate(SCHEDULES):
    ax = axes[idx]
    for size in SIZES:
        data = [m for m in metrics if m['schedule'] == schedule and m['size'] == size]
        if not data:
            continue
        data.sort(key=lambda x: x['threads'])
        threads = [m['threads'] for m in data]
        efficiencies = [m['efficiency'] for m in data]
        ax.plot(threads, efficiencies, marker='o', linewidth=2, label=f'N={size}')
    ax.axhline(y=1.0, color='k', linestyle='--', alpha=0.5)
    ax.set_xlabel('Threads', fontsize=12)
    ax.set_ylabel('Efficiency (E = S/P)', fontsize=12)
    ax.set_ylim([0, 1.2])
    ax.set_title(f'{schedule.capitalize()} Schedule', fontsize=13)
    ax.set_xticks(THREADS)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig(IMG_DIR / 'efficiency_comparison.pdf', bbox_inches='tight')
plt.savefig(IMG_DIR / 'efficiency_comparison.png', dpi=300)
print('Saved: efficiency_comparison')

# 3. Schedule comparison (8 threads)
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

# GFLOPS comparison
ax = axes[0]
for size in [512, 1024, 2048]:
    data = [m for m in metrics if m['size'] == size and m['threads'] == 8]
    if not data:
        continue
    data.sort(key=lambda x: SCHEDULES.index(x['schedule']))
    schedules = [m['schedule'] for m in data]
    gflops = [m['gflops'] for m in data]
    x = np.arange(len(schedules))
    width = 0.25
    offset = ([512, 1024, 2048].index(size) - 1) * width
    ax.bar(x + offset, gflops, width, label=f'N={size}')
ax.set_xlabel('Schedule', fontsize=12)
ax.set_ylabel('GFLOPS', fontsize=12)
ax.set_title('Schedule Performance (8 Threads)', fontsize=13)
ax.set_xticks(np.arange(len(SCHEDULES)))
ax.set_xticklabels(SCHEDULES)
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# Time comparison
ax = axes[1]
for size in [512, 1024, 2048]:
    data = [m for m in metrics if m['size'] == size and m['threads'] == 8]
    if not data:
        continue
    data.sort(key=lambda x: SCHEDULES.index(x['schedule']))
    schedules = [m['schedule'] for m in data]
    times = [m['time_ms'] for m in data]
    x = np.arange(len(schedules))
    width = 0.25
    offset = ([512, 1024, 2048].index(size) - 1) * width
    ax.bar(x + offset, times, width, label=f'N={size}')
ax.set_xlabel('Schedule', fontsize=12)
ax.set_ylabel('Time (ms)', fontsize=12)
ax.set_title('Schedule Time (8 Threads)', fontsize=13)
ax.set_xticks(np.arange(len(SCHEDULES)))
ax.set_xticklabels(SCHEDULES)
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(IMG_DIR / 'schedule_comparison.pdf', bbox_inches='tight')
plt.savefig(IMG_DIR / 'schedule_comparison.png', dpi=300)
print('Saved: schedule_comparison')

# 4. Thread scalability
fig, ax = plt.subplots(figsize=(8, 5))
for schedule in SCHEDULES:
    data = [m for m in metrics if m['schedule'] == schedule and m['size'] == 1024]
    if not data:
        continue
    data.sort(key=lambda x: x['threads'])
    threads = [m['threads'] for m in data]
    gflops = [m['gflops'] for m in data]
    ax.plot(threads, gflops, marker='o', linewidth=2, label=schedule)
ax.set_xlabel('Threads', fontsize=12)
ax.set_ylabel('Performance (GFLOPS)', fontsize=12)
ax.set_title('Thread Scalability (N=1024)', fontsize=13)
ax.set_xticks(THREADS)
ax.grid(True, alpha=0.3)
ax.legend()
plt.tight_layout()
plt.savefig(IMG_DIR / 'scalability.pdf', bbox_inches='tight')
plt.savefig(IMG_DIR / 'scalability.png', dpi=300)
print('Saved: scalability')

print('\nAll plots generated successfully!')
