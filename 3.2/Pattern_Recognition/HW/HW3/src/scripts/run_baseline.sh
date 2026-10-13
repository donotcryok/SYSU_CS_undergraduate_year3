#!/usr/bin/env bash
# ============================================================================
# run_baseline.sh — USB/semilearn FixMatch Baseline 训练 (Step C)
# ============================================================================
# 仅 4000 标签 (2^14 = 16384 steps), seed=123
# ============================================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "========== Baseline: 4000 labels/class (16384 steps) =========="

python src/baseline.py \
    --exp_name fixmatch_baseline_4k \
    --data_root . \
    --num_labeled 4000 \
    --total_steps 16384 \
    --batch_size 64 \
    --mu 7 \
    --lr 0.03 \
    --amp \
    --num_workers 4

echo "========== Baseline 训练完成 =========="
