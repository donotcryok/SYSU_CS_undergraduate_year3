#!/bin/bash

# ============================================================
# Lab2 MPI 并行矩阵乘法 - 自动化测试脚本 (通用化版本)
# ============================================================
# 功能：遍历不同进程数和矩阵规模，运行测试并记录结果
# 使用方法：bash run_tests.sh
# 输出文件：results.txt
# ============================================================

# 定义输出文件
OUTPUT_FILE="results.txt"
EXECUTABLE="mpi_v2"
SOURCE_FILE="mpi_v2.c"

# 定义测试参数
PROCESS_COUNTS=(1 2 4 8 16)
MATRIX_SIZES=(128 256 512 1024 2048)

# MPI 运行参数（绕过WSL限制）
MPI_OPTS="--allow-run-as-root --oversubscribe"

# 清空或创建输出文件
echo "============================================"  > "$OUTPUT_FILE"
echo "Lab2 MPI 并行矩阵乘法 - 性能测试结果"      >> "$OUTPUT_FILE"
echo "测试时间: $(date '+%Y-%m-%d %H:%M:%S')"    >> "$OUTPUT_FILE"
echo "测试模式: 方阵 (m=n=k=S)"                  >> "$OUTPUT_FILE"
echo "============================================"  >> "$OUTPUT_FILE"
echo ""                                           >> "$OUTPUT_FILE"

# 编译代码
echo "正在编译 $SOURCE_FILE ..."
mpicc -O3 "$SOURCE_FILE" -o "$EXECUTABLE"
if [ $? -ne 0 ]; then
    echo "编译失败！请检查源代码。"
    exit 1
fi
echo "编译成功！"
echo ""

# 输出表头
echo "============================================"  >> "$OUTPUT_FILE"
echo "格式: Size: m x n x k, Procs: <进程数>, Time: <时间> s" >> "$OUTPUT_FILE"
echo "============================================"  >> "$OUTPUT_FILE"
echo ""                                           >> "$OUTPUT_FILE"

# 开始测试
echo "开始性能测试..."
echo "进程数配置: ${PROCESS_COUNTS[*]}"
echo "矩阵规模配置: ${MATRIX_SIZES[*]} (方阵模式 m=n=k)"
echo ""

total_tests=$((${#PROCESS_COUNTS[@]} * ${#MATRIX_SIZES[@]}))
current_test=0

# 双层循环遍历所有配置
for procs in "${PROCESS_COUNTS[@]}"; do
    echo "----------------------------------------"  >> "$OUTPUT_FILE"
    echo "进程数: $procs"                           >> "$OUTPUT_FILE"
    echo "----------------------------------------"  >> "$OUTPUT_FILE"
    
    for S in "${MATRIX_SIZES[@]}"; do
        current_test=$((current_test + 1))
        echo -n "[$current_test/$total_tests] 测试: Procs=$procs, Size=$S x $S x $S ... "
        
        # 运行MPI程序（传入三个相同的参数作为方阵）
        result=$(mpirun $MPI_OPTS -n $procs ./$EXECUTABLE $S $S $S 2>&1)
        
        # 提取时间信息
        time_line=$(echo "$result" | grep "Size: $S x $S x $S")
        
        if [ -n "$time_line" ]; then
            echo "$time_line" >> "$OUTPUT_FILE"
            echo "完成 - $time_line"
        else
            # 尝试匹配其他格式
            time_line=$(echo "$result" | grep "Size:")
            if [ -n "$time_line" ]; then
                echo "$time_line" >> "$OUTPUT_FILE"
                echo "完成 - $time_line"
            else
                echo "Size: $S x $S x $S, Procs: $procs, Time: Error (运行失败)" >> "$OUTPUT_FILE"
                echo "失败"
                echo "错误信息: $result" >> "$OUTPUT_FILE"
            fi
        fi
    done
    
    echo "" >> "$OUTPUT_FILE"
done

# 输出汇总表格
echo ""                                           >> "$OUTPUT_FILE"
echo "============================================"  >> "$OUTPUT_FILE"
echo "性能汇总表格 (方阵 m=n=k)"                   >> "$OUTPUT_FILE"
echo "============================================"  >> "$OUTPUT_FILE"
echo ""                                           >> "$OUTPUT_FILE"

# 生成表格头
printf "%-8s" "进程数\\规模" >> "$OUTPUT_FILE"
for S in "${MATRIX_SIZES[@]}"; do
    printf "%12d" "$S" >> "$OUTPUT_FILE"
done
echo "" >> "$OUTPUT_FILE"

# 生成表格分隔线
printf "%-8s" "--------" >> "$OUTPUT_FILE"
for S in "${MATRIX_SIZES[@]}"; do
    printf "%12s" "------------" >> "$OUTPUT_FILE"
done
echo "" >> "$OUTPUT_FILE"

# 重新运行测试生成表格数据
for procs in "${PROCESS_COUNTS[@]}"; do
    printf "%-8d" "$procs" >> "$OUTPUT_FILE"
    
    for S in "${MATRIX_SIZES[@]}"; do
        # 运行一次获取时间
        result=$(mpirun $MPI_OPTS -n $procs ./$EXECUTABLE $S $S $S 2>&1)
        time_line=$(echo "$result" | grep "Size:")
        
        # 提取时间值
        if [ -n "$time_line" ]; then
            time_val=$(echo "$time_line" | grep -oP 'Time: \K[0-9.]+')
            printf "%12.4f" "$time_val" >> "$OUTPUT_FILE"
        else
            printf "%12s" "Error" >> "$OUTPUT_FILE"
        fi
    done
    echo "" >> "$OUTPUT_FILE"
done

echo ""                                           >> "$OUTPUT_FILE"
echo "============================================"  >> "$OUTPUT_FILE"
echo "测试完成时间: $(date '+%Y-%m-%d %H:%M:%S')" >> "$OUTPUT_FILE"
echo "============================================"  >> "$OUTPUT_FILE"

echo ""
echo "============================================"
echo "测试完成！"
echo "结果已保存到: $OUTPUT_FILE"
echo "============================================"