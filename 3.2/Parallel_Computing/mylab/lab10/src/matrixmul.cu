/**
 * matrixmul.cu — Lab 10: CUDA 并行矩阵乘法
 *
 * 实现并严格对比以下矩阵乘法核函数:
 *   0: matmul_naive_2d      — 朴素全局内存 (2D Grid + 2D Block)
 *   1: matmul_naive_1d      — 朴素全局内存 (1D Grid + 1D Block)
 *   2: matmul_shared_tiled  — 共享内存分块优化 (2D Grid + 2D Block)
 *
 * 用法:
 *   ./matrixmul_b<N> <m> <n> <k> <kernel_type> <warmup> <repeat>
 *
 *   <N>            : BLOCK_SIZE (编译期宏, 8/16/32)
 *   <m> <n> <k>    : 矩阵维度 C=A×B: A(m×k), B(k×n), C(m×n)
 *   <kernel_type>  : 0=naive_2d, 1=naive_1d, 2=shared_tiled
 *   <warmup>       : 预热轮数 (默认 3)
 *   <repeat>       : 计时轮数 (默认 10)
 *
 * 输出格式 (stdout):
 *   m,n,k,kernel_name,block_size,time_ms,verified
 *
 * 编译要求:
 *   nvcc -O3 -arch=sm_89 -DBLOCK_SIZE=16 -o matrixmul_b16 matrixmul.cu
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <cuda_runtime.h>

/* ================================================================
 * 编译期常量
 * ================================================================ */

#ifndef BLOCK_SIZE
#define BLOCK_SIZE 16
#endif

#define EPSILON 1e-5f
#define CUDA_CHECK(err) do {                                         \
    cudaError_t _err = (err);                                        \
    if (_err != cudaSuccess) {                                       \
        fprintf(stderr, "CUDA Error: %s:%d: %s\n",                   \
                __FILE__, __LINE__, cudaGetErrorString(_err));        \
        exit(EXIT_FAILURE);                                          \
    }                                                                \
} while(0)

/* ================================================================
 * CPU 参考实现 (用于正确性校验)
 * ================================================================ */

void matmul_cpu(const float *A, const float *B, float *C,
                int m, int n, int k)
{
    for (int i = 0; i < m; i++) {
        for (int j = 0; j < n; j++) {
            float sum = 0.0f;
            for (int p = 0; p < k; p++) {
                sum += A[i * k + p] * B[p * n + j];
            }
            C[i * n + j] = sum;
        }
    }
}

/* ================================================================
 * Kernel 0: 朴素全局内存 — 2D Grid + 2D Block
 *
 * 每个线程计算 C 的一个元素, 直接从全局内存读取 A 的整行与 B 的整列。
 * 访存特征: 大量冗余的全局内存读取; 同一 Warp 内相邻线程读取 A 的
 * 同一行但 B 的不同列 → B 读取为合并访问, A 读取不合并。
 * ================================================================ */

__global__ void matmul_naive_2d(const float *A, const float *B, float *C,
                                 int m, int n, int k)
{
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;

    if (row < m && col < n) {
        float sum = 0.0f;
        for (int i = 0; i < k; i++) {
            sum += A[row * k + i] * B[i * n + col];
        }
        C[row * n + col] = sum;
    }
}

/* ================================================================
 * Kernel 1: 朴素全局内存 — 1D Grid + 1D Block
 *
 * 与 Kernel 0 计算逻辑完全相同, 但使用一维线程索引映射到二维矩阵坐标。
 * 用于对比不同 Grid/Block 映射策略对 Occupancy 和调度效率的影响。
 * ================================================================ */

__global__ void matmul_naive_1d(const float *A, const float *B, float *C,
                                 int m, int n, int k)
{
    int tid = blockIdx.x * blockDim.x + threadIdx.x;
    int total = m * n;

    if (tid < total) {
        int row = tid / n;
        int col = tid % n;
        float sum = 0.0f;
        for (int i = 0; i < k; i++) {
            sum += A[row * k + i] * B[i * n + col];
        }
        C[row * n + col] = sum;
    }
}

