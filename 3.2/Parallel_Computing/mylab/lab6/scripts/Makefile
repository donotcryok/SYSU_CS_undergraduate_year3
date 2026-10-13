# Makefile for Lab6: parallel_for + heated_plate
# ============================================================
# 用法：cd scripts && make
# 所有源文件在 ../src/，编译产物也输出到 ../src/

CC       = gcc
CFLAGS   = -O2 -Wall -Wextra -std=c11
SOFLAGS  = -fPIC -shared
LDFLAGS  = -lpthread -lm
ARFLAGS  = rcs

# OpenMP 版本使用独立编译规则
OMP_CC   = gcc
OMP_CFLAGS = -O2 -Wall -Wextra -std=c11 -fopenmp

# 目录
SRCDIR   = ../src
LIBDIR   = ../src
BINDIR   = ../src

# 目标文件
LIB_SO   = $(LIBDIR)/libparallel_for.so
TEST_BIN = $(BINDIR)/matmul_test
HP_PTH   = $(BINDIR)/heated_plate_pthread
HP_OMP   = $(BINDIR)/heated_plate_openmp
HP_PF    = $(BINDIR)/heated_plate_parallel_for

# 目标
.PHONY: all clean test

all: $(LIB_SO) $(TEST_BIN) $(HP_PTH) $(HP_OMP) $(HP_PF)

# ============================================================
# 动态库
# ============================================================
$(LIB_SO): $(SRCDIR)/parallel_for.c $(SRCDIR)/parallel_for.h
	$(CC) $(CFLAGS) $(SOFLAGS) -o $@ $< $(LDFLAGS)

# ============================================================
# 矩阵乘法测试程序
# ============================================================
$(TEST_BIN): $(SRCDIR)/matmul_test.c $(SRCDIR)/parallel_for.h
	$(CC) $(CFLAGS) -o $@ $< -L$(LIBDIR) -lparallel_for $(LDFLAGS) -Wl,-rpath,$(LIBDIR)

# ============================================================
# 热传导模拟 — Pthreads 版本
# ============================================================
$(HP_PTH): $(SRCDIR)/heated_plate_pthread.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

# ============================================================
# 热传导模拟 — OpenMP 参考版本
# ============================================================
$(HP_OMP): $(SRCDIR)/heated_plate_openmp.c
	$(OMP_CC) $(OMP_CFLAGS) -o $@ $< $(LDFLAGS)

# ============================================================
# 热传导模拟 — parallel_for 版本
# ============================================================
$(HP_PF): $(SRCDIR)/heated_plate_parallel_for.c $(SRCDIR)/parallel_for.h
	$(CC) $(CFLAGS) -o $@ $< -L$(LIBDIR) -lparallel_for $(LDFLAGS) -Wl,-rpath,$(LIBDIR)

# ============================================================
# 清理
# ============================================================
clean:
	rm -f $(LIB_SO) $(TEST_BIN) $(HP_PTH) $(HP_OMP) $(HP_PF) $(SRCDIR)/*.o
