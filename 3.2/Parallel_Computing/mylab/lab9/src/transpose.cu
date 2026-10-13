#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <cuda_runtime.h>

// ============================================================
// 配置宏
// ============================================================
#define TILE_DIM_16 16
#define TILE_DIM_32 32

// ============================================================
// 算法 A: Naive Global Memory — 基础全局内存转置
// 直接根据行列索引通过全局内存进行不合并的读（或写）。
// 此处采用 "读合并、写不合并" 方式：
//   每个线程读取 (row,col)，写入 (col,row)。
//   读取时同一 warp 内的线程访问连续列（合并读），
//   写入时跨行跳跃（不合并写）。
// ============================================================
template <typename T>
__global__ void transpose_naive_global(const T *A, T *AT, int n) {
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;
    if (row < n && col < n) {
        AT[col * n + row] = A[row * n + col];
    }
}

// ============================================================
// 算法 B: Shared Memory Naive（含 Bank Conflict）
// 将矩阵分块 (Tile) 加载到 Shared Memory，
// 消除全局内存的不合并写，但会引发 Bank Conflict。
//
// 加载阶段：同一 warp 线程访问连续全局内存 → 合并读。
// 存储阶段：从 shared memory 以转置方式读出 → 合并写。
// 但 shared memory 读取阶段，同一 warp 线程访问同一 bank 的不同
// 地址偏移 → 产生 bank conflict。
// ============================================================
template <typename T, int TILE_DIM>
__global__ void transpose_shared_naive(const T *A, T *AT, int n) {
    __shared__ T tile[TILE_DIM][TILE_DIM];

    int bx = blockIdx.x, by = blockIdx.y;
    int tx = threadIdx.x, ty = threadIdx.y;

    int row = by * TILE_DIM + ty;
    int col = bx * TILE_DIM + tx;

    // 协同加载 tile
    if (row < n && col < n) {
        tile[ty][tx] = A[row * n + col];
    }

    __syncthreads();

    // 计算转置后的输出坐标
    int out_row = bx * TILE_DIM + ty;
    int out_col = by * TILE_DIM + tx;

    // 转置写回全局内存（合并写）
    if (out_row < n && out_col < n) {
        AT[out_row * n + out_col] = tile[tx][ty];
    }
}

// ============================================================
// 算法 C: Optimized Shared Memory（Padding 消除 Bank Conflict）
// 在 Shared Memory 二维数组的第二维增加 Padding (TILE_DIM+1)，
// 使同一列的元素在 32 个 bank 中分布在不同的 bank 上，
// 彻底消除 Bank Conflict。
//
// Bank 映射公式：bank_index = (byte_address / 4) % 32
// 设无 padding 时 tile[ty][tx] 的 bank = (ty * TILE_DIM + tx) % 32
// 当多个线程的 ty 不同但 (ty * TILE_DIM) % 32 相同时就会冲突。
// 增加 padding 后 tile[ty][tx] 的 bank = (ty * (TILE_DIM+1) + tx) % 32
// 如果 TILE_DIM+1 与 32 互质或至少不是 32 的约数，
// 则不同 ty 访问同一 bank 的概率大大降低。
// ============================================================
template <typename T, int TILE_DIM>
__global__ void transpose_shared_padded(const T *A, T *AT, int n) {
    __shared__ T tile[TILE_DIM][TILE_DIM + 1];  // padding!

    int bx = blockIdx.x, by = blockIdx.y;
    int tx = threadIdx.x, ty = threadIdx.y;

    int row = by * TILE_DIM + ty;
    int col = bx * TILE_DIM + tx;

    // 协同加载 tile
    if (row < n && col < n) {
        tile[ty][tx] = A[row * n + col];
    }

    __syncthreads();

    // 计算转置后的输出坐标
    int out_row = bx * TILE_DIM + ty;
    int out_col = by * TILE_DIM + tx;

    // 转置写回全局内存（合并写）
    if (out_row < n && out_col < n) {
        AT[out_row * n + out_col] = tile[tx][ty];
    }
}

// ============================================================
// 正确性校验：比较两个矩阵是否在误差范围内相等
// ============================================================
template <typename T>
bool verify_transpose(const T *ref, const T *result, int n, T eps = 1e-6) {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            T diff = fabs(ref[i * n + j] - result[i * n + j]);
            if (diff > eps) {
                fprintf(stderr, "Mismatch at (%d,%d): ref=%f, got=%f\n",
                        i, j, (double)ref[i * n + j], (double)result[i * n + j]);
                return false;
            }
        }
    }
    return true;
}

