/*
 * V2: C 语言基础版本 (i-j-k 循环顺序)
 * 最基础的矩阵乘法实现，作为 C 语言性能基准
 */

#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <time.h>

// 动态分配二维数组
double** allocate_matrix(int N) {
    double** matrix = (double**)malloc(N * sizeof(double*));
    for (int i = 0; i < N; i++) {
        matrix[i] = (double*)malloc(N * sizeof(double));
    }
    return matrix;
}

// 释放二维数组
void free_matrix(double** matrix, int N) {
    for (int i = 0; i < N; i++) {
        free(matrix[i]);
    }
    free(matrix);
}

// 初始化矩阵为随机值
void init_matrix(double** matrix, int N) {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            matrix[i][j] = (double)rand() / RAND_MAX;
        }
    }
}

// i-j-k 循环顺序的矩阵乘法
void matrix_mult_ijk(double** A, double** B, double** C, int N) {
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            double sum = 0.0;
            for (int k = 0; k < N; k++) {
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }
}

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
    
    // 分配矩阵内存
    double** A = allocate_matrix(N);
    double** B = allocate_matrix(N);
    double** C = allocate_matrix(N);
    
    // 初始化矩阵
    init_matrix(A, N);
    init_matrix(B, N);
    
    // 初始化结果矩阵为 0
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            C[i][j] = 0.0;
        }
    }
    
    // 计时开始
    struct timeval start, end;
    gettimeofday(&start, NULL);
    
    // 执行矩阵乘法
    matrix_mult_ijk(A, B, C, N);
    
    // 计时结束
    gettimeofday(&end, NULL);
    
    // 计算运行时间
    double elapsed_time = (end.tv_sec - start.tv_sec) + 
                          (end.tv_usec - start.tv_usec) / 1e6;
    
    // 计算性能指标
    long flops = 2L * N * N * N;
    double gflops = flops / (elapsed_time * 1e9);
    
    printf("\n========== V2: C 语言基础版本 (i-j-k) 结果 ==========\n");
    printf("矩阵大小: %d x %d\n", N, N);
    printf("运行时间: %.6f 秒\n", elapsed_time);
    printf("GFLOPS: %.4f\n", gflops);
    printf("==================================================\n");
    
    // 释放内存
    free_matrix(A, N);
    free_matrix(B, N);
    free_matrix(C, N);
    
    return 0;
}