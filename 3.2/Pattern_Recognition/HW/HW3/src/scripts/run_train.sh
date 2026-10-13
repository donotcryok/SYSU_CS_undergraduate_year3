#!/usr/bin/env bash
# ============================================================================
# run_train.sh — 自研 FixMatch 训练 (Step B)
# ============================================================================
# 用法:
#   bash src/scripts/run_train.sh          # 全部三个实验
#   bash src/scripts/run_train.sh 40       # 仅 40 labels
#   bash src/scripts/run_train.sh 250      # 仅 250 labels
#   bash src/scripts/run_train.sh 4k       # 仅 4000 labels
# ============================================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

TARGET="${1:-all}"

run_40() {
    echo "========== B1: 40 labels/class (65536 steps) =========="
    python src/train.py \
        --exp_name fixmatch_ours_40 \
        --data_root . \
        --num_labeled 40 \
        --total_steps 65536 \
        --batch_size 64 \
        --mu 7 \
        --lr 0.03 \
        --amp \
        --num_workers 4 \
        --seed 42
}

run_250() {
    echo "========== B2: 250 labels/class (32768 steps) =========="
    python src/train.py \
        --exp_name fixmatch_ours_250 \
        --data_root . \
        --num_labeled 250 \
        --total_steps 32768 \
        --batch_size 64 \
        --mu 7 \
        --lr 0.03 \
        --amp \
        --num_workers 4 \
        --seed 42
}

run_4k() {
    echo "========== B3: 4000 labels/class (16384 steps) =========="
    python src/train.py \
        --exp_name fixmatch_ours_4k \
        --data_root . \
        --num_labeled 4000 \
        --total_steps 16384 \
        --batch_size 64 \
        --mu 7 \
        --lr 0.03 \
        --amp \
        --num_workers 4 \
        --seed 42
}

case "$TARGET" in
    40)   run_40 ;;
    250)  run_250 ;;
    4k)   run_4k ;;
    all)
        run_40
        run_250
        run_4k
        ;;
    *)
        echo "Usage: $0 {40|250|4k|all}"
        exit 1
        ;;
esac

echo "========== 训练全部完成 =========="
