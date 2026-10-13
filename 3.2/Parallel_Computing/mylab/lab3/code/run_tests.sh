#!/bin/bash
# =============================================================================
# Lab3 Pthreads 并行实验 - 多策略对比测试脚本
# =============================================================================
# 编译参数: gcc -std=c11 -Wall -Wextra -O2 -pthread
# 测试内容:
#   1. 矩阵乘法策略对比: Row-wise vs Column-wise vs Block-wise
#   2. 数组求和策略对比: Global-Mutex vs Local-Reduction
# 
# 使用方法:
#   从项目根目录运行: bash code/run_tests.sh
#   或从 code 目录运行: bash run_tests.sh
# =============================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 自动检测脚本所在目录和项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$SCRIPT_DIR" == *"/code" ]]; then
    CODE_DIR="$SCRIPT_DIR"
    ROOT_DIR="$(dirname "$SCRIPT_DIR")"
else
    ROOT_DIR="$(pwd)"
    CODE_DIR="$ROOT_DIR/code"
fi

# 结果文件
MATRIX_RESULT_FILE="$CODE_DIR/results_matrix_compare.txt"
SUM_RESULT_FILE="$CODE_DIR/results_sum_compare.txt"

# 编译器参数
CC=gcc
CFLAGS="-std=c11 -Wall -Wextra -O2 -pthread"

echo "脚本目录: $SCRIPT_DIR"
echo "代码目录: $CODE_DIR"
echo "根目录: $ROOT_DIR"
echo ""

# =============================================================================
# 编译程序
# =============================================================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}编译程序${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "${GREEN}编译 matrix_pthread.c...${NC}"
$CC $CFLAGS -o "$CODE_DIR/matrix_pthread" "$CODE_DIR/matrix_pthread.c" -lm
if [ $? -eq 0 ]; then
    echo -e "${GREEN}编译成功: matrix_pthread${NC}"
else
    echo -e "${RED}编译失败: matrix_pthread${NC}"
    exit 1
fi

echo -e "${GREEN}编译 sum_pthread.c...${NC}"
$CC $CFLAGS -o "$CODE_DIR/sum_pthread" "$CODE_DIR/sum_pthread.c"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}编译成功: sum_pthread${NC}"
else
    echo -e "${RED}编译失败: sum_pthread${NC}"
    exit 1
fi

echo ""

# =============================================================================
# 矩阵乘法策略对比测试
# =============================================================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}矩阵乘法策略对比测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo "策略: 0=Row-wise, 1=Column-wise, 2=Block-wise"
echo "线程数: 1, 2, 4, 8, 16"
echo "规模: 512, 1024, 2048 (方阵)"
echo ""

# 清空结果文件
echo "=============================================================================" > "$MATRIX_RESULT_FILE"
echo "矩阵乘法策略对比测试结果" >> "$MATRIX_RESULT_FILE"
echo "测试时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$MATRIX_RESULT_FILE"
echo "策略: 0=Row-wise, 1=Column-wise, 2=Block-wise" >> "$MATRIX_RESULT_FILE"
echo "=============================================================================" >> "$MATRIX_RESULT_FILE"
echo "" >> "$MATRIX_RESULT_FILE"

# 策略数组
STRATEGIES=(0 1 2)
STRATEGY_NAMES=("Row-wise" "Column-wise" "Block-wise")
# 线程数数组
THREADS=(1 2 4 8 16)
# 规模数组（使用较大规模以体现差异）
SIZES=(512 1024 2048)

for size in "${SIZES[@]}"; do
    echo "" >> "$MATRIX_RESULT_FILE"
    echo "--- 矩阵规模: ${size}x${size}x${size} ---" >> "$MATRIX_RESULT_FILE"
    for strategy in "${STRATEGIES[@]}"; do
        echo "" >> "$MATRIX_RESULT_FILE"
        echo "策略: ${STRATEGY_NAMES[$strategy]}" >> "$MATRIX_RESULT_FILE"
        for t in "${THREADS[@]}"; do
            echo -e "${YELLOW}[TEST] 矩阵乘法: 规模=${size}, 策略=${STRATEGY_NAMES[$strategy]}, 线程数=${t}${NC}"
            "$CODE_DIR/matrix_pthread" $size $size $size $t $strategy >> "$MATRIX_RESULT_FILE"
        done
    done
done

echo ""
echo -e "${GREEN}矩阵乘法策略对比测试完成！${NC}"
echo -e "${GREEN}结果已保存到: ${MATRIX_RESULT_FILE}${NC}"
echo ""

# =============================================================================
# 数组求和策略对比测试
# =============================================================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}数组求和策略对比测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo "策略: 0=Global-Mutex, 1=Local-Reduction"
echo "线程数: 1, 2, 4, 8, 16"
echo "规模: 10M, 128M"
echo ""
echo -e "${YELLOW}警告: Global-Mutex策略测试可能需要较长时间！${NC}"
echo ""

# 清空结果文件
echo "=============================================================================" > "$SUM_RESULT_FILE"
echo "数组求和策略对比测试结果" >> "$SUM_RESULT_FILE"
echo "测试时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$SUM_RESULT_FILE"
echo "策略: 0=Global-Mutex, 1=Local-Reduction" >> "$SUM_RESULT_FILE"
echo "=============================================================================" >> "$SUM_RESULT_FILE"
echo "" >> "$SUM_RESULT_FILE"

# 策略数组
SUM_STRATEGIES=(0 1)
SUM_STRATEGY_NAMES=("Global-Mutex" "Local-Reduction")
# 线程数数组
SUM_THREADS=(1 2 4 8 16)
# 规模数组（使用较大规模）
SUM_SIZES=(10000000 128000000)

for arr_size in "${SUM_SIZES[@]}"; do
    echo "" >> "$SUM_RESULT_FILE"
    echo "--- 数组规模: ${arr_size} ---" >> "$SUM_RESULT_FILE"
    for strategy in "${SUM_STRATEGIES[@]}"; do
        echo "" >> "$SUM_RESULT_FILE"
        echo "策略: ${SUM_STRATEGY_NAMES[$strategy]}" >> "$SUM_RESULT_FILE"
        for t in "${SUM_THREADS[@]}"; do
            echo -e "${YELLOW}[TEST] 数组求和: 规模=${arr_size}, 策略=${SUM_STRATEGY_NAMES[$strategy]}, 线程数=${t}${NC}"
            "$CODE_DIR/sum_pthread" $arr_size $t $strategy >> "$SUM_RESULT_FILE"
        done
    done
done

echo ""
echo -e "${GREEN}数组求和策略对比测试完成！${NC}"
echo -e "${GREEN}结果已保存到: ${SUM_RESULT_FILE}${NC}"
echo ""

# =============================================================================
# 测试完成
# =============================================================================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}所有测试完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "生成的结果文件:"
echo "  - $MATRIX_RESULT_FILE"
echo "  - $SUM_RESULT_FILE"
echo ""
echo "请运行 python3 code/plot_comparison.py 生成对比图表"
