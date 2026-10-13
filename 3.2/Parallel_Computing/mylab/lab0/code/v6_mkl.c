/*
 * V6: Intel MKL 库版本
 * 使用 Intel Math Kernel Library 的 cblas_dgemm 函数
 * 
 * MKL 是 Intel 提供的高度优化的数学库，包含：
 * - 针对Intel CPU优化的BLAS例程
 * - 自动向量化
 * - 多线程并行
 * - Cache优化
 * 
 * 编译命令（需要先设置MKL环境）：
 * source /opt/intel/oneapi/mkl/latest/env/vars.sh intel64 ilp64
 * gcc -o v6_mkl v6_mkl.c -lmkl_rt
 * 
 * 或使用静态链接：
 * gcc -o v6_mkl v6_mkl.c -lmkl_intel_ilp64 -lmkl_sequential -lmkl_core -lpthread -lm -ldl
 */

#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <time.h>
#include "mkl.h"

int main(int argc, char* argv[]) {
    int N;
    
    // 设置随机种子
    srand(42);
    
    // 如果命令行指定了矩阵大小，使用命令行参数
    if (argc > 1) {
        N = atoi(argv[1]);
    } else {
        // 随机生成 512-2048 之间的矩阵大小
        N = 512 + rand() % (2048 - 512 + 1);
    }
    
    printf("矩阵大小: N = %d\n", N);
    printf("浮点运算次数: 2 * %d^3 = %ld\n", N, 2L * N * N * N);
    
    // 使用 MKL 优化的内存分配
    double* A = (double*)mkl_malloc(N * N * sizeof(double), 64);
    double* B = (double*)mkl_malloc(N * N * sizeof(double), 64);
    double* C = (double*)mkl_malloc(N * N * sizeof(double), 64);
    
    if (A == NULL || B == NULL || C == NULL) {
        printf("内存分配失败!\n");
        return 1;
    }
    
    // 初始化矩阵（使用行优先存储）
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            A[i * N + j] = (double)rand() / RAND_MAX;
            B[i * N + j] = (double)rand() / RAND_MAX;
            C[i * N + j] = 0.0;
        }
    }
    
    // 计时开始
    struct timeval start, end;
    gettimeofday(&start, NULL);
    
    // 使用 cblas_dgemm 进行矩阵乘法
    // C = alpha * A * B + beta * C
    // 参数说明：
    // CblasRowMajor: 行优先存储
    // CblasNoTrans: A 不转置
    // CblasNoTrans: B 不转置
    // N, N, N: 矩阵维度
    // alpha: 缩放因子
    // A, N: A 矩阵和其 leading dimension
    // B, N: B 矩阵和其 leading dimension
    // beta: 缩放因子
    // C, N: C 矩阵和其 leading dimension
    double alpha = 1.0;
    double beta = 0.0;
    
    cblas_dgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans,
                N, N, N, alpha, A, N, B, N, beta, C, N);
    
    // 计时结束
    gettimeofday(&end, NULL);
    
    // 计算运行时间
    double elapsed_time = (end.tv_sec - start.tv_sec) + 
                          (end.tv_usec - start.tv_usec) / 1e6;
    
    // 计算性能指标
    long flops = 2L * N * N * N;
    double gflops = flops / (elapsed_time * 1e9);
    
    printf("\n========== V6: Intel MKL 库版本 结果 ==========\n");
    printf("矩阵大小: %d x %d\n", N, N);
    printf("运行时间: %.6f 秒\n", elapsed_time);
    printf("GFLOPS: %.4f\n", gflops);
    printf("============================================\n");
    
    // 释放内存
    mkl_free(A);
    mkl_free(B);
    mkl_free(C);
    
    return 0;
}