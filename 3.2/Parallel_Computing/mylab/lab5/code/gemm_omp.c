/**
 * OpenMP 并行矩阵乘法 (GEMM)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <omp.h>
#include <sys/time.h>
#include <errno.h>

// 默认参数
#define DEFAULT_THREADS 4
#define DEFAULT_SIZE 1024
#define DEFAULT_SCHEDULE "static"

// 矩阵初始化
void init_matrix(double *A, int rows, int cols, int seed) {
    unsigned int state = seed;
    for (int i = 0; i < rows * cols; i++) {
        A[i] = (double)(rand_r(&state) % 100) / 10.0;
    }
}

// 验证结果正确性
int verify_result(double *C, double *C_ref, int size) {
    const double eps = 1e-6;
    for (int i = 0; i < size * size; i++) {
        if (fabs(C[i] - C_ref[i]) > eps * (1.0 + fabs(C_ref[i]))) {
            printf("  不匹配: C[%d]=%.10f, C_ref[%d]=%.10f\n", i, C[i], i, C_ref[i]);
            return 0;
        }
    }
    return 1;
}

// 串行矩阵乘法（IJK 顺序，用于验证基准）
void gemm_serial(double *A, double *B, double *C, int m, int n, int k) {
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < k; j++) {
            double sum = 0.0;
            for (int p = 0; p < n; p++) {
                sum += A[i * n + p] * B[p * k + j];
            }
            C[i * k + j] = sum;
        }
    }
}

/**
 * OpenMP 并行矩阵乘法 - IKJ 循环顺序
 *
 * 优化点：
 * 1. IKJ 顺序：内层 j 循环对 B[p*k+j] 和 C[i*k+j] 均为连续访问（行主序），
 *    充分利用 Cache Line，减少 Cache Miss
 * 2. A[i*n+p] 在 p 固定时广播到寄存器 (a_ip)，在内层 j 循环中复用 n 次
 * 3. 使用 schedule(runtime) 配合 omp_set_schedule() 实现运行时调度选择
 * 4. 仅并行化外层 i 循环（因为 p 循环存在对 C[i][j] 的累加依赖）
 */
void gemm_omp(double *A, double *B, double *C, int m, int n, int k) {
    /* 清零 C 矩阵（IKJ 顺序需要先清零再累加） */
    memset(C, 0, (size_t)m * k * sizeof(double));

    /* IKJ 循环顺序并行计算 */
    #pragma omp parallel for schedule(runtime)
    for (int i = 0; i < m; i++) {
        for (int p = 0; p < n; p++) {
            double a_ip = A[i * n + p];   /* 广播到寄存器，j 循环复用 */
            for (int j = 0; j < k; j++) {
                C[i * k + j] += a_ip * B[p * k + j];
            }
        }
    }
}

/**
 * 分块矩阵乘法 (Blocked GEMM)
 * 将矩阵划分为 block_size × block_size 的子块，提升 Cache 命中率
 * 适合大规模矩阵，使工作集适配 L2/L3 Cache
 */
void gemm_omp_blocked(double *A, double *B, double *C, int m, int n, int k, int block_size) {
    memset(C, 0, (size_t)m * k * sizeof(double));

    #pragma omp parallel for schedule(runtime)
    for (int ii = 0; ii < m; ii += block_size) {
        for (int jj = 0; jj < k; jj += block_size) {
            for (int kk = 0; kk < n; kk += block_size) {
                /* 处理当前 (ii,jj,kk) 子块 */
                int i_end = (ii + block_size < m) ? ii + block_size : m;
                int j_end = (jj + block_size < k) ? jj + block_size : k;
                int k_end = (kk + block_size < n) ? kk + block_size : n;

                for (int i = ii; i < i_end; i++) {
                    for (int p = kk; p < k_end; p++) {
                        double a_ip = A[i * n + p];
                        for (int j = jj; j < j_end; j++) {
                            C[i * k + j] += a_ip * B[p * k + j];
                        }
                    }
                }
            }
        }
    }
}

// 打印矩阵（仅小规模时使用）
void print_matrix(const char *name, double *M, int rows, int cols) {
    printf("矩阵 %s (%dx%d):\n", name, rows, cols);
    int print_rows = (rows > 8) ? 8 : rows;
    int print_cols = (cols > 8) ? 8 : cols;
    for (int i = 0; i < print_rows; i++) {
        for (int j = 0; j < print_cols; j++) {
            printf("%8.2f ", M[i * cols + j]);
        }
        if (cols > 8) printf("...");
        printf("\n");
    }
    if (rows > 8) printf("... (省略 %d 行)\n", rows - 8);
    printf("\n");
}

// 获取时间（毫秒）
double get_time_ms() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec * 1000.0 + tv.tv_usec / 1000.0;
}

// 打印帮助信息
void print_usage(const char *prog) {
    printf("用法: %s [threads] [size] [schedule] [verify] [blocked]\n", prog);
    printf("  threads:  线程数 (1-16), 默认 %d\n", DEFAULT_THREADS);
    printf("  size:     矩阵规模 (4-2048), 默认 %d\n", DEFAULT_SIZE);
    printf("  schedule: 调度模式 (static|dynamic|guided), 默认 %s\n", DEFAULT_SCHEDULE);
    printf("  verify:   是否验证结果 (0|1), 默认 0\n");
    printf("  blocked:  是否使用分块优化 (0|1), 默认 0\n");
    printf("\n示例:\n");
    printf("  %s 4 1024 static 1    # 4线程，1024规模，static调度，验证结果\n", prog);
    printf("  %s 8 2048 dynamic 0 1 # 8线程，2048规模，dynamic调度，使用分块\n", prog);
}

