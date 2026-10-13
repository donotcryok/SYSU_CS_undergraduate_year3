#!/bin/bash
# run_experiments.sh — 实验七自动化测试脚本
# 路径: scripts/run_experiments.sh
# 测试: N=2^16, 2^20, 2^24; P=1, 2, 4, 8
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJ_DIR="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$PROJ_DIR/src"
LOGS_DIR="$PROJ_DIR/logs"

cd "$SRC_DIR"

RESULTS="$LOGS_DIR/results.csv"
NP_LIST="1 2 4 8"
MPI_PREFIX="OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1 mpirun --allow-run-as-root"

echo "============================================"
echo "  实验七: MPI FFT 性能测试"
echo "============================================"

# 编译
echo "[1/3] 编译..."
make clean >/dev/null 2>&1 || true
make all
echo "编译完成"

# CSV 头
echo "version,N,P,nits,error,time_sec,mflops" > "$RESULTS"

echo "[2/3] 运行性能测试..."

# N=2^16, nits=100
echo "--- N=2^16=65536 (nits=100) ---"
for np in $NP_LIST; do
    LOG=$($MPI_PREFIX -np $np ./fft_mpi 16 100 2>&1)
    echo "  mpi    P=$np: $LOG"
    ERR=$(echo "$LOG" | sed 's/.*error=\([^ ]*\).*/\1/')
    TM=$(echo "$LOG"  | sed 's/.*time=\([^ ]*\).*/\1/')
    MF=$(echo "$LOG"  | sed 's/.*mflops=\([^ ]*\).*/\1/')
    echo "mpi,65536,$np,100,$ERR,$TM,$MF" >> "$RESULTS"

    LOG=$($MPI_PREFIX -np $np ./fft_mpi_opt 16 100 2>&1)
    echo "  mpi_opt P=$np: $LOG"
    ERR=$(echo "$LOG" | sed 's/.*error=\([^ ]*\).*/\1/')
    TM=$(echo "$LOG"  | sed 's/.*time=\([^ ]*\).*/\1/')
    MF=$(echo "$LOG"  | sed 's/.*mflops=\([^ ]*\).*/\1/')
    echo "mpi_opt,65536,$np,100,$ERR,$TM,$MF" >> "$RESULTS"
done

# N=2^20, nits=10
echo "--- N=2^20=1048576 (nits=10) ---"
for np in $NP_LIST; do
    LOG=$($MPI_PREFIX -np $np ./fft_mpi 20 10 2>&1)
    echo "  mpi    P=$np: $LOG"
    ERR=$(echo "$LOG" | sed 's/.*error=\([^ ]*\).*/\1/')
    TM=$(echo "$LOG"  | sed 's/.*time=\([^ ]*\).*/\1/')
    MF=$(echo "$LOG"  | sed 's/.*mflops=\([^ ]*\).*/\1/')
    echo "mpi,1048576,$np,10,$ERR,$TM,$MF" >> "$RESULTS"

    LOG=$($MPI_PREFIX -np $np ./fft_mpi_opt 20 10 2>&1)
    echo "  mpi_opt P=$np: $LOG"
    ERR=$(echo "$LOG" | sed 's/.*error=\([^ ]*\).*/\1/')
    TM=$(echo "$LOG"  | sed 's/.*time=\([^ ]*\).*/\1/')
    MF=$(echo "$LOG"  | sed 's/.*mflops=\([^ ]*\).*/\1/')
    echo "mpi_opt,1048576,$np,10,$ERR,$TM,$MF" >> "$RESULTS"
done

# N=2^24, nits=1
echo "--- N=2^24=16777216 (nits=1) ---"
for np in $NP_LIST; do
    LOG=$($MPI_PREFIX -np $np ./fft_mpi 24 1 2>&1)
    echo "  mpi    P=$np: $LOG"
    ERR=$(echo "$LOG" | sed 's/.*error=\([^ ]*\).*/\1/')
    TM=$(echo "$LOG"  | sed 's/.*time=\([^ ]*\).*/\1/')
    MF=$(echo "$LOG"  | sed 's/.*mflops=\([^ ]*\).*/\1/')
    echo "mpi,16777216,$np,1,$ERR,$TM,$MF" >> "$RESULTS"

    LOG=$($MPI_PREFIX -np $np ./fft_mpi_opt 24 1 2>&1)
    echo "  mpi_opt P=$np: $LOG"
    ERR=$(echo "$LOG" | sed 's/.*error=\([^ ]*\).*/\1/')
    TM=$(echo "$LOG"  | sed 's/.*time=\([^ ]*\).*/\1/')
    MF=$(echo "$LOG"  | sed 's/.*mflops=\([^ ]*\).*/\1/')
    echo "mpi_opt,16777216,$np,1,$ERR,$TM,$MF" >> "$RESULTS"
done

echo ""
echo "[3/3] Valgrind massif (fft_mpi_opt, N=2^16, P=4)..."
cd "$LOGS_DIR"
$MPI_PREFIX -np 4 valgrind --tool=massif --massif-out-file=massif.out.%p "$SRC_DIR/fft_mpi_opt" 16 10 >/dev/null 2>&1 || true

echo ""
echo "============================================"
echo "  测试完成！结果: $RESULTS"
cat "$RESULTS"
echo "============================================"
