#!/bin/bash
# run_tests.sh - 自动化测试脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 输出文件
RESULTS_FILE="results.txt"
CODE_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$CODE_DIR")"

cd "$ROOT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Lab4 自动化测试脚本${NC}"
echo -e "${BLUE}========================================${NC}"

# 清空结果文件
> "$RESULTS_FILE"

echo -e "${YELLOW}[1/3] 编译程序...${NC}"
# 编译方程求解程序（-lm 必须放在源文件之后）
gcc -O2 -pthread "$CODE_DIR/eq_solver.c" -o "$CODE_DIR/eq_solver" -lm
echo -e "${GREEN}✓ eq_solver.c 编译成功${NC}"

# 编译蒙特卡洛程序
gcc -O2 -pthread "$CODE_DIR/mc_pi.c" -o "$CODE_DIR/mc_pi" -lm
echo -e "${GREEN}✓ mc_pi.c 编译成功${NC}"

echo ""
echo -e "${YELLOW}[2/3] 测试方程求解程序...${NC}"
echo -e "${BLUE}----------------------------------------${NC}"

# 方程求解测试用例
# 格式: a b c 描述
EQ_TESTS=(
    "1 -3 2 两个不同实根(x²-3x+2=0)"
    "1 2 1 重根(x²+2x+1=0)"
    "1 0 1 无实根(x²+1=0)"
    "2 5 -3 两个不同实根(2x²+5x-3=0)"
)

echo "========== 方程求解测试 ==========" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

for test in "${EQ_TESTS[@]}"; do
    read -r a b c desc <<< "$test"
    echo -e "${BLUE}测试: $desc${NC}"
    echo "方程: ${a}x² + ${b}x + ${c} = 0" >> "$RESULTS_FILE"
    "$CODE_DIR/eq_solver" $a $b $c | tee -a "$RESULTS_FILE"
    echo "" >> "$RESULTS_FILE"
    echo -e "${GREEN}✓ 完成${NC}"
    echo ""
done

echo -e "${YELLOW}[3/3] 测试蒙特卡洛程序...${NC}"
echo -e "${BLUE}----------------------------------------${NC}"

echo "========== 蒙特卡洛测试 ==========" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

# 蒙特卡洛测试规模
# 题目要求范围: 1024 - 65536
# 追加大规模测试: 10M, 100M
MC_SCALES=(1024 4096 16384 65536 10000000 100000000)
THREAD_COUNTS=(1 2 4 8 16)

echo -e "${BLUE}蒙特卡洛测试规模: ${MC_SCALES[*]}${NC}"
echo -e "${BLUE}线程数: ${THREAD_COUNTS[*]}${NC}"
echo ""

# 表头
echo -n "Scale" >> "$RESULTS_FILE"
for t in "${THREAD_COUNTS[@]}"; do
    echo -n ",${t}threads" >> "$RESULTS_FILE"
done
echo "" >> "$RESULTS_FILE"

for scale in "${MC_SCALES[@]}"; do
    echo -e "${BLUE}--- 规模: $scale ---${NC}"
    echo -n "$scale" >> "$RESULTS_FILE"
    
    for t in "${THREAD_COUNTS[@]}"; do
        echo -e "  线程数: $t"
        output=$("$CODE_DIR/mc_pi" $scale $t 2>&1)
        
        # 提取耗时（毫秒）
        time_ms=$(echo "$output" | grep "计算耗时" | grep -oP '[\d.]+')
        
        # 提取Pi估计值
        pi_est=$(echo "$output" | grep "估计的Pi值" | grep -oP '[\d.]+')
        
        echo -n ",$time_ms" >> "$RESULTS_FILE"
        
        # 显示部分输出
        echo "$output" | tail -5
        echo ""
    done
    
    echo "" >> "$RESULTS_FILE"
    echo -e "${GREEN}✓ 规模 $scale 完成${NC}"
    echo ""
done

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}所有测试完成！${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "结果已保存到: ${YELLOW}$RESULTS_FILE${NC}"
echo ""
echo -e "下一步: 运行 ${YELLOW}python code/plot_results.py${NC} 生成加速比图表"