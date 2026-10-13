/**
 * MPI并行矩阵乘法 - 进阶版 
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <mpi.h>

// 定义控制参数结构体
typedef struct {
    int m;              // 矩阵A的行数
    int n;              // 矩阵A的列数 / 矩阵B的行数
    int k;              // 矩阵B的列数
    int total_procs;    // 总进程数
} ControlParams;

// 创建MPI结构体数据类型
MPI_Datatype create_control_params_type() {
    MPI_Datatype mpi_type;
    int blocklengths[4] = {1, 1, 1, 1};
    MPI_Datatype types[4] = {MPI_INT, MPI_INT, MPI_INT, MPI_INT};
    MPI_Aint offsets[4];
    
    offsets[0] = offsetof(ControlParams, m);
    offsets[1] = offsetof(ControlParams, n);
    offsets[2] = offsetof(ControlParams, k);
    offsets[3] = offsetof(ControlParams, total_procs);
    
    MPI_Type_create_struct(4, blocklengths, offsets, types, &mpi_type);
    MPI_Type_commit(&mpi_type);
    
    return mpi_type;
}

// 动态分配矩阵内存
double* allocate_matrix(int rows, int cols) {
    double* matrix = (double*)calloc(rows * cols, sizeof(double));
    if (matrix == NULL) {
        fprintf(stderr, "Error: Failed to allocate matrix memory (%d x %d)\n", rows, cols);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
    return matrix;
}

// 初始化矩阵（仅Root进程调用）
void init_matrix(double* matrix, int rows, int cols, int seed) {
    srand(seed);
    for (int i = 0; i < rows * cols; i++) {
        matrix[i] = (double)(rand() % 100) / 10.0;
    }
}

// 计算每个进程负责的行数（非均匀划分）
void calculate_row_distribution(int m, int size, int* sendcounts, int* displs) {
    int base_rows = m / size;       // 每个进程的基础行数
    int remainder = m % size;       // 剩余行数
    
    int offset = 0;
    for (int i = 0; i < size; i++) {
        // 前 remainder 个进程多分配一行
        int rows = base_rows + (i < remainder ? 1 : 0);
        sendcounts[i] = rows;       // 行数
        displs[i] = offset;         // 偏移量（以行为单位）
        offset += rows;
    }
}

int main(int argc, char* argv[]) {
    int rank, size;
    int m = 1024, n = 1024, k = 1024;  // 默认矩阵规模
    
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    
    // 解析命令行参数
    if (argc >= 4) {
        m = atoi(argv[1]);
        n = atoi(argv[2]);
        k = atoi(argv[3]);
    } else if (argc == 2) {
        // 兼容旧版单参数模式（方阵）
        m = n = k = atoi(argv[1]);
    }
    
    if (m <= 0 || n <= 0 || k <= 0) {
        if (rank == 0) {
            fprintf(stderr, "Error: Matrix dimensions must be positive (m=%d, n=%d, k=%d)\n", m, n, k);
        }
        MPI_Finalize();
        return 1;
    }
    
    // 创建自定义MPI数据类型
    MPI_Datatype MPI_CONTROL_PARAMS = create_control_params_type();
    
    // 初始化控制参数结构体
    ControlParams params;
    params.m = m;
    params.n = n;
    params.k = k;
    params.total_procs = size;
    
    // 广播控制参数
    MPI_Bcast(&params, 1, MPI_CONTROL_PARAMS, 0, MPI_COMM_WORLD);
    
    // 所有进程从广播后的参数获取矩阵维度
    m = params.m;
    n = params.n;
    k = params.k;
    
    // 计算非均匀行分布
    int* sendcounts = (int*)malloc(size * sizeof(int));
    int* displs = (int*)malloc(size * sizeof(int));
    int* recvcounts = (int*)malloc(size * sizeof(int));
    int* recvdispls = (int*)malloc(size * sizeof(int));
    
    calculate_row_distribution(m, size, sendcounts, displs);
    
    // 计算本进程负责的行数
    int my_rows = sendcounts[rank];
    int my_row_offset = displs[rank];
    
    // 分配矩阵内存
    double *A = NULL, *B = NULL, *C = NULL;
    double *local_A = NULL, *local_C = NULL;
    
    // Root进程分配完整矩阵并初始化
    if (rank == 0) {
        A = allocate_matrix(m, n);
        B = allocate_matrix(n, k);
        C = allocate_matrix(m, k);
        
        init_matrix(A, m, n, 42);
        init_matrix(B, n, k, 123);
    }
    
    // 所有进程分配B矩阵空间（用于广播）
    if (rank != 0) {
        B = allocate_matrix(n, k);
    }
    
    // 分配局部矩阵空间
    local_A = allocate_matrix(my_rows, n);
    local_C = allocate_matrix(my_rows, k);
    
    // 开始计时
    MPI_Barrier(MPI_COMM_WORLD);
    double start_time = MPI_Wtime();
    
    // ==================== 集合通信阶段 ====================
    
    // 1. 广播矩阵B给所有进程
    MPI_Bcast(B, n * k, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    
    // 2. 使用 MPI_Scatterv 分发矩阵A的行块（非均匀划分）
    // sendcounts 需要转换为元素数（每行有 n 个元素）
    int* sendcounts_elements = (int*)malloc(size * sizeof(int));
    int* displs_elements = (int*)malloc(size * sizeof(int));
    
    for (int i = 0; i < size; i++) {
        sendcounts_elements[i] = sendcounts[i] * n;  // 行数 * 每行元素数
        displs_elements[i] = displs[i] * n;          // 行偏移 * 每行元素数
    }
    
    MPI_Scatterv(A, sendcounts_elements, displs_elements, MPI_DOUBLE,
                 local_A, my_rows * n, MPI_DOUBLE,
                 0, MPI_COMM_WORLD);
    
    // ==================== 计算阶段 ====================
    
    for (int i = 0; i < my_rows; i++) {
        for (int j = 0; j < k; j++) {
            double sum = 0.0;
            for (int l = 0; l < n; l++) {
                sum += local_A[i * n + l] * B[l * k + j];
            }
            local_C[i * k + j] = sum;
        }
    }
    
    // ==================== 收集结果阶段 ====================
    
    // 3. 使用 MPI_Gatherv 收集各进程的计算结果（非均匀划分）
    // recvcounts 需要转换为元素数（每行有 k 个元素）
    int* recvcounts_elements = (int*)malloc(size * sizeof(int));
    int* recvdispls_elements = (int*)malloc(size * sizeof(int));
    
    for (int i = 0; i < size; i++) {
        recvcounts_elements[i] = sendcounts[i] * k;  // 行数 * 每行元素数
        recvdispls_elements[i] = displs[i] * k;      // 行偏移 * 每行元素数
    }
    
    MPI_Gatherv(local_C, my_rows * k, MPI_DOUBLE,
                C, recvcounts_elements, recvdispls_elements, MPI_DOUBLE,
                0, MPI_COMM_WORLD);
    
    // 结束计时
    MPI_Barrier(MPI_COMM_WORLD);
    double end_time = MPI_Wtime();
    double elapsed_time = end_time - start_time;
    
    // 输出结果（仅Root进程）
    if (rank == 0) {
        printf("Size: %d x %d x %d, Procs: %d, Time: %.4f s\n", m, n, k, size, elapsed_time);
    }
    
    // 释放内存
    if (rank == 0) {
        free(A);
        free(C);
    }
    free(B);
    free(local_A);
    free(local_C);
    
    free(sendcounts);
    free(displs);
    free(recvcounts);
    free(recvdispls);
    free(sendcounts_elements);
    free(displs_elements);
    free(recvcounts_elements);
    free(recvdispls_elements);
    
    // 释放自定义MPI数据类型
    MPI_Type_free(&MPI_CONTROL_PARAMS);
    
    MPI_Finalize();
    return 0;
}