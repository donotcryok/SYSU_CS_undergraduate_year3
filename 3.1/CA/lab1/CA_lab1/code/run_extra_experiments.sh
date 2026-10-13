#!/bin/bash

# 设置路径变量
GEM5_PATH="/root/gem5/build/RISCV/gem5.opt"
CONFIG_PATH="extra.py"
BINARY_PATH="daxpy"
RESULTS_DIR="extra_experiment_results"

# 创建结果目录
mkdir -p $RESULTS_DIR

# 缓存大小参数
l1d_sizes=("32KiB" )
l2_sizes=("128KiB" )

echo "开始运行缓存大小影响实验..."
echo "实验参数组合总数: $((${#l1d_sizes[@]} * ${#l2_sizes[@]}))"

# 创建CSV文件记录结果
echo "L1DSize,L2Size,NumCycles,L1DCacheMisses,L2CacheMisses,L1DHitRate,L2HitRate" > $RESULTS_DIR/extra_results.csv

# 遍历所有缓存大小组合
for l1d in "${l1d_sizes[@]}"; do
    for l2 in "${l2_sizes[@]}"; do
        echo "运行实验: L1D=$l1d, L2=$l2"
        
        # 创建输出目录
        outdir="$RESULTS_DIR/l1d_${l1d}_l2_${l2}"
        mkdir -p $outdir
        
        # 运行仿真
        $GEM5_PATH --outdir=$outdir --remote-gdb-port=0 $CONFIG_PATH \
         -c $BINARY_PATH \
         --l1d-size=$l1d \
         --l2-size=$l2
        
        # 提取关键指标
        if [ -f "$outdir/stats.txt" ]; then
            numCycles=$(grep "system.cpu.numCycles" $outdir/stats.txt | awk '{print $2}')
            l1dMisses=$(grep "system.cpu.dcache.overallMisses::total" $outdir/stats.txt | awk '{print $2}')
            l2Misses=$(grep "system.l2cache.overallMisses::total" $outdir/stats.txt | awk '{print $2}')
            l1dAccesses=$(grep "system.cpu.dcache.overallAccesses::total" $outdir/stats.txt | awk '{print $2}')
            l2Accesses=$(grep "system.l2cache.overallAccesses::total" $outdir/stats.txt | awk '{print $2}')
            
            # 计算命中率
            if [ ! -z "$l1dAccesses" ] && [ "$l1dAccesses" -gt 0 ]; then
                l1dHitRate=$(echo "scale=4; (1 - $l1dMisses / $l1dAccesses) * 100" | bc -l)
            else
                l1dHitRate="0"
            fi
            
            if [ ! -z "$l2Accesses" ] && [ "$l2Accesses" -gt 0 ]; then
                l2HitRate=$(echo "scale=4; (1 - $l2Misses / $l2Accesses) * 100" | bc -l)
            else
                l2HitRate="0"
            fi
            
            # 处理空值
            l1dMisses=${l1dMisses:-0}
            l2Misses=${l2Misses:-0}
            
            echo "$l1d,$l2,$numCycles,$l1dMisses,$l2Misses,$l1dHitRate,$l2HitRate" >> $RESULTS_DIR/extra_results.csv
            echo "  完成 - 时钟数: $numCycles, L1D缺失: $l1dMisses, L2缺失: $l2Misses"
        else
            echo "  错误: 未找到stats.txt文件"
            echo "$l1d,$l2,ERROR,ERROR,ERROR,ERROR,ERROR" >> $RESULTS_DIR/extra_results.csv
        fi
    done
done

echo "所有扩展实验完成！结果保存在 $RESULTS_DIR/extra_results.csv"
