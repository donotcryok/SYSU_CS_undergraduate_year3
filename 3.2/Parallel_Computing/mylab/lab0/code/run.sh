#!/bin/bash
# Lab0 自动化编译和测试脚本
# 用于编译和运行 6 个版本的矩阵乘法程序

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 矩阵大小（可修改）
MATRIX_SIZE=1024

# 结果文件
RESULT_FILE="results.txt"

echo "=============================================="
echo "  Lab0 矩阵乘法性能测试脚本"
echo "=============================================="
echo ""

# 清空结果文件
> $RESULT_FILE

# 记录测试信息
echo "测试日期: $(date)" >> $RESULT_FILE
echo "矩阵大小: N = $MATRIX_SIZE" >> $RESULT_FILE
echo "浮点运算次数: 2 * $MATRIX_SIZE^3 = $((2 * MATRIX_SIZE * MATRIX_SIZE * MATRIX_SIZE))" >> $RESULT_FILE
echo "" >> $RESULT_FILE

# 检查 MKL 环境
check_mkl() {
    if [ -z "$MKLROOT" ]; then
        echo -e "${YELLOW}警告: MKL 环境变量未设置${NC}"
        echo "正在尝试设置 MKL 环境..."
        if [ -f "/opt/intel/oneapi/mkl/latest/env/vars.sh" ]; then
            source /opt/intel/oneapi/mkl/latest/env/vars.sh intel64 ilp64
            echo -e "${GREEN}MKL 环境设置成功${NC}"
        else
            echo -e "${RED}错误: 未找到 MKL 安装${NC}"
            echo "请先安装 Intel MKL:"
            echo "  sudo apt install intel-oneapi-mkl-devel -y"
            return 1
        fi
    fi
    return 0
}

# 编译函数
compile_c() {
    local src=$1
    local out=$2
    local flags=$3
    
    echo -e "${BLUE}编译: $src -> $out${NC}"
    gcc $flags -o $out $src -lm
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}编译成功: $out${NC}"
        return 0
    else
        echo -e "${RED}编译失败: $src${NC}"
        return 1
    fi
}

# 编译 MKL 版本
compile_mkl() {
    local src=$1
    local out=$2
    
    echo -e "${BLUE}编译 MKL 版本: $src -> $out${NC}"
    # 使用静态链接方式，避免 OpenMP 符号缺失问题
    gcc -o $out $src -lmkl_intel_ilp64 -lmkl_sequential -lmkl_core -lpthread -lm -ldl
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}编译成功: $out${NC}"
        return 0
    else
        echo -e "${RED}编译失败: $src (MKL)${NC}"
        return 1
    fi
}

# 运行测试函数
run_test() {
    local name=$1
    local cmd=$2
    
    echo ""
    echo "----------------------------------------------"
    echo -e "${YELLOW}运行: $name${NC}"
    echo "----------------------------------------------"
    
    echo "" >> $RESULT_FILE
    echo "========== $name ==========" >> $RESULT_FILE
    
    # 运行并捕获输出
    output=$(eval $cmd 2>&1)
    echo "$output"
    echo "$output" >> $RESULT_FILE
}

# ==================== 主测试流程 ====================

echo ""
echo "=============================================="
echo "  Step 1: 编译所有 C 程序"
echo "=============================================="

# V2: C 语言基础版本 (无优化)
compile_c "v2_c_base.c" "v2_c_base" ""
v2_compiled=$?

# V3: C 语言循环重排版本 (无优化)
compile_c "v3_c_ikj.c" "v3_c_ikj" ""
v3_compiled=$?

# V4: C 语言编译优化版本 (-O3)
compile_c "v4_c_o3.c" "v4_c_o3" "-O3"
v4_compiled=$?

# V5: C 语言循环展开版本 (-O3)
compile_c "v5_c_unroll.c" "v5_c_unroll" "-O3"
v5_compiled=$?

# V6: Intel MKL 版本
check_mkl
if [ $? -eq 0 ]; then
    compile_mkl "v6_mkl.c" "v6_mkl"
    v6_compiled=$?
else
    v6_compiled=1
fi

echo ""
echo "=============================================="
echo "  Step 2: 运行所有测试"
echo "=============================================="

# V1: Python 版本
echo ""
echo "----------------------------------------------"
echo -e "${YELLOW}V1: Python 基准版本${NC}"
echo "----------------------------------------------"
if command -v python3 &> /dev/null; then
    echo "" >> $RESULT_FILE
    echo "========== V1: Python 基准版本 ==========" >> $RESULT_FILE
    output=$(python3 v1_python.py 2>&1)
    # 修改 Python 脚本使用固定矩阵大小
    output=$(python3 -c "
import numpy as np
import time

N = $MATRIX_SIZE
print(f'矩阵大小: N = {N}')
print(f'浮点运算次数: 2 * {N}^3 = {2 * N**3:,}')

np.random.seed(42)
A = np.random.rand(N, N)
B = np.random.rand(N, N)

start_time = time.time()
C = np.dot(A, B)
end_time = time.time()

elapsed_time = end_time - start_time
flops = 2 * N**3
gflops = flops / (elapsed_time * 1e9)

print(f'运行时间: {elapsed_time:.6f} 秒')
print(f'GFLOPS: {gflops:.4f}')
" 2>&1)
    echo "$output"
    echo "$output" >> $RESULT_FILE
else
    echo -e "${RED}Python3 未安装，跳过 V1 测试${NC}"
fi

# V2: C 语言基础版本
if [ $v2_compiled -eq 0 ]; then
    run_test "V2: C 语言基础版本 (i-j-k)" "./v2_c_base $MATRIX_SIZE"
fi

# V3: C 语言循环重排版本
if [ $v3_compiled -eq 0 ]; then
    run_test "V3: C 语言循环重排版本 (i-k-j)" "./v3_c_ikj $MATRIX_SIZE"
fi

# V4: C 语言编译优化版本
if [ $v4_compiled -eq 0 ]; then
    run_test "V4: C 语言编译优化版本 (-O3)" "./v4_c_o3 $MATRIX_SIZE"
fi

# V5: C 语言循环展开版本
if [ $v5_compiled -eq 0 ]; then
    run_test "V5: C 语言循环展开版本" "./v5_c_unroll $MATRIX_SIZE"
fi

# V6: Intel MKL 版本
if [ $v6_compiled -eq 0 ]; then
    run_test "V6: Intel MKL 库版本" "./v6_mkl $MATRIX_SIZE"
fi

echo ""
echo "=============================================="
echo "  Step 3: 生成性能对比表格"
echo "=============================================="

# 提取结果并生成表格
echo ""
echo -e "${GREEN}测试完成！结果已保存到 $RESULT_FILE${NC}"
echo ""
echo "请将以下数据填入实验报告："
echo "----------------------------------------------"
cat $RESULT_FILE
echo "----------------------------------------------"

# 清理可执行文件
echo ""
echo "是否清理编译生成的可执行文件？(y/n)"
read -t 5 answer || answer="n"
if [ "$answer" = "y" ]; then
    rm -f v2_c_base v3_c_ikj v4_c_o3 v5_c_unroll v6_mkl
    echo "可执行文件已清理"
fi

echo ""
echo "=============================================="
echo "  测试结束"
echo "=============================================="