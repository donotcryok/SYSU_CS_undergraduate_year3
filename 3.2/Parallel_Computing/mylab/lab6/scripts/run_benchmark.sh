#!/bin/bash
# run_benchmark.sh — 自动化性能基准测试脚本
#
# 功能：
#   1. 运行不同线程数 (1,2,4,8,16) 的 Pthreads Native、parallel_for (static/cyclic/dynamic)、OpenMP 版本
#   2. 运行不同任务规模 (128, 256, 512) 的热传导模拟
#   3. 输出 CSV 数据到 stdout，日志到 stderr
#
# 用法：cd scripts && ./run_benchmark.sh [重复次数]
#   默认重复 3 次取中位数

set -e

REPEAT=${1:-3}
THREADS="1 2 4 8 16"
SIZES="128 256 512"
EPSILON="0.001"

SRC_DIR="../src"
PTHREAD_BIN="$SRC_DIR/heated_plate_pthread"
OMP_BIN="$SRC_DIR/heated_plate_openmp"
PF_BIN="$SRC_DIR/heated_plate_parallel_for"

# schedule 编号: 0=static, 1=cyclic, 2=dynamic
SCHEDULES=("0:static" "1:cyclic" "2:dynamic")

echo "# Lab6 Heated Plate Benchmark (comprehensive)" >&2
echo "# Repeat: $REPEAT, Sizes: $SIZES, Threads: $THREADS" >&2
echo "# Timestamp: $(date -Iseconds)" >&2

# CSV header
echo "version,size,threads,epsilon,repeat,time_sec"

# ─── Native Pthreads ─────────────────────────────────────────────
for SIZE in $SIZES; do
    for THR in $THREADS; do
        for ((r=1; r<=REPEAT; r++)); do
            >&2 echo "  [Pthreads] size=$SIZE threads=$THR repeat=$r"
            OUT=$($PTHREAD_BIN $SIZE $SIZE $EPSILON $THR 2>&1) || true
            CSV_LINE=$(echo "$OUT" | grep "^CSV," | tail -1)
            if [ -n "$CSV_LINE" ]; then
                TIME=$(echo "$CSV_LINE" | cut -d',' -f6)
                echo "pthread,$SIZE,$THR,$EPSILON,$r,$TIME"
            else
                >&2 echo "ERROR: pthread,$SIZE,$THR,$EPSILON,$r,NO_CSV"
            fi
        done
    done
done

# ─── parallel_for (3 schedules) ──────────────────────────────────
for S_ENTRY in "${SCHEDULES[@]}"; do
    SCHED_ID="${S_ENTRY%%:*}"
    SCHED_NAME="${S_ENTRY##*:}"
    for SIZE in $SIZES; do
        for THR in $THREADS; do
            for ((r=1; r<=REPEAT; r++)); do
                >&2 echo "  [parallel_for/$SCHED_NAME] size=$SIZE threads=$THR repeat=$r"
                OUT=$(LD_LIBRARY_PATH="$SRC_DIR" $PF_BIN $SIZE $SIZE $EPSILON $THR $SCHED_ID 2>&1) || true
                # CSV 格式: CSV,M,N,epsilon,threads,schedule,time
                CSV_LINE=$(echo "$OUT" | grep "^CSV," | tail -1)
                if [ -n "$CSV_LINE" ]; then
                    TIME=$(echo "$CSV_LINE" | cut -d',' -f7)
                    echo "pf_${SCHED_NAME},$SIZE,$THR,$EPSILON,$r,$TIME"
                else
                    >&2 echo "ERROR: pf_${SCHED_NAME},$SIZE,$THR,$EPSILON,$r,NO_CSV"
                fi
            done
        done
    done
done

# ─── OpenMP ──────────────────────────────────────────────────────
for SIZE in $SIZES; do
    for THR in $THREADS; do
        for ((r=1; r<=REPEAT; r++)); do
            >&2 echo "  [OpenMP]   size=$SIZE threads=$THR repeat=$r"
            OUT=$($OMP_BIN $SIZE $SIZE $EPSILON $THR 2>&1) || true
            CSV_LINE=$(echo "$OUT" | grep "^CSV," | tail -1)
            if [ -n "$CSV_LINE" ]; then
                TIME=$(echo "$CSV_LINE" | cut -d',' -f6)
                echo "openmp,$SIZE,$THR,$EPSILON,$r,$TIME"
            else
                >&2 echo "ERROR: openmp,$SIZE,$THR,$EPSILON,$r,NO_CSV"
            fi
        done
    done
done

echo "# Benchmark complete." >&2
