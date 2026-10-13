/**
 * matmul_test.c — 基于 parallel_for 的矩阵乘法验证程序
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <math.h>
#include "parallel_for.h"

/* ------------------------------------------------------------------ */
/*  全局变量（供 functor 访问）                                         */
/* ------------------------------------------------------------------ */
static double *g_A;
static double *g_B;
static double *g_C;
static int     g_m, g_n, g_k;   /* A: m×n, B: n×k, C: m×k */

/* ------------------------------------------------------------------ */
/*  functor：每个线程处理分配到的行 i，完成 C[i][*] 的计算              */
/* ------------------------------------------------------------------ */
static void *matmul_functor(int i, void *arg)
{
    (void)arg;
    double *A = g_A;
    double *B = g_B;
    double *C = g_C;
    int n = g_n;
    int k = g_k;

    /* IKJ 循环顺序：对于行 i，先累计所有 (p,j) 对 */
    for (int p = 0; p < n; p++) {
        double a_ip = A[i * n + p];   /* 寄存器复用 */
        for (int j = 0; j < k; j++) {
            C[i * k + j] += a_ip * B[p * k + j];
        }
    }
    return NULL;
}

/* ------------------------------------------------------------------ */
/*  辅助函数                                                           */
/* ------------------------------------------------------------------ */

/** 初始化矩阵（固定种子保证可重复性） */
static void init_matrix(double *M, int rows, int cols)
{
    for (int i = 0; i < rows * cols; i++) {
        M[i] = (double)((i * 1103515245 + 12345) % 100) / 10.0;
    }
}

/** 串行矩阵乘法（验证基准） */
static void matmul_serial(double *A, double *B, double *C, int m, int n, int k)
{
    memset(C, 0, (size_t)m * k * sizeof(double));
    for (int i = 0; i < m; i++) {
        for (int p = 0; p < n; p++) {
            double a_ip = A[i * n + p];
            for (int j = 0; j < k; j++) {
                C[i * k + j] += a_ip * B[p * k + j];
            }
        }
    }
}

/** 比较两个矩阵，返回最大绝对误差 */
static double compare_matrices(double *C1, double *C2, int m, int k)
{
    double max_err = 0.0;
    for (int i = 0; i < m * k; i++) {
        double err = fabs(C1[i] - C2[i]);
        if (err > max_err) max_err = err;
    }
    return max_err;
}

/** Wall-clock 时间（秒） */
static double get_time_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

/* ------------------------------------------------------------------ */
/*  主函数                                                             */
/* ------------------------------------------------------------------ */
int main(int argc, char *argv[])
{
    int N   = (argc > 1) ? atoi(argv[1]) : 256;
    int thr = (argc > 2) ? atoi(argv[2]) : 1;

    if (N <= 0)   N = 256;
    if (thr <= 0) thr = 1;

    /* 方阵：m=n=k=N */
    int m = N, n = N, k = N;

    printf("=== Matrix Multiplication Test (parallel_for) ===\n");
    printf("  Matrix size: %d x %d x %d\n", m, n, k);
    printf("  Threads:     %d\n", thr);

    size_t size_A = (size_t)m * n * sizeof(double);
    size_t size_B = (size_t)n * k * sizeof(double);
    size_t size_C = (size_t)m * k * sizeof(double);

    double *A = (double *)aligned_alloc(64, size_A);
    double *B = (double *)aligned_alloc(64, size_B);
    double *C_par = (double *)aligned_alloc(64, size_C);
    double *C_ref = (double *)aligned_alloc(64, size_C);

    if (!A || !B || !C_par || !C_ref) {
        fprintf(stderr, "Memory allocation failed\n");
        return 1;
    }

    init_matrix(A, m, n);
    init_matrix(B, n, k);

    /* 串行基准 */
    double t0 = get_time_sec();
    matmul_serial(A, B, C_ref, m, n, k);
    double t_ref = get_time_sec() - t0;

    /* 并行版本 */
    memset(C_par, 0, size_C);
    g_A = A; g_B = B; g_C = C_par;
    g_m = m; g_n = n; g_k = k;

    double t1 = get_time_sec();
    parallel_for(0, m, 1, matmul_functor, NULL, thr);
    double t_par = get_time_sec() - t1;

    /* 验证 */
    double max_err = compare_matrices(C_par, C_ref, m, k);
    printf("\n  Serial time:      %.6f s\n", t_ref);
    printf("  Parallel time:    %.6f s\n", t_par);
    printf("  Speedup:          %.4f x\n", t_ref / t_par);
    printf("  Max error:        %e\n", max_err);
    printf("  Verification:     %s\n", (max_err < 1e-10) ? "PASSED" : "FAILED");

    /* 小规模输出前几个元素 */
    if (N <= 8) {
        printf("\n  C (first 8x8):\n");
        for (int i = 0; i < N && i < 8; i++) {
            printf("  ");
            for (int j = 0; j < N && j < 8; j++) {
                printf("%8.2f ", C_par[i * k + j]);
            }
            printf("\n");
        }
    }

    free(A); free(B); free(C_par); free(C_ref);
    parallel_for_cleanup();
    return (max_err < 1e-10) ? 0 : 1;
}
