#!/bin/bash
# MPI 并行矩阵乘法自动化测试脚本，测试不同进程数和矩阵规模下的性能

# 输出文件
RESULT_FILE="results.txt"
EXECUTABLE="mpi_v1"
SOURCE="mpi_v1.c"

# 清空结果文件
echo "# MPI Matrix Multiplication Performance Results" > $RESULT_FILE
echo "# Format: Size: <N>, Procs: <P>, Time: <T> s" >> $RESULT_FILE
echo "# Generated on: $(date)" >> $RESULT_FILE
echo "# ============================================" >> $RESULT_FILE
echo "" >> $RESULT_FILE

# 编译程序
echo "Compiling $SOURCE..."
mpicc -O2 -o $EXECUTABLE $SOURCE
if [ $? -ne 0 ]; then
    echo "Error: Compilation failed!"
    exit 1
fi
echo "Compilation successful!"
echo ""

# 进程数列表
PROCS_LIST=(1 2 4 8 16)
# 矩阵规模列表
SIZES_LIST=(128 256 512 1024 2048)

# 运行测试
echo "Starting performance tests..."
echo "========================================"

for procs in "${PROCS_LIST[@]}"; do
    for size in "${SIZES_LIST[@]}"; do
        echo "Running: Procs=$procs, Size=$size"
        echo "# Procs=$procs, Size=$size" >> $RESULT_FILE
        
        # 运行 MPI 程序并捕获输出
        output=$(mpirun --allow-run-as-root -n $procs ./$EXECUTABLE $size 2>&1)
        
        # 提取时间行并追加到结果文件
        echo "$output" | grep "Size:" >> $RESULT_FILE
        
        echo "" >> $RESULT_FILE
    done
    echo "----------------------------------------"
done

echo ""
echo "All tests completed!"
echo "Results saved to: $RESULT_FILE"
echo "Summary:"
cat $RESULT_FILE | grep "Size:"