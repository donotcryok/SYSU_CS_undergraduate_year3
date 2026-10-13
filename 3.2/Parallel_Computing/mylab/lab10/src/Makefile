# Makefile — Lab 10: CUDA 并行矩阵乘法
# ================================================================
#
# 编译目标:
#   make all      — 编译所有 BLOCK_SIZE 变体 (8, 16, 32)
#   make run      — 运行完整基准测试 (终端输出)
#   make run-csv  — 运行基准测试并将结果保存到 benchmark_results.csv
#   make clean    — 清理所有编译产物与数据文件
# ================================================================

NVCC       := nvcc
NVCC_FLAGS := -O3 -arch=sm_89
RM         := rm -f

# 矩阵规模采样点 (m, n, k 三方阵)
SIZES := 128 256 512 1024 2048

# Block Size 变体
BLOCK_SIZES := 8 16 32

# Kernel 类型 (0=naive_2d, 1=naive_1d, 2=shared_tiled)
KERNEL_TYPES := 0 1 2

# 计时参数
WARMUP  := 3
REPEAT  := 10

# CSV 输出文件
CSV_FILE := benchmark_results.csv

# ================================================================
# 编译目标
# ================================================================

.PHONY: all clean run run-csv

all: $(foreach bs,$(BLOCK_SIZES),matrixmul_b$(bs))

matrixmul_b%: matrixmul.cu
	$(NVCC) $(NVCC_FLAGS) -DBLOCK_SIZE=$* -o $@ $<

# ================================================================
# 运行目标: 终端输出
# ================================================================

run: all
	@echo "================================================================"
	@echo "  Lab 10: CUDA Matrix Multiplication Benchmark"
	@echo "  Block Sizes: $(BLOCK_SIZES)"
	@echo "  Matrix Sizes: $(SIZES)"
	@echo "  Kernel Types: 0=naive_2d, 1=naive_1d, 2=shared_tiled"
	@echo "================================================================"
	@echo ""
	@echo "m,n,k,kernel_name,block_size,time_ms,verified"
	@for sz in $(SIZES); do \
		for bs in $(BLOCK_SIZES); do \
			for kt in $(KERNEL_TYPES); do \
				./matrixmul_b$$bs $$sz $$sz $$sz $$kt $(WARMUP) $(REPEAT) 2>/dev/null; \
			done; \
		done; \
	done

# ================================================================
# 运行目标: 保存到 CSV 文件
# ================================================================

run-csv: all
	@echo "Running benchmarks, saving to $(CSV_FILE)..."
	@echo "m,n,k,kernel_name,block_size,time_ms,verified" > $(CSV_FILE)
	@for sz in $(SIZES); do \
		for bs in $(BLOCK_SIZES); do \
			for kt in $(KERNEL_TYPES); do \
				./matrixmul_b$$bs $$sz $$sz $$sz $$kt $(WARMUP) $(REPEAT) 2>/dev/null >> $(CSV_FILE); \
			done; \
		done; \
	done
	@echo "Done. Results written to $(CSV_FILE)."
	@wc -l $(CSV_FILE)

# ================================================================
# 快速测试单个配置 (用于调试)
# ================================================================

test: all
	@echo "=== Quick Test: m=128 n=128 k=128, all kernel types ==="
	@for kt in $(KERNEL_TYPES); do \
		./matrixmul_b16 128 128 128 $$kt $(WARMUP) $(REPEAT); \
	done

# ================================================================
# 清理
# ================================================================

clean:
	$(RM) matrixmul_b8 matrixmul_b16 matrixmul_b32
	$(RM) $(CSV_FILE)
	@echo "Cleaned."