/* ================================================================
 * Kernel 2: 共享内存分块优化 — 2D Grid + 2D Block
 *
 * 核心优化策略:
 *   1. 将 A、B 各划分为 TILE_DIM×TILE_DIM 子块加载到 Shared Memory
 *   2. 每个 Block 内的线程协同加载一个 Tile
 *   3. 在 Shared Memory 中完成子块的局部矩阵乘法累加
 *   4. 遍历 k 维度上所有 Tile 后, 将最终累加结果写回全局内存
 *
 * 访存收益:
 *   - A 的每个元素从全局内存仅加载一次 (被 Block 内 TILE_DIM 个线程复用)
 *   - B 同上
 *   - 全局内存带宽需求从 O(k) 降至 O(k/TILE_DIM) (每线程)
 *
 * Shared Memory 声明使用编译期常量 BLOCK_SIZE, 确保编译期地址计算最优。
 * ================================================================ */

__global__ void matmul_shared_tiled(const float *A, const float *B, float *C,
                                     int m, int n, int k)
{
    __shared__ float As[BLOCK_SIZE][BLOCK_SIZE];
    __shared__ float Bs[BLOCK_SIZE][BLOCK_SIZE];

    int bx = blockIdx.x;
    int by = blockIdx.y;
    int tx = threadIdx.x;
    int ty = threadIdx.y;

    int row = by * BLOCK_SIZE + ty;   /* C 的全局行索引 */
    int col = bx * BLOCK_SIZE + tx;   /* C 的全局列索引 */

    float sum = 0.0f;

    /* 沿 k 维度遍历所有 Tile */
    int num_tiles = (k + BLOCK_SIZE - 1) / BLOCK_SIZE;
    for (int t = 0; t < num_tiles; t++) {

        /* ---- Phase 1: 协同加载 A 和 B 的 Tile 到 Shared Memory ---- */

        /* 加载 A 的 Tile: A[row][t*BLOCK_SIZE + tx] */
        int a_col = t * BLOCK_SIZE + tx;
        if (row < m && a_col < k)
            As[ty][tx] = A[row * k + a_col];
        else
            As[ty][tx] = 0.0f;

        /* 加载 B 的 Tile: B[t*BLOCK_SIZE + ty][col] */
        int b_row = t * BLOCK_SIZE + ty;
        if (b_row < k && col < n)
            Bs[ty][tx] = B[b_row * n + col];
        else
            Bs[ty][tx] = 0.0f;

        __syncthreads();  /* 确保整个 Tile 加载完成 */

        /* ---- Phase 2: 在 Shared Memory 中计算部分点积 ---- */

#pragma unroll
        for (int kt = 0; kt < BLOCK_SIZE; kt++) {
            sum += As[ty][kt] * Bs[kt][tx];
        }

        __syncthreads();  /* 防止下一轮 Tile 加载覆盖正在使用的数据 */
    }

    /* 写回最终结果 */
    if (row < m && col < n) {
        C[row * n + col] = sum;
    }
}

/* ================================================================
 * 正确性校验: 逐元素比对 CPU 参考结果与 GPU 结果
 *
 * 浮点误差分析:
 *   FP32 精度约为 7 位有效数字 (ULP ≈ 1.19e-7)。
 *   矩阵乘法每个输出元素经过 k 次乘加 (FMA) 运算。
 *   由于 CPU 与 GPU 的累加顺序不同 (CPU 串行 vs. GPU Warp 级并行),
 *   舍入误差按随机游走模型累积: ε ≈ eps_base × sqrt(k)。
 *   取 eps_base = 1e-7, 并保底 1e-5 覆盖小 k 场景。
 * ================================================================ */

int verify_result(const float *cpu, const float *gpu, int total,
                  const char *kernel_name, int k)
{
    /* 动态误差阈值: FP32 每步乘加累积 0.5 ULP ≈ 6e-8, k 步线性累积,
     *   取 1e-7 * k, 并保底 1e-5 覆盖小规模场景 */
    float eps_per_op = 1e-7f;
    float dynamic_eps = eps_per_op * (float)k;
    float threshold = (dynamic_eps > EPSILON) ? dynamic_eps : EPSILON;

    float max_err = 0.0f;
    int err_count = 0;

    for (int i = 0; i < total; i++) {
        float err = fabsf(cpu[i] - gpu[i]);
        if (err > max_err) max_err = err;
        if (err > threshold) {
            if (err_count < 5) {
                fprintf(stderr, "  Mismatch[%d]: cpu=%.6f gpu=%.6f err=%.2e\n",
                        i, cpu[i], gpu[i], err);
            }
            err_count++;
        }
    }

    if (err_count == 0) {
        return 1;  /* 校验通过 */
    } else {
        fprintf(stderr, "  [FAIL] %s: %d/%d elements exceed eps=%.1e, "
                "max_err=%.2e\n",
                kernel_name, err_count, total, threshold, max_err);
        return 0;  /* 校验失败 */
    }
}

/* ================================================================
 * 矩阵初始化 (随机浮点数, 范围 [-1, 1])
 * ================================================================ */

void init_matrix(float *mat, int size) {
    for (int i = 0; i < size; i++) {
        mat[i] = (float)rand() / (float)RAND_MAX * 2.0f - 1.0f;
    }
}

/* ================================================================
 * 主函数
 * ================================================================ */

