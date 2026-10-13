#include <stdio.h>
#include <stdlib.h>
#include <cuda_runtime.h>

/**
 * CUDA Hello World 核函数
 * Grid: 1D (n blocks)
 * Block: 2D (m rows × k columns)
 *
 * 每个线程输出 "Hello World from Thread (行, 列) in Block 块号!"
 */
__global__ void hello_kernel() {
    int block_id = blockIdx.x;
    int row = threadIdx.y;  // 行索引
    int col = threadIdx.x;  // 列索引
    printf("Hello World from Thread (%d, %d) in Block %d!\n", row, col, block_id);
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <n> <m> <k>\n", argv[0]);
        fprintf(stderr, "  n = number of blocks (1-32)\n");
        fprintf(stderr, "  m = block dimension in y (1-32)\n");
        fprintf(stderr, "  k = block dimension in x (1-32)\n");
        return 1;
    }

    int n = atoi(argv[1]);
    int m = atoi(argv[2]);
    int k = atoi(argv[3]);

    if (n < 1 || n > 32 || m < 1 || m > 32 || k < 1 || k > 32) {
        fprintf(stderr, "Error: n, m, k must be in [1, 32]\n");
        return 1;
    }

    // 配置 Grid (1D: n blocks) 和 Block (2D: m × k threads)
    dim3 gridDim(n, 1, 1);
    dim3 blockDim(k, m, 1);  // x 维度 = k 列, y 维度 = m 行

    printf("Launching kernel with Grid=(%d,1,1), Block=(%d,%d,1)\n", n, k, m);
    printf("Total threads = %d blocks × %d threads/block = %d\n", n, k * m, n * k * m);
    printf("--- Kernel Output ---\n");

    hello_kernel<<<gridDim, blockDim>>>();

    // 同步设备，确保所有核函数输出完成
    cudaDeviceSynchronize();

    // 检查核函数执行是否出错
    cudaError_t err = cudaGetLastError();
    if (err != cudaSuccess) {
        fprintf(stderr, "CUDA Error: %s\n", cudaGetErrorString(err));
        return 1;
    }

    printf("--- Host Output ---\n");
    printf("Hello World from the host!\n");

    return 0;
}