int main(int argc, char *argv[]) {
    int threads = DEFAULT_THREADS;
    int size = DEFAULT_SIZE;
    char *schedule_str = DEFAULT_SCHEDULE;
    int verify = 0;
    int blocked = 0;

    /* 参数解析 */
    if (argc > 1) {
        threads = atoi(argv[1]);
        if (threads < 1 || threads > 16) {
            fprintf(stderr, "错误: 线程数必须在 1-16 范围内\n");
            print_usage(argv[0]);
            return 1;
        }
    }
    if (argc > 2) {
        size = atoi(argv[2]);
        if (size < 4 || size > 2048) {
            fprintf(stderr, "错误: 矩阵规模必须在 4-2048 范围内\n");
            print_usage(argv[0]);
            return 1;
        }
    }
    if (argc > 3) {
        schedule_str = argv[3];
    }
    if (argc > 4) {
        verify = atoi(argv[4]);
    }
    if (argc > 5) {
        blocked = atoi(argv[5]);
    }

    /* 设置 OpenMP 调度类型 */
    omp_sched_t sched;
    if (strcmp(schedule_str, "static") == 0) {
        sched = omp_sched_static;
    } else if (strcmp(schedule_str, "dynamic") == 0) {
        sched = omp_sched_dynamic;
    } else if (strcmp(schedule_str, "guided") == 0) {
        sched = omp_sched_guided;
    } else {
        fprintf(stderr, "错误: 不支持的调度模式 '%s'\n", schedule_str);
        print_usage(argv[0]);
        return 1;
    }

    /* 设置 OpenMP 运行时参数 */
    omp_set_num_threads(threads);
    omp_set_schedule(sched, 0);   /* chunk=0 表示使用默认块大小 */

    /* 输出配置信息 */
    printf("=== OpenMP 矩阵乘法基准测试 ===\n");
    printf("矩阵规模: %dx%d\n", size, size);
    printf("线程数: %d\n", threads);
    printf("调度模式: %s\n", schedule_str);
    printf("分块优化: %s\n", blocked ? "启用" : "禁用");
    printf("验证结果: %s\n", verify ? "启用" : "禁用");
    printf("==============================\n\n");

    /* 分配矩阵内存（64 字节对齐，匹配 Cache Line） */
    double *A = (double *)aligned_alloc(64, (size_t)size * size * sizeof(double));
    double *B = (double *)aligned_alloc(64, (size_t)size * size * sizeof(double));
    double *C = (double *)aligned_alloc(64, (size_t)size * size * sizeof(double));
    double *C_ref = NULL;

    if (!A || !B || !C) {
        fprintf(stderr, "错误: 内存分配失败\n");
        free(A);
        free(B);
        free(C);
        free(C_ref);
        return 1;
    }

    /* 初始化矩阵 */
    init_matrix(A, size, size, 42);
    init_matrix(B, size, size, 123);

    if (verify) {
        C_ref = (double *)aligned_alloc(64, (size_t)size * size * sizeof(double));
        if (!C_ref) {
            fprintf(stderr, "错误: C_ref 内存分配失败\n");
            free(A); free(B); free(C);
            return 1;
        }
        gemm_serial(A, B, C_ref, size, size, size);
    }

    /* 运行并行计算 */
    double t_start = get_time_ms();

    if (blocked) {
        int block_size = (size < 512) ? 32 : 64;
        gemm_omp_blocked(A, B, C, size, size, size, block_size);
    } else {
        gemm_omp(A, B, C, size, size, size);
    }

    double t_end = get_time_ms();
    double elapsed = t_end - t_start;

    /* 计算性能指标
     * GFLOPS = (2 * m * n * k) / (time_seconds * 1e9)
     * elapsed 为毫秒，故除以 1e6 */
    double gflops = (2.0 * size * size * size) / (elapsed * 1e6);

    printf("计算时间: %.3f ms\n", elapsed);
    printf("性能: %.3f GFLOPS\n", gflops);

    /* 小规模矩阵输出完整内容，大规模矩阵仅输出摘要 */
    if (size <= 16) {
        print_matrix("A", A, size, size);
        print_matrix("B", B, size, size);
        print_matrix("C", C, size, size);
    } else {
        printf("\n(矩阵规模 %dx%d 较大，省略完整输出。以下为各矩阵前 8×8 子块：)\n\n", size, size);
        print_matrix("A (前8×8)", A, size, size);
        print_matrix("B (前8×8)", B, size, size);
        print_matrix("C (前8×8)", C, size, size);
    }

    if (verify && C_ref) {
        int correct = verify_result(C, C_ref, size);
        printf("结果验证: %s\n", correct ? "通过" : "失败");
    }

    /* 释放内存 */
    free(A);
    free(B);
    free(C);
    free(C_ref);

    return 0;
}
