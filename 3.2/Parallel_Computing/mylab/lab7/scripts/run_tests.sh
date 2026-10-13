#!/bin/bash
# run_tests.sh — 实验七性能测试 (简化健壮版)
# 用法: bash scripts/run_tests.sh
set +e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJ_DIR="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PROJ_DIR/src"
LOGS_DIR="$PROJ_DIR/logs"
RESULTS="$LOGS_DIR/results.csv"

cd "$SRC_DIR"

# 编译 (-g for valgrind later)
echo "[compile] building..."
make clean >/dev/null 2>&1 || true
make CXXFLAGS="-O2 -g -Wall" all
echo "[compile] done"

export OMPI_ALLOW_RUN_AS_ROOT=1
export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

echo "version,N,P,nits,error,time_sec,mflops" > "$RESULTS"

run_one() {
    local ver=$1   # mpi or mpi_opt
    local ln2=$2
    local np=$3
    local nits=$4
    local N=$((1 << ln2))
    local exe
    if [ "$ver" = "mpi" ]; then exe="./fft_mpi"; else exe="./fft_mpi_opt"; fi

    local raw
    raw=$(mpirun --allow-run-as-root -np "$np" "$exe" "$ln2" "$nits" 2>&1)
    echo "  [$ver P=$np N=2^$ln2] $raw"

    # 用 awk 提取 key=value 对
    local err tm mf
    err=$(echo "$raw" | awk '{for(i=1;i<=NF;i++) if($i ~ /^error=/) {sub(/error=/,"",$i); print $i; exit}}')
    tm=$(echo "$raw"  | awk '{for(i=1;i<=NF;i++) if($i ~ /^time=/)  {sub(/time=/,"",$i);  print $i; exit}}')
    mf=$(echo "$raw"  | awk '{for(i=1;i<=NF;i++) if($i ~ /^mflops=/){sub(/mflops=/,"",$i);print $i; exit}}')

    echo "$ver,$N,$np,$nits,$err,$tm,$mf" >> "$RESULTS"
}

echo "[run] N=2^16 (nits=100)"
for np in 1 2 4 8; do
    run_one mpi     16 $np 100
    run_one mpi_opt 16 $np 100
done

echo "[run] N=2^20 (nits=10)"
for np in 1 2 4 8; do
    run_one mpi     20 $np 10
    run_one mpi_opt 20 $np 10
done

echo "[run] N=2^24 (nits=1)"
for np in 1 2 4 8; do
    run_one mpi     24 $np 1
    run_one mpi_opt 24 $np 1
done

echo ""
echo "=== RESULTS ==="
cat "$RESULTS"
echo "=== DONE ==="
