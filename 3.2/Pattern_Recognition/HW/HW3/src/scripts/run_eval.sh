#!/usr/bin/env bash
# ============================================================================
# run_eval.sh — 最终评估 (Step E)
# ============================================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "========== 评估: 自研 40-label =========="
python src/test.py \
    --checkpoint src/runs/fixmatch_ours_40/checkpoint_final.pth \
    --data_root .

echo "========== 评估: 自研 250-label =========="
python src/test.py \
    --checkpoint src/runs/fixmatch_ours_250/checkpoint_final.pth \
    --data_root .

echo "========== 评估: 自研 4k-label =========="
python src/test.py \
    --checkpoint src/runs/fixmatch_ours_4k/checkpoint_final.pth \
    --data_root .

echo "========== 评估: Baseline 4k-label =========="
python src/test.py \
    --checkpoint src/runs/fixmatch_baseline_4k/latest_model.pth \
    --data_root .

echo "========== 评估全部完成 =========="