// ============================================================
// CPU 参考转置
// ============================================================
template <typename T>
void cpu_transpose(const T *A, T *AT, int n) {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            AT[j * n + i] = A[i * n + j];
        }
    }
}

// ============================================================
// 基于 cudaEvent_t 的精确内核计时（不含 Host-Device 拷贝）
// ============================================================
template <typename T, int TILE_DIM>
float time_kernel_naive(const T *d_A, T *d_AT, int n,
                        dim3 grid, dim3 block, int warmup_iters, int bench_iters) {
    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);

    // warmup
    for (int i = 0; i < warmup_iters; i++) {
        transpose_naive_global<T><<<grid, block>>>(d_A, d_AT, n);
    }
    cudaDeviceSynchronize();

    // benchmark
    cudaEventRecord(start, 0);
    for (int i = 0; i < bench_iters; i++) {
        transpose_naive_global<T><<<grid, block>>>(d_A, d_AT, n);
    }
    cudaEventRecord(stop, 0);
    cudaDeviceSynchronize();

    float elapsed_ms = 0;
    cudaEventElapsedTime(&elapsed_ms, start, stop);
    cudaEventDestroy(start);
    cudaEventDestroy(stop);

    return elapsed_ms / bench_iters;
}

template <typename T, int TILE_DIM>
float time_kernel_shared_naive(const T *d_A, T *d_AT, int n,
                               dim3 grid, dim3 block, int warmup_iters, int bench_iters) {
    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);

    for (int i = 0; i < warmup_iters; i++) {
        transpose_shared_naive<T, TILE_DIM><<<grid, block>>>(d_A, d_AT, n);
    }
    cudaDeviceSynchronize();

    cudaEventRecord(start, 0);
    for (int i = 0; i < bench_iters; i++) {
        transpose_shared_naive<T, TILE_DIM><<<grid, block>>>(d_A, d_AT, n);
    }
    cudaEventRecord(stop, 0);
    cudaDeviceSynchronize();

    float elapsed_ms = 0;
    cudaEventElapsedTime(&elapsed_ms, start, stop);
    cudaEventDestroy(start);
    cudaEventDestroy(stop);

    return elapsed_ms / bench_iters;
}

template <typename T, int TILE_DIM>
float time_kernel_shared_padded(const T *d_A, T *d_AT, int n,
                                dim3 grid, dim3 block, int warmup_iters, int bench_iters) {
    cudaEvent_t start, stop;
    cudaEventCreate(&start);
    cudaEventCreate(&stop);

    for (int i = 0; i < warmup_iters; i++) {
        transpose_shared_padded<T, TILE_DIM><<<grid, block>>>(d_A, d_AT, n);
    }
    cudaDeviceSynchronize();

    cudaEventRecord(start, 0);
    for (int i = 0; i < bench_iters; i++) {
        transpose_shared_padded<T, TILE_DIM><<<grid, block>>>(d_A, d_AT, n);
    }
    cudaEventRecord(stop, 0);
    cudaDeviceSynchronize();

    float elapsed_ms = 0;
    cudaEventElapsedTime(&elapsed_ms, start, stop);
    cudaEventDestroy(start);
    cudaEventDestroy(stop);

    return elapsed_ms / bench_iters;
}

