/**
 * 策略说明:
 *   0 (Row-wise): 按行块划分 - 每个线程负责结果矩阵C的若干行
 *   1 (Column-wise): 按列块划分 - 每个线程负责结果矩阵C的若干列
 *   2 (Block-wise): 2D块划分 - 线程网格化，每个线程负责一个子方块
 */

#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
#include <math.h>

// 策略常量
#define STRATEGY_ROW_WISE     0
#define STRATEGY_COLUMN_WISE  1
#define STRATEGY_BLOCK_WISE   2

// 策略名称
const char* strategy_names[] = {"Row-wise", "Column-wise", "Block-wise"};

// 全局矩阵
double *A = NULL;
double *B = NULL;
double *C = NULL;
int M, N, K;

// 线程参数结构体
typedef struct {
    int thread_id;
    int num_threads;
    int strategy;
    // Row-wise 参数
    int start_row;
    int end_row;
    // Column-wise 参数
    int start_col;
    int end_col;
    // Block-wise 参数
    int block_row;
    int block_col;
    int num_block_rows;
    int num_block_cols;
} ThreadArg;

// 获取当前时间（秒）
double get_time() {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

// 策略0：按行划分（Row-wise）
void* matrix_multiply_row_wise(void *arg) {
    ThreadArg *params = (ThreadArg *)arg;
    
    int start_row = params->start_row;
    int end_row = params->end_row;
    
    // 执行矩阵乘法：C[i][j] = sum(A[i][l] * B[l][j])
    for (int i = start_row; i < end_row; i++) {
        for (int j = 0; j < K; j++) {
            double sum = 0.0;
            for (int l = 0; l < N; l++) {
                sum += A[i * N + l] * B[l * K + j];
            }
            C[i * K + j] = sum;
        }
    }
    
    pthread_exit(NULL);
    return NULL;
}

// 策略1：按列划分（Column-wise）
void* matrix_multiply_column_wise(void *arg) {
    ThreadArg *params = (ThreadArg *)arg;
    
    int start_col = params->start_col;
    int end_col = params->end_col;
    
    // 执行矩阵乘法：C[i][j] = sum(A[i][l] * B[l][j])
    // 注意：按列划分时，每个线程负责若干列
    // 这会导致对矩阵A的跨行访问，Cache命中率低
    for (int j = start_col; j < end_col; j++) {
        for (int i = 0; i < M; i++) {
            double sum = 0.0;
            for (int l = 0; l < N; l++) {
                sum += A[i * N + l] * B[l * K + j];
            }
            C[i * K + j] = sum;
        }
    }
    
    pthread_exit(NULL);
    return NULL;
}

// 策略2：2D块划分（Block-wise）
void* matrix_multiply_block_wise(void *arg) {
    ThreadArg *params = (ThreadArg *)arg;
    
    int num_block_rows = params->num_block_rows;
    int num_block_cols = params->num_block_cols;
    int block_row = params->block_row;
    int block_col = params->block_col;
    
    // 计算每个块的行数和列数
    int rows_per_block = M / num_block_rows;
    int cols_per_block = K / num_block_cols;
    int row_remainder = M % num_block_rows;
    int col_remainder = K % num_block_cols;
    
    // 计算当前块的起始和结束行
    int start_row, end_row;
    if (block_row < row_remainder) {
        start_row = block_row * (rows_per_block + 1);
        end_row = start_row + rows_per_block + 1;
    } else {
        start_row = row_remainder * (rows_per_block + 1) + (block_row - row_remainder) * rows_per_block;
        end_row = start_row + rows_per_block;
    }
    
    // 计算当前块的起始和结束列
    int start_col, end_col;
    if (block_col < col_remainder) {
        start_col = block_col * (cols_per_block + 1);
        end_col = start_col + cols_per_block + 1;
    } else {
        start_col = col_remainder * (cols_per_block + 1) + (block_col - col_remainder) * cols_per_block;
        end_col = start_col + cols_per_block;
    }
    
    // 执行矩阵乘法：计算当前块的C[i][j]
    for (int i = start_row; i < end_row; i++) {
        for (int j = start_col; j < end_col; j++) {
            double sum = 0.0;
            for (int l = 0; l < N; l++) {
                sum += A[i * N + l] * B[l * K + j];
            }
            C[i * K + j] = sum;
        }
    }
    
    pthread_exit(NULL);
    return NULL;
}

// 线程函数入口 - 根据策略选择不同实现
void* matrix_multiply_thread(void *arg) {
    ThreadArg *params = (ThreadArg *)arg;
    
    switch (params->strategy) {
        case STRATEGY_ROW_WISE:
            return matrix_multiply_row_wise(arg);
        case STRATEGY_COLUMN_WISE:
            return matrix_multiply_column_wise(arg);
        case STRATEGY_BLOCK_WISE:
            return matrix_multiply_block_wise(arg);
        default:
            return matrix_multiply_row_wise(arg);
    }
}

// 设置 Row-wise 策略的线程参数
void setup_row_wise_args(ThreadArg *args, int num_threads) {
    int rows_per_thread = M / num_threads;
    int remainder = M % num_threads;
    int current_start = 0;
    
    for (int i = 0; i < num_threads; i++) {
        args[i].thread_id = i;
        args[i].num_threads = num_threads;
        args[i].strategy = STRATEGY_ROW_WISE;
        
        int my_rows = rows_per_thread + (i < remainder ? 1 : 0);
        args[i].start_row = current_start;
        args[i].end_row = current_start + my_rows;
        current_start = args[i].end_row;
    }
}

// 设置 Column-wise 策略的线程参数
void setup_column_wise_args(ThreadArg *args, int num_threads) {
    int cols_per_thread = K / num_threads;
    int remainder = K % num_threads;
    int current_start = 0;
    
    for (int i = 0; i < num_threads; i++) {
        args[i].thread_id = i;
        args[i].num_threads = num_threads;
        args[i].strategy = STRATEGY_COLUMN_WISE;
        
        int my_cols = cols_per_thread + (i < remainder ? 1 : 0);
        args[i].start_col = current_start;
        args[i].end_col = current_start + my_cols;
        current_start = args[i].end_col;
    }
}

// 设置 Block-wise 策略的线程参数
void setup_block_wise_args(ThreadArg *args, int num_threads) {
    // 计算最佳的块网格
    int num_block_rows = (int)sqrt((double)num_threads);
    int num_block_cols = num_threads / num_block_rows;
    
    // 调整以尽可能利用所有线程
    while (num_block_rows * num_block_cols < num_threads) {
        num_block_cols++;
    }
    
    // 如果仍然不够，调整行数
    if (num_block_rows * num_block_cols < num_threads) {
        num_block_rows = num_threads / num_block_cols;
        if (num_block_rows * num_block_cols < num_threads) {
            num_block_rows++;
        }
    }
    
    int thread_idx = 0;
    for (int br = 0; br < num_block_rows && thread_idx < num_threads; br++) {
        for (int bc = 0; bc < num_block_cols && thread_idx < num_threads; bc++) {
            args[thread_idx].thread_id = thread_idx;
            args[thread_idx].num_threads = num_threads;
            args[thread_idx].strategy = STRATEGY_BLOCK_WISE;
            args[thread_idx].block_row = br;
            args[thread_idx].block_col = bc;
            args[thread_idx].num_block_rows = num_block_rows;
            args[thread_idx].num_block_cols = num_block_cols;
            thread_idx++;
        }
    }
    
    // 剩余线程（如果有）处理空块
    while (thread_idx < num_threads) {
        args[thread_idx].thread_id = thread_idx;
        args[thread_idx].num_threads = num_threads;
        args[thread_idx].strategy = STRATEGY_BLOCK_WISE;
        args[thread_idx].block_row = 0;
        args[thread_idx].block_col = 0;
        args[thread_idx].num_block_rows = num_block_rows;
        args[thread_idx].num_block_cols = num_block_cols;
        // 这些线程实际上不计算任何内容（空块）
        args[thread_idx].start_row = M;
        args[thread_idx].end_row = M;
        thread_idx++;
    }
}

int main(int argc, char *argv[]) {
    // 参数检查
    if (argc != 6) {
        fprintf(stderr, "Usage: %s m n k num_threads strategy\n", argv[0]);
        fprintf(stderr, "  m: rows of matrix A\n");
        fprintf(stderr, "  n: columns of matrix A / rows of matrix B\n");
        fprintf(stderr, "  k: columns of matrix B\n");
        fprintf(stderr, "  num_threads: number of threads (1-16)\n");
        fprintf(stderr, "  strategy: 0=Row-wise, 1=Column-wise, 2=Block-wise\n");
        return 1;
    }
    
    // 解析命令行参数
    M = atoi(argv[1]);
    N = atoi(argv[2]);
    K = atoi(argv[3]);
    int num_threads = atoi(argv[4]);
    int strategy = atoi(argv[5]);
    
    // 参数有效性检查
    if (M <= 0 || N <= 0 || K <= 0) {
        fprintf(stderr, "Error: Matrix dimensions must be positive integers\n");
        return 1;
    }
    if (num_threads < 1 || num_threads > 16) {
        fprintf(stderr, "Error: Number of threads must be between 1 and 16\n");
        return 1;
    }
    if (strategy < 0 || strategy > 2) {
        fprintf(stderr, "Error: Strategy must be 0, 1, or 2\n");
        return 1;
    }
    
    // 动态分配矩阵内存
    A = (double *)malloc(M * N * sizeof(double));
    B = (double *)malloc(N * K * sizeof(double));
    C = (double *)malloc(M * K * sizeof(double));
    
    if (!A || !B || !C) {
        fprintf(stderr, "Error: Memory allocation failed\n");
        free(A);
        free(B);
        free(C);
        return 1;
    }
    
    // 初始化矩阵A和B（使用固定种子保证可重复性）
    srand(42);
    for (int i = 0; i < M * N; i++) {
        A[i] = (double)(rand() % 100) / 10.0;
    }
    for (int i = 0; i < N * K; i++) {
        B[i] = (double)(rand() % 100) / 10.0;
    }
    
    // 创建线程和参数数组
    pthread_t *threads = (pthread_t *)malloc(num_threads * sizeof(pthread_t));
    ThreadArg *thread_args = (ThreadArg *)malloc(num_threads * sizeof(ThreadArg));
    
    if (!threads || !thread_args) {
        fprintf(stderr, "Error: Thread allocation failed\n");
        free(A);
        free(B);
        free(C);
        free(threads);
        free(thread_args);
        return 1;
    }
    
    // 根据策略设置线程参数
    switch (strategy) {
        case STRATEGY_ROW_WISE:
            setup_row_wise_args(thread_args, num_threads);
            break;
        case STRATEGY_COLUMN_WISE:
            setup_column_wise_args(thread_args, num_threads);
            break;
        case STRATEGY_BLOCK_WISE:
            setup_block_wise_args(thread_args, num_threads);
            break;
        default:
            setup_row_wise_args(thread_args, num_threads);
            break;
    }
    
    // 开始计时
    double start_time = get_time();
    
    // 创建并启动线程
    for (int i = 0; i < num_threads; i++) {
        int rc = pthread_create(&threads[i], NULL, matrix_multiply_thread, &thread_args[i]);
        if (rc) {
            fprintf(stderr, "Error: Failed to create thread %d, return code %d\n", i, rc);
            free(A);
            free(B);
            free(C);
            free(threads);
            free(thread_args);
            return 1;
        }
    }
    
    // 等待所有线程完成
    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // 结束计时
    double end_time = get_time();
    double elapsed = end_time - start_time;
    
    // 输出结果（指定格式）
    printf("Strategy: %s, Size: %d x %d x %d, Threads: %d, Time: %.6f s\n", 
           strategy_names[strategy], M, N, K, num_threads, elapsed);
    
    // 释放内存
    free(A);
    free(B);
    free(C);
    free(threads);
    free(thread_args);
    
    return 0;
}