int main(int argc, char **argv)
{
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <m> <n> <k> [kernel_type] [warmup] [repeat]\n",
                argv[0]);
        fprintf(stderr, "  kernel_type: 0=naive_2d, 1=naive_1d, 2=shared_tiled\n");
        fprintf(stderr, "  Compiled BLOCK_SIZE = %d\n", BLOCK_SIZE);
        return 1;
    }

    int m = atoi(argv[1]);
    int n = atoi(argv[2]);
    int k = atoi(argv[3]);
    int kernel_type = (argc >= 5) ? atoi(argv[4]) : 2;
    int warmup      = (argc >= 6) ? atoi(argv[5]) : 3;
    int repeat      = (argc >= 7) ? atoi(argv[6]) : 10;

    /* 选择核函数名称 (用于输出) */
    const char *kernel_name;
    switch (kernel_type) {
        case 0:  kernel_name = "naive_2d";      break;
        case 1:  kernel_name = "naive_1d";      break;
        case 2:  kernel_name = "shared_tiled";  break;
        default:
            fprintf(stderr, "Invalid kernel_type: %d\n", kernel_type);
            return 1;
    }

    /* 内存分配 */
    int size_a = m * k;
    int size_b = k * n;
    int size_c = m * n;
    size_t bytes_a = size_a * sizeof(float);
    size_t bytes_b = size_b * sizeof(float);
    size_t bytes_c = size_c * sizeof(float);

    float *h_A = (float *)malloc(bytes_a);
    float *h_B = (float *)malloc(bytes_b);
    float *h_C_cpu = (float *)malloc(bytes_c);
    float *h_C_gpu = (float *)malloc(bytes_c);

    srand(42);  /* 固定种子, 保证可复现 */
    init_matrix(h_A, size_a);
    init_matrix(h_B, size_b);

    /* 设备端内存分配 */
    float *d_A, *d_B, *d_C;
    CUDA_CHECK(cudaMalloc((void **)&d_A, bytes_a));
    CUDA_CHECK(cudaMalloc((void **)&d_B, bytes_b));
    CUDA_CHECK(cudaMalloc((void **)&d_C, bytes_c));

    CUDA_CHECK(cudaMemcpy(d_A, h_A, bytes_a, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_B, h_B, bytes_b, cudaMemcpyHostToDevice));

    /* GPU 计时事件 */
    cudaEvent_t start, stop;
    CUDA_CHECK(cudaEventCreate(&start));
    CUDA_CHECK(cudaEventCreate(&stop));

    /* 配置 Grid 和 Block 维度 */
    dim3 block_dim, grid_dim;

    switch (kernel_type) {
        case 0: /* naive_2d */
            block_dim = dim3(BLOCK_SIZE, BLOCK_SIZE);
            grid_dim  = dim3((n + BLOCK_SIZE - 1) / BLOCK_SIZE,
                             (m + BLOCK_SIZE - 1) / BLOCK_SIZE);
            break;
        case 1: /* naive_1d */
            {
                int threads_per_block = BLOCK_SIZE * BLOCK_SIZE;
                int total_threads = m * n;
                block_dim = dim3(threads_per_block);
                grid_dim  = dim3((total_threads + threads_per_block - 1)
                                  / threads_per_block);
            }
            break;
        case 2: /* shared_tiled */
            block_dim = dim3(BLOCK_SIZE, BLOCK_SIZE);
            grid_dim  = dim3((n + BLOCK_SIZE - 1) / BLOCK_SIZE,
                             (m + BLOCK_SIZE - 1) / BLOCK_SIZE);
            break;
    }

    /* 预热 */
    for (int i = 0; i < warmup; i++) {
        switch (kernel_type) {
            case 0:
                matmul_naive_2d<<<grid_dim, block_dim>>>(d_A, d_B, d_C, m, n, k);
                break;
            case 1:
                matmul_naive_1d<<<grid_dim, block_dim>>>(d_A, d_B, d_C, m, n, k);
                break;
            case 2:
                matmul_shared_tiled<<<grid_dim, block_dim>>>(d_A, d_B, d_C, m, n, k);
                break;
        }
        CUDA_CHECK(cudaDeviceSynchronize());
    }

    /* 正式计时 */
    float total_time = 0.0f;
    for (int i = 0; i < repeat; i++) {
        CUDA_CHECK(cudaEventRecord(start));
        switch (kernel_type) {
            case 0:
                matmul_naive_2d<<<grid_dim, block_dim>>>(d_A, d_B, d_C, m, n, k);
                break;
            case 1:
                matmul_naive_1d<<<grid_dim, block_dim>>>(d_A, d_B, d_C, m, n, k);
                break;
            case 2:
                matmul_shared_tiled<<<grid_dim, block_dim>>>(d_A, d_B, d_C, m, n, k);
                break;
        }
        CUDA_CHECK(cudaEventRecord(stop));
        CUDA_CHECK(cudaEventSynchronize(stop));

        float ms;
        CUDA_CHECK(cudaEventElapsedTime(&ms, start, stop));
        total_time += ms;
    }
    float avg_time = total_time / (float)repeat;

    /* 拷贝结果回主机 */
    CUDA_CHECK(cudaMemcpy(h_C_gpu, d_C, bytes_c, cudaMemcpyDeviceToHost));

    /* CPU 参考计算 (仅做一次) */
    matmul_cpu(h_A, h_B, h_C_cpu, m, n, k);

    /* 正确性校验 */
    int verified = verify_result(h_C_cpu, h_C_gpu, size_c, kernel_name, k);

    /* 输出结果: CSV 格式一行 (用于 Python 解析) */
    printf("%d,%d,%d,%s,%d,%.6f,%d\n",
           m, n, k, kernel_name, BLOCK_SIZE, avg_time, verified);

    /* 清理 */
    CUDA_CHECK(cudaEventDestroy(start));
    CUDA_CHECK(cudaEventDestroy(stop));
    CUDA_CHECK(cudaFree(d_A));
    CUDA_CHECK(cudaFree(d_B));
    CUDA_CHECK(cudaFree(d_C));
    free(h_A);
    free(h_B);
    free(h_C_cpu);
    free(h_C_gpu);

    return 0;
}