// ============================================================
// 测试入口
// ============================================================
int main() {
    // 测试配置
    const int sizes[] = {512, 1024, 2048};
    const int n_sizes = 3;
    const int tile_dims[] = {16, 32};
    const int n_tiles = 2;

    // 预热与测试迭代次数
    const int warmup_iters = 3;
    const int bench_iters = 10;

    printf("============================================================\n");
    printf("  CUDA Matrix Transpose Benchmark\n");
    printf("============================================================\n\n");

    // 打印 CSV 头
    printf("n,tile_dim,algorithm,time_ms\n");

    for (int si = 0; si < n_sizes; si++) {
        int n = sizes[si];
        size_t matrix_bytes = (size_t)n * n * sizeof(float);

        // Host 端分配
        float *h_A = (float *)malloc(matrix_bytes);
        float *h_AT_cpu = (float *)malloc(matrix_bytes);
        float *h_AT_gpu = (float *)malloc(matrix_bytes);

        // 随机初始化矩阵 A
        srand(42);
        for (int i = 0; i < n * n; i++) {
            h_A[i] = (float)rand() / RAND_MAX;
        }

        // CPU 参考转置
        cpu_transpose(h_A, h_AT_cpu, n);

        // Device 端分配
        float *d_A, *d_AT;
        cudaMalloc(&d_A, matrix_bytes);
        cudaMalloc(&d_AT, matrix_bytes);
        cudaMemcpy(d_A, h_A, matrix_bytes, cudaMemcpyHostToDevice);

        fprintf(stderr, "\n>>> Testing n = %d (matrix %dx%d, %.2f MB)\n",
                n, n, n, (double)matrix_bytes / (1024.0 * 1024.0));

        for (int ti = 0; ti < n_tiles; ti++) {
            int TILE_DIM = tile_dims[ti];
            dim3 block(TILE_DIM, TILE_DIM);
            dim3 grid((n + TILE_DIM - 1) / TILE_DIM, (n + TILE_DIM - 1) / TILE_DIM);

            fprintf(stderr, "  Tile = %dx%d\n", TILE_DIM, TILE_DIM);

            // ---- 算法 A: Naive Global Memory ----
            {
                cudaMemset(d_AT, 0, matrix_bytes);
                float t_ms = time_kernel_naive<float, 16>(
                    d_A, d_AT, n, grid, block, warmup_iters, bench_iters);

                // 正确性校验
                cudaMemcpy(h_AT_gpu, d_AT, matrix_bytes, cudaMemcpyDeviceToHost);
                bool correct = verify_transpose(h_AT_cpu, h_AT_gpu, n);
                fprintf(stderr, "    Naive Global:     %.6f ms  %s\n", t_ms, correct ? "PASS" : "FAIL");
                if (!correct) {
                    fprintf(stderr, "FATAL: Naive Global verification failed!\n");
                    return 1;
                }
                printf("%d,%d,naive_global,%.6f\n", n, TILE_DIM, t_ms);
            }

            // ---- 算法 B: Shared Memory Naive (Bank Conflict) ----
            {
                cudaMemset(d_AT, 0, matrix_bytes);
                float t_ms = 0;
                if (TILE_DIM == 16) {
                    t_ms = time_kernel_shared_naive<float, 16>(
                        d_A, d_AT, n, grid, block, warmup_iters, bench_iters);
                } else {
                    t_ms = time_kernel_shared_naive<float, 32>(
                        d_A, d_AT, n, grid, block, warmup_iters, bench_iters);
                }

                cudaMemcpy(h_AT_gpu, d_AT, matrix_bytes, cudaMemcpyDeviceToHost);
                bool correct = verify_transpose(h_AT_cpu, h_AT_gpu, n);
                fprintf(stderr, "    Shared Naive:     %.6f ms  %s\n", t_ms, correct ? "PASS" : "FAIL");
                if (!correct) {
                    fprintf(stderr, "FATAL: Shared Naive verification failed!\n");
                    return 1;
                }
                printf("%d,%d,shared_naive,%.6f\n", n, TILE_DIM, t_ms);
            }

            // ---- 算法 C: Optimized Shared Memory (Padding) ----
            {
                cudaMemset(d_AT, 0, matrix_bytes);
                float t_ms = 0;
                if (TILE_DIM == 16) {
                    t_ms = time_kernel_shared_padded<float, 16>(
                        d_A, d_AT, n, grid, block, warmup_iters, bench_iters);
                } else {
                    t_ms = time_kernel_shared_padded<float, 32>(
                        d_A, d_AT, n, grid, block, warmup_iters, bench_iters);
                }

                cudaMemcpy(h_AT_gpu, d_AT, matrix_bytes, cudaMemcpyDeviceToHost);
                bool correct = verify_transpose(h_AT_cpu, h_AT_gpu, n);
                fprintf(stderr, "    Shared Padded:    %.6f ms  %s\n", t_ms, correct ? "PASS" : "FAIL");
                if (!correct) {
                    fprintf(stderr, "FATAL: Shared Padded verification failed!\n");
                    return 1;
                }
                printf("%d,%d,shared_padded,%.6f\n", n, TILE_DIM, t_ms);
            }
        }

        cudaFree(d_A);
        cudaFree(d_AT);
        free(h_A);
        free(h_AT_cpu);
        free(h_AT_gpu);
    }

    fprintf(stderr, "\nAll tests passed!\n");
    return 0;
}
