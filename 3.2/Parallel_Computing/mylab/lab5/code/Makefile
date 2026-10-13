# OpenMP 矩阵乘法实验 Makefile
# 编译器: GCC with -fopenmp, -O3 优化

CC = gcc
CFLAGS = -fopenmp -O3 -Wall -Wextra -march=native
LDFLAGS = -fopenmp -lm

TARGET = gemm_omp
SRC = gemm_omp.c

# 默认目标
all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC) $(LDFLAGS)

# 调试版本
debug: CFLAGS += -g -DDEBUG -O0
debug: clean $(TARGET)

# 清理
clean:
	rm -f $(TARGET) *.o

# 运行快速测试
test: $(TARGET)
	@echo "=== 小规模演示（输出矩阵） ==="
	./$(TARGET) 1 8 static 1
	@echo "=== 性能测试 ==="
	./$(TARGET) 1 512 static 1
	./$(TARGET) 4 512 static 1
	./$(TARGET) 4 512 dynamic 1

.PHONY: all clean debug test