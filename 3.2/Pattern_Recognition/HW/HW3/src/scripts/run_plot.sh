#!/usr/bin/env bash
# ============================================================================
# run_plot.sh — 训练曲线 & 对比图生成 (Step D)
# ============================================================================

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

# ── D1: 4000 标签 自研 vs Baseline 对比 ──
echo "========== D1: 4000-label 对比图 =========="
python src/plot_curves.py \
    --ours fixmatch_ours_4k \
    --baseline fixmatch_baseline_4k \
    --mode comparison \
    --output_dir img/4klabels

# ── D2: 三种标注量自研单图 ──
echo "========== D2: 40-label 单图 =========="
python src/plot_curves.py \
    --ours fixmatch_ours_40 \
    --mode single \
    --output_dir img/40labels

echo "========== D2: 250-label 单图 =========="
python src/plot_curves.py \
    --ours fixmatch_ours_250 \
    --mode single \
    --output_dir img/250labels

echo "========== D2: 4k-label 单图 =========="
python src/plot_curves.py \
    --ours fixmatch_ours_4k \
    --mode single \
    --output_dir img/4klabels

echo "========== 绘图全部完成 =========="
