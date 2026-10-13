# Makefile for Lab 11: CUDA 卷积神经网络算子实验
# ================================================================

NVCC       = /usr/bin/nvcc
NVCC_FLAGS = -O3 -arch=sm_89 -ccbin /usr/bin/gcc-12
LDFLAGS    = -lcudnn

TARGET     = convolution
SRC        = convolution.cu
CSV_FILE   = benchmark_results.csv

.PHONY: all clean run-csv run-all plot

all: $(TARGET)

$(TARGET): $(SRC)
	$(NVCC) $(NVCC_FLAGS) -o $@ $< $(LDFLAGS)

# 运行全量基准测试 (5 尺寸 × 3 Stride = 15 组)
run-csv: $(TARGET)
	@rm -f $(CSV_FILE)
	@echo "============================================"
	@echo "  Running Full Benchmark Suite"
	@echo "============================================"
	@for SZ in 32 64 128 256 512; do \
		for ST in 1 2 3; do \
			echo ""; \
			echo ">>> Size=$${SZ}, Stride=$${ST} <<<"; \
			./$(TARGET) $${SZ} $${ST} $(CSV_FILE); \
		done; \
	done
	@echo ""
	@echo "Benchmark complete. Results in $(CSV_FILE)"
	@cat $(CSV_FILE)

# 快捷运行单个测试
run32s1:  $(TARGET); ./$(TARGET) 32 1
run64s1:  $(TARGET); ./$(TARGET) 64 1
run128s1: $(TARGET); ./$(TARGET) 128 1
run256s1: $(TARGET); ./$(TARGET) 256 1
run512s1: $(TARGET); ./$(TARGET) 512 1

clean:
	rm -f $(TARGET) $(CSV_FILE)
