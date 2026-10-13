#!/bin/bash
# filepath: run_experiments.sh

# 设置路径变量
GEM5_PATH="/root/gem5/build/RISCV/gem5.opt"  # 请根据您的实际路径修改
CONFIG_PATH="O3CPU.py"
BINARY_PATH="daxpy"
RESULTS_DIR="experiment_results"

# 创建结果目录
mkdir -p $RESULTS_DIR

# 参数数组
phys_regs=(64 256 1024)  # 物理寄存器数量
iq_entries=(4 16 64 256)  # 指令队列条目数
rob_entries=(4 16 64 256)  # 重排序缓冲区条目数

echo "开始运行gem5 O3 CPU仿真实验..."
echo "实验参数组合总数: $((${#phys_regs[@]} * ${#iq_entries[@]} * ${#rob_entries[@]}))"

# 创建CSV文件记录结果
echo "PhysRegs,IQEntries,ROBEntries,NumCycles,ROBFullEvents,IQFullEvents,FullRegistersEvents" > $RESULTS_DIR/results.csv

# 遍历所有参数组合
for phys in "${phys_regs[@]}"; do
    for iq in "${iq_entries[@]}"; do
        for rob in "${rob_entries[@]}"; do
            echo "运行实验: PhysRegs=$phys, IQ=$iq, ROB=$rob"
            
            # 创建输出目录
            outdir="$RESULTS_DIR/phys${phys}_iq${iq}_rob${rob}"
            mkdir -p $outdir
            
            # 运行仿真
            $GEM5_PATH --outdir=$outdir --remote-gdb-port=0 $CONFIG_PATH \
             -c $BINARY_PATH \
             --num-phys-int-regs=$phys \
             --num-iq-entries=$iq \
             --num-rob-entries=$rob
            
            # 提取关键指标
            if [ -f "$outdir/stats.txt" ]; then
                numCycles=$(grep "system.cpu.numCycles" $outdir/stats.txt | awk '{print $2}')
                robFull=$(grep "system.cpu.rename.ROBFullEvents" $outdir/stats.txt | awk '{print $2}')
                iqFull=$(grep "system.cpu.rename.IQFullEvents" $outdir/stats.txt | awk '{print $2}')
                regFull=$(grep "system.cpu.rename.fullRegistersEvents" $outdir/stats.txt | awk '{print $2}')
                
                echo "$phys,$iq,$rob,$numCycles,$robFull,$iqFull,$regFull" >> $RESULTS_DIR/results.csv
                echo "  完成 - 时钟数: $numCycles"
            else
                echo "  错误: 未找到stats.txt文件"
            fi
        done
    done
done

echo "所有实验完成！结果保存在 $RESULTS_DIR/results.csv"