/**
 * MPI 并行矩阵乘法 (MPI-v1)
 * 使用点对点通信 (MPI_Send, MPI_Recv) 实现
 * 采用行块划分策略 (Row-wise block distribution)
 * 
 * 编译: mpicc -o mpi_v1 mpi_v1.c -O2
 * 运行: mpirun -n <procs> ./mpi_v1 <matrix_size>
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <mpi.h>

// 矩阵分配函数
double* allocate_matrix(int rows, int cols) {
    double *matrix = (double*)malloc(rows * cols * sizeof(double));
    if (matrix == NULL) {
        fprintf(stderr, "Error: Failed to allocate matrix memory\n");
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
    return matrix;
}

// 矩阵初始化函数 (使用固定种子保证可重复性)
void init_matrix(double *matrix, int rows, int cols, int seed) {
    srand(seed);
    for (int i = 0; i < rows * cols; i++) {
        matrix[i] = (double)(rand() % 100) / 10.0;
    }
}

// 矩阵乘法核心计算 (C = A * B)
void matrix_multiply(double *A, double *B, double *C, 
                     int rows_A, int cols_A, int cols_B) {
    for (int i = 0; i < rows_A; i++) {
        for (int j = 0; j < cols_B; j++) {
            double sum = 0.0;
            for (int k = 0; k < cols_A; k++) {
                sum += A[i * cols_A + k] * B[k * cols_B + j];
            }
            C[i * cols_B + j] = sum;
        }
    }
}

// 验证结果正确性 (与串行计算结果比较)
int verify_result(double *C, double *A, double *B, 
                  int rows_A, int cols_A, int cols_B, int start_row) {
    int errors = 0;
    double tolerance = 1e-6;
    
    for (int i = 0; i < rows_A && errors < 10; i++) {
        for (int j = 0; j < cols_B && errors < 10; j++) {
            double sum = 0.0;
            for (int k = 0; k < cols_A; k++) {
                sum += A[i * cols_A + k] * B[k * cols_B + j];
            }
            if (fabs(C[i * cols_B + j] - sum) > tolerance) {
                errors++;
                if (errors <= 3) {
                    printf("Error at C[%d][%d]: expected %.6f, got %.6f\n",
                           start_row + i, j, sum, C[i * cols_B + j]);
                }
            }
        }
    }
    return errors;
}

int main(int argc, char *argv[]) {
    int rank, size;
    int N = 1024;  // 默认矩阵规模
    
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    
    // 解析命令行参数
    if (argc >= 2) {
        N = atoi(argv[1]);
        if (N <= 0) {
            if (rank == 0) {
                fprintf(stderr, "Error: Matrix size must be positive\n");
            }
            MPI_Finalize();
            return 1;
        }
    }
    
    // 检查矩阵规模是否能被进程数整除
    if (N % size != 0) {
        if (rank == 0) {
            fprintf(stderr, "Error: Matrix size %d cannot be evenly divided by %d processes\n", N, size);
        }
        MPI_Finalize();
        return 1;
    }
    
    int rows_per_proc = N / size;  // 每个进程分配的行数
    
    double *A = NULL;      // 完整矩阵 A (仅 Root 持有)
    double *B = NULL;      // 完整矩阵 B (所有进程都需要)
    double *C = NULL;      // 完整结果矩阵 C (仅 Root 持有)
    double *local_A = NULL;  // 本地 A 的行块
    double *local_C = NULL;  // 本地 C 的行块
    
    double start_time, end_time;
    
    // ==================== Root 进程初始化 ====================
    if (rank == 0) {
        A = allocate_matrix(N, N);
        B = allocate_matrix(N, N);
        C = allocate_matrix(N, N);
        
        // 初始化矩阵 (使用固定种子)
        init_matrix(A, N, N, 42);
        init_matrix(B, N, N, 43);
        
        printf("Matrix multiplication: N=%d, Processes=%d\n", N, size);
        start_time = MPI_Wtime();
    }
    
    // ==================== 分发矩阵 B (所有进程都需要) ====================
    B = allocate_matrix(N, N);
    
    if (rank == 0) {
        // Root 发送 B 给所有其他进程
        for (int p = 1; p < size; p++) {
            MPI_Send(B, N * N, MPI_DOUBLE, p, 0, MPI_COMM_WORLD);
        }
    } else {
        // 其他进程接收 B
        MPI_Recv(B, N * N, MPI_DOUBLE, 0, 0, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    }
    
    // ==================== 分发矩阵 A 的行块 ====================
    local_A = allocate_matrix(rows_per_proc, N);
    local_C = allocate_matrix(rows_per_proc, N);
    
    if (rank == 0) {
        // Root 保留自己的行块
        memcpy(local_A, A, rows_per_proc * N * sizeof(double));
        
        // 发送其他行块给其他进程
        for (int p = 1; p < size; p++) {
            int start_row = p * rows_per_proc;
            MPI_Send(&A[start_row * N], rows_per_proc * N, MPI_DOUBLE, 
                     p, 1, MPI_COMM_WORLD);
        }
    } else {
        // 其他进程接收 A 的行块
        MPI_Recv(local_A, rows_per_proc * N, MPI_DOUBLE, 0, 1, 
                 MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    }
    
    // ==================== 本地矩阵乘法计算 ====================
    matrix_multiply(local_A, B, local_C, rows_per_proc, N, N);
    
    // ==================== 收集结果到 Root ====================
    if (rank == 0) {
        // Root 复制自己的结果
        memcpy(C, local_C, rows_per_proc * N * sizeof(double));
        
        // 接收其他进程的结果
        for (int p = 1; p < size; p++) {
            int start_row = p * rows_per_proc;
            MPI_Recv(&C[start_row * N], rows_per_proc * N, MPI_DOUBLE, 
                     p, 2, MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
        
        end_time = MPI_Wtime();
        
        printf("Size: %d, Procs: %d, Time: %.4f s\n", N, size, end_time - start_time);
        
    } else {
        // 其他进程发送结果给 Root
        MPI_Send(local_C, rows_per_proc * N, MPI_DOUBLE, 0, 2, MPI_COMM_WORLD);
    }
    
    // ==================== 内存释放 ====================
    free(local_A);
    free(local_C);
    free(B);
    
    if (rank == 0) {
        free(A);
        free(C);
    }
    
    MPI_Finalize();
    return 0;
}