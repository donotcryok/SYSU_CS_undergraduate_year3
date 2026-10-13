/**
 * convolution.cu — Lab 11: CUDA 卷积神经网络算子实验
 * 
 * 实现三种卷积方法：
 *   1. 直接卷积 (Direct Convolution)
 *   2. im2col + GEMM 卷积
 *   3. cuDNN 卷积
 *
 * 编译: nvcc -O3 -arch=sm_89 -lcudnn -o convolution convolution.cu
 */

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <cuda_runtime.h>
#include <cudnn.h>

// ============================================================
// 宏定义
// ============================================================
#define BLOCK_SIZE 16          // 2D Block 尺寸 (16x16)
#define BLOCK_SIZE_1D 256      // 1D Block 尺寸
#define CUDA_CHECK(err)  do { \
    cudaError_t e = (err); \
    if (e != cudaSuccess) { \
        fprintf(stderr, "CUDA Error %s:%d: %s\n", __FILE__, __LINE__, cudaGetErrorString(e)); \
        exit(1); \
    } \
} while(0)

#define CUDNN_CHECK(err) do { \
    cudnnStatus_t e = (err); \
    if (e != CUDNN_STATUS_SUCCESS) { \
        fprintf(stderr, "cuDNN Error %s:%d: %s\n", __FILE__, __LINE__, cudnnGetErrorString(e)); \
        exit(1); \
    } \
} while(0)

// ============================================================
// CPU 参考实现 (用于校验)
// ============================================================
void conv_cpu_reference(
    const float *input,   // [C, H, W]
    const float *kernel,  // [C_out, C, K, K]
    float *output,        // [C_out, H_out, W_out]
    int C, int H, int W,
    int C_out, int K,
    int H_out, int W_out,
    int pad, int stride)
{
    for (int oc = 0; oc < C_out; oc++) {
        for (int oy = 0; oy < H_out; oy++) {
            for (int ox = 0; ox < W_out; ox++) {
                float sum = 0.0f;
                for (int ic = 0; ic < C; ic++) {
                    for (int ky = 0; ky < K; ky++) {
                        for (int kx = 0; kx < K; kx++) {
                            int ix = ox * stride + kx - pad;
                            int iy = oy * stride + ky - pad;
                            if (ix >= 0 && ix < W && iy >= 0 && iy < H) {
                                sum += input[ic * H * W + iy * W + ix]
                                     * kernel[oc * C * K * K + ic * K * K + ky * K + kx];
                            }
                        }
                    }
                }
                output[oc * H_out * W_out + oy * W_out + ox] = sum;
            }
        }
    }
}

// ============================================================
// 计算校验和 (Checksum)
// ============================================================
float compute_checksum(const float *data, int N) {
    double sum = 0.0;
    for (int i = 0; i < N; i++) {
        sum += (double)data[i];
    }
    return (float)sum;
}

// ============================================================
// 验证两个数组是否一致 (动态误差阈值)
// ============================================================
int verify_result(const float *a, const float *b, int N, float eps) {
    int mismatches = 0;
    float max_diff = 0.0f;
    for (int i = 0; i < N; i++) {
        float diff = fabsf(a[i] - b[i]);
        if (diff > max_diff) max_diff = diff;
        if (diff > eps) {
            if (mismatches < 5) {
                printf("  Mismatch[%d]: ref=%.8f, got=%.8f, diff=%.2e\n", i, a[i], b[i], diff);
            }
            mismatches++;
        }
    }
    if (mismatches > 0) {
        printf("  Total mismatches: %d / %d, max_diff=%.2e\n", mismatches, N, max_diff);
    }
    return (mismatches == 0) ? 1 : 0;
}

// ============================================================
// 任务 1: Direct Convolution Kernel
// ============================================================
// 2D Grid + 2D Block, 每个线程计算一个输出位置的所有 C_out 通道
__global__ void direct_conv_kernel(
    const float * __restrict__ input,
    const float * __restrict__ kernel,
    float * __restrict__ output,
    int C, int H, int W,
    int C_out, int K,
    int H_out, int W_out,
    int pad, int stride)
{
    int ox = blockIdx.x * blockDim.x + threadIdx.x;
    int oy = blockIdx.y * blockDim.y + threadIdx.y;

    if (ox >= W_out || oy >= H_out) return;

    int input_plane = H * W;
    int kernel_plane = C * K * K;
    int output_plane = H_out * W_out;

    for (int oc = 0; oc < C_out; oc++) {
        float sum = 0.0f;
        const float *k_ptr = kernel + oc * kernel_plane;

        for (int ic = 0; ic < C; ic++) {
            int iy_base = oy * stride - pad;
            int ix_base = ox * stride - pad;

            for (int ky = 0; ky < K; ky++) {
                int iy = iy_base + ky;
                if (iy < 0 || iy >= H) continue;
                for (int kx = 0; kx < K; kx++) {
                    int ix = ix_base + kx;
                    if (ix < 0 || ix >= W) continue;
                    sum += input[ic * input_plane + iy * W + ix]
                         * k_ptr[ic * K * K + ky * K + kx];
                }
            }
        }
        output[oc * output_plane + oy * W_out + ox] = sum;
    }
}

// ============================================================
// 任务 2: im2col Kernel
// ============================================================
// 将输入张量 [C, H, W] 转换为 im2col 矩阵 [C*K*K, H_out*W_out]
// 使用 1D grid, 每个线程处理一个矩阵元素
__global__ void im2col_kernel(
    const float * __restrict__ input,
    float * __restrict__ col,
    int C, int H, int W,
    int K, int H_out, int W_out,
    int pad, int stride)
{
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    int total = C * K * K * H_out * W_out;
    if (idx >= total) return;

    int col_stride = H_out * W_out;          // 每个 patch 元素跨步
    int patch_idx  = idx / col_stride;        // patch 内偏移
    int sp_idx     = idx % col_stride;         // 空间位置

    int ox = sp_idx % W_out;
    int oy = sp_idx / W_out;

    int ic = patch_idx / (K * K);
    int kk = patch_idx % (K * K);
    int ky = kk / K;
    int kx = kk % K;

    int ix = ox * stride + kx - pad;
    int iy = oy * stride + ky - pad;

    if (ix >= 0 && ix < W && iy >= 0 && iy < H)
        col[idx] = input[ic * H * W + iy * W + ix];
    else
        col[idx] = 0.0f;
}

// ============================================================
// 任务 2: Shared Memory Tiled GEMM Kernel
// ============================================================
// C = A * B,  A: [M, K], B: [K, N], C: [M, N]
// 与实验十相同的共享内存分块实现
#define TILE_SIZE 16

__global__ void gemm_tiled_kernel(
    const float * __restrict__ A,
    const float * __restrict__ B,
    float * __restrict__ C,
    int M, int N, int K_gemm)
{
    __shared__ float As[TILE_SIZE][TILE_SIZE];
    __shared__ float Bs[TILE_SIZE][TILE_SIZE];

    int row = blockIdx.y * TILE_SIZE + threadIdx.y;
    int col = blockIdx.x * TILE_SIZE + threadIdx.x;
    float sum = 0.0f;

    int num_tiles = (K_gemm + TILE_SIZE - 1) / TILE_SIZE;
    for (int t = 0; t < num_tiles; t++) {
        // 协同加载 A 的分块
        int a_col = t * TILE_SIZE + threadIdx.x;
        if (row < M && a_col < K_gemm)
            As[threadIdx.y][threadIdx.x] = A[row * K_gemm + a_col];
        else
            As[threadIdx.y][threadIdx.x] = 0.0f;

        // 协同加载 B 的分块
        int b_row = t * TILE_SIZE + threadIdx.y;
        if (b_row < K_gemm && col < N)
            Bs[threadIdx.y][threadIdx.x] = B[b_row * N + col];
        else
            Bs[threadIdx.y][threadIdx.x] = 0.0f;

        __syncthreads();

        #pragma unroll
        for (int kt = 0; kt < TILE_SIZE; kt++) {
            sum += As[threadIdx.y][kt] * Bs[kt][threadIdx.x];
        }
        __syncthreads();
    }

    if (row < M && col < N)
        C[row * N + col] = sum;
}

// ============================================================
// 任务 2: im2col + GEMM 卷积包装器
// ============================================================
void conv_im2col_gemm(
    const float *d_input, const float *d_kernel,
    float *d_output, float *d_col, float *d_kernel_mat,
    int C, int H, int W, int C_out, int K,
    int H_out, int W_out, int pad, int stride,
    cudaEvent_t start, cudaEvent_t stop, float *ms_time)
{
    int M = C_out;
    int K_gemm = C * K * K;
    int N = H_out * W_out;

    // Phase 1: im2col
    int col_total = K_gemm * N;
    int im2col_grid = (col_total + BLOCK_SIZE_1D - 1) / BLOCK_SIZE_1D;
    im2col_kernel<<<im2col_grid, BLOCK_SIZE_1D>>>(
        d_input, d_col, C, H, W, K, H_out, W_out, pad, stride);

    // Phase 2: 将 kernel 从 [C_out, C, K, K] 转换为 [C_out, C*K*K]
    // kernel 在内存中已经是连续布局 (oc, ic, ky, kx), 直接使用
    // d_kernel 本身就是 [M, K_gemm], 直接传给 GEMM
    // 不需要额外转换!

    // Phase 3: GPU 计时起点
    cudaEventRecord(start);
    im2col_kernel<<<im2col_grid, BLOCK_SIZE_1D>>>(
        d_input, d_col, C, H, W, K, H_out, W_out, pad, stride);
    cudaDeviceSynchronize();

    // GEMM: C_out x (C*K*K)  *  (C*K*K) x (H_out*W_out)
    dim3 gemm_block(TILE_SIZE, TILE_SIZE);
    dim3 gemm_grid((N + TILE_SIZE - 1) / TILE_SIZE,
                   (M + TILE_SIZE - 1) / TILE_SIZE);
    gemm_tiled_kernel<<<gemm_grid, gemm_block>>>(
        d_kernel, d_col, d_output, M, N, K_gemm);
    cudaDeviceSynchronize();
    cudaEventRecord(stop);
    cudaEventSynchronize(stop);
    cudaEventElapsedTime(ms_time, start, stop);
}

// ============================================================
// 任务 1: 直接卷积包装器 (含计时)
// ============================================================
float run_direct_convolution(
    const float *d_input, const float *d_kernel, float *d_output,
    int C, int H, int W, int C_out, int K,
    int H_out, int W_out, int pad, int stride,
    cudaEvent_t start, cudaEvent_t stop)
{
    dim3 block(BLOCK_SIZE, BLOCK_SIZE);
    dim3 grid((W_out + BLOCK_SIZE - 1) / BLOCK_SIZE,
              (H_out + BLOCK_SIZE - 1) / BLOCK_SIZE);

    cudaEventRecord(start);
    direct_conv_kernel<<<grid, block>>>(
        d_input, d_kernel, d_output,
        C, H, W, C_out, K, H_out, W_out, pad, stride);
    cudaDeviceSynchronize();
    cudaEventRecord(stop);
    cudaEventSynchronize(stop);

    float ms;
    cudaEventElapsedTime(&ms, start, stop);
    return ms;
}

// ============================================================
// 任务 3: cuDNN 卷积包装器
// ============================================================
float run_cudnn_convolution(
    const float *d_input, const float *d_kernel, float *d_output,
    int C, int H, int W, int C_out, int K,
    int H_out, int W_out, int pad, int stride,
    cudnnHandle_t handle,
    cudnnTensorDescriptor_t input_desc,
    cudnnTensorDescriptor_t output_desc,
    cudnnFilterDescriptor_t filter_desc,
    cudnnConvolutionDescriptor_t conv_desc,
    cudaEvent_t start, cudaEvent_t stop)
{
    float alpha = 1.0f, beta = 0.0f;

    // Warmup
    CUDNN_CHECK(cudnnConvolutionForward(handle, &alpha, input_desc, d_input,
        filter_desc, d_kernel, conv_desc, CUDNN_CONVOLUTION_FWD_ALGO_IMPLICIT_GEMM,
        NULL, 0, &beta, output_desc, d_output));
    cudaDeviceSynchronize();

    // Timed run
    cudaEventRecord(start);
    CUDNN_CHECK(cudnnConvolutionForward(handle, &alpha, input_desc, d_input,
        filter_desc, d_kernel, conv_desc, CUDNN_CONVOLUTION_FWD_ALGO_IMPLICIT_GEMM,
        NULL, 0, &beta, output_desc, d_output));
    cudaDeviceSynchronize();
    cudaEventRecord(stop);
    cudaEventSynchronize(stop);

    float ms;
    cudaEventElapsedTime(&ms, start, stop);
    return ms;
}

// ============================================================
// 输出大小计算
// ============================================================
void calc_output_size(int H, int W, int K, int pad, int stride,
                       int *H_out, int *W_out) {
    *H_out = (H + 2 * pad - K) / stride + 1;
    *W_out = (W + 2 * pad - K) / stride + 1;
}

// ============================================================
// 主函数
// ============================================================
int main(int argc, char **argv) {
    if (argc < 3) {
        printf("Usage: %s <input_size> <stride> [output_csv]\n", argv[0]);
        printf("  input_size: 32, 64, 128, 256, 512\n");
        printf("  stride: 1, 2, 3\n");
        printf("  output_csv: optional CSV file to append results\n");
        return 1;
    }

    int H = atoi(argv[1]);
    int W = H;
    int stride = atoi(argv[2]);
    const char *csv_file = (argc >= 4) ? argv[3] : NULL;

    const int C = 3;           // 输入通道
    const int C_out = 3;       // 输出通道
    const int K = 3;           // 卷积核尺寸
    const int pad = 1;         // Padding (same padding for stride=1)

    int H_out, W_out;
    calc_output_size(H, W, K, pad, stride, &H_out, &W_out);

    printf("\n");
    printf("============================================================\n");
    printf("  CUDA Convolution Benchmark\n");
    printf("  Input:  [%d, %d, %d]  (%dx%d spatial)\n", C, H, W, H, W);
    printf("  Kernel: [%d, %d, %d, %d]\n", C_out, C, K, K);
    printf("  Stride: %d, Padding: %d\n", stride, pad);
    printf("  Output: [%d, %d, %d]  (%dx%d spatial)\n", C_out, H_out, W_out, H_out, W_out);
    printf("============================================================\n");

    // 分配主机内存
    size_t input_size  = C * H * W * sizeof(float);
    size_t kernel_size = C_out * C * K * K * sizeof(float);
    size_t output_size = C_out * H_out * W_out * sizeof(float);
    size_t col_size    = C * K * K * H_out * W_out * sizeof(float);

    float *h_input  = (float *)malloc(input_size);
    float *h_kernel = (float *)malloc(kernel_size);
    float *h_output_ref   = (float *)malloc(output_size);
    float *h_output_direct = (float *)malloc(output_size);
    float *h_output_im2col = (float *)malloc(output_size);
    float *h_output_cudnn  = (float *)malloc(output_size);

    // 初始化输入和卷积核 (随机值)
    srand(42);
    for (size_t i = 0; i < C * H * W; i++)
        h_input[i] = (float)(rand()) / (float)(RAND_MAX) * 2.0f - 1.0f;
    for (size_t i = 0; i < C_out * C * K * K; i++)
        h_kernel[i] = (float)(rand()) / (float)(RAND_MAX) * 2.0f - 1.0f;

    // CPU 参考结果
    conv_cpu_reference(h_input, h_kernel, h_output_ref,
                       C, H, W, C_out, K, H_out, W_out, pad, stride);
    float ref_checksum = compute_checksum(h_output_ref, C_out * H_out * W_out);

    // 分配设备内存
    float *d_input, *d_kernel, *d_output, *d_col;
    CUDA_CHECK(cudaMalloc(&d_input, input_size));
    CUDA_CHECK(cudaMalloc(&d_kernel, kernel_size));
    CUDA_CHECK(cudaMalloc(&d_output, output_size));
    CUDA_CHECK(cudaMalloc(&d_col, col_size));

    // 拷贝数据到设备
    CUDA_CHECK(cudaMemcpy(d_input, h_input, input_size, cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_kernel, h_kernel, kernel_size, cudaMemcpyHostToDevice));

    // 创建 CUDA Events
    cudaEvent_t start, stop;
    CUDA_CHECK(cudaEventCreate(&start));
    CUDA_CHECK(cudaEventCreate(&stop));

    // ============================================================
    // 任务 1: Direct Convolution
    // ============================================================
    printf("\n--- Task 1: Direct Convolution ---\n");
    float t_direct = 0.0f;

    // Warmup
    {
        dim3 block(BLOCK_SIZE, BLOCK_SIZE);
        dim3 grid((W_out + BLOCK_SIZE - 1) / BLOCK_SIZE,
                  (H_out + BLOCK_SIZE - 1) / BLOCK_SIZE);
        direct_conv_kernel<<<grid, block>>>(
            d_input, d_kernel, d_output,
            C, H, W, C_out, K, H_out, W_out, pad, stride);
        CUDA_CHECK(cudaDeviceSynchronize());
    }

    // Timed (3 runs, take average)
    for (int r = 0; r < 3; r++) {
        float t = run_direct_convolution(
            d_input, d_kernel, d_output,
            C, H, W, C_out, K, H_out, W_out, pad, stride,
            start, stop);
        t_direct += t;
    }
    t_direct /= 3.0f;

    CUDA_CHECK(cudaMemcpy(h_output_direct, d_output, output_size, cudaMemcpyDeviceToHost));
    float direct_checksum = compute_checksum(h_output_direct, C_out * H_out * W_out);
    int direct_ok = verify_result(h_output_ref, h_output_direct, C_out * H_out * W_out, 1e-4f);
    printf("  Time: %.6f ms, Checksum: %.6f, Verified: %s\n",
           t_direct, direct_checksum, direct_ok ? "PASS" : "FAIL");

    // ============================================================
    // 任务 2: im2col + GEMM
    // ============================================================
    printf("\n--- Task 2: im2col + GEMM Convolution ---\n");

    float t_im2col = 0.0f;
    for (int r = 0; r < 3; r++) {
        float t;
        conv_im2col_gemm(d_input, d_kernel, d_output, d_col, d_kernel,
                         C, H, W, C_out, K, H_out, W_out, pad, stride,
                         start, stop, &t);
        t_im2col += t;
    }
    t_im2col /= 3.0f;

    CUDA_CHECK(cudaMemcpy(h_output_im2col, d_output, output_size, cudaMemcpyDeviceToHost));
    float im2col_checksum = compute_checksum(h_output_im2col, C_out * H_out * W_out);
    int im2col_ok = verify_result(h_output_ref, h_output_im2col, C_out * H_out * W_out, 1e-4f);
    printf("  Time: %.6f ms, Checksum: %.6f, Verified: %s\n",
           t_im2col, im2col_checksum, im2col_ok ? "PASS" : "FAIL");

    // ============================================================
    // 任务 3: cuDNN Convolution
    // ============================================================
    printf("\n--- Task 3: cuDNN Convolution ---\n");

    // 创建 cuDNN 句柄和描述符
    cudnnHandle_t cudnn_handle;
    CUDNN_CHECK(cudnnCreate(&cudnn_handle));

    cudnnTensorDescriptor_t input_desc, output_desc;
    cudnnFilterDescriptor_t filter_desc;
    cudnnConvolutionDescriptor_t conv_desc;

    CUDNN_CHECK(cudnnCreateTensorDescriptor(&input_desc));
    CUDNN_CHECK(cudnnCreateTensorDescriptor(&output_desc));
    CUDNN_CHECK(cudnnCreateFilterDescriptor(&filter_desc));
    CUDNN_CHECK(cudnnCreateConvolutionDescriptor(&conv_desc));

    // 设置描述符 (NCHW 格式)
    CUDNN_CHECK(cudnnSetTensor4dDescriptor(input_desc, CUDNN_TENSOR_NCHW,
        CUDNN_DATA_FLOAT, 1, C, H, W));
    CUDNN_CHECK(cudnnSetTensor4dDescriptor(output_desc, CUDNN_TENSOR_NCHW,
        CUDNN_DATA_FLOAT, 1, C_out, H_out, W_out));
    CUDNN_CHECK(cudnnSetFilter4dDescriptor(filter_desc, CUDNN_DATA_FLOAT,
        CUDNN_TENSOR_NCHW, C_out, C, K, K));
    CUDNN_CHECK(cudnnSetConvolution2dDescriptor(conv_desc,
        pad, pad, stride, stride, 1, 1, CUDNN_CROSS_CORRELATION,
        CUDNN_DATA_FLOAT));

    // 查询推荐算法
    int requested_algo_count = 1;
    int returned_algo_count;
    cudnnConvolutionFwdAlgoPerf_t algo_perf;
    CUDNN_CHECK(cudnnFindConvolutionForwardAlgorithm(cudnn_handle,
        input_desc, filter_desc, conv_desc, output_desc,
        requested_algo_count, &returned_algo_count, &algo_perf));
    printf("  cuDNN algo: %d, time: %.3f ms\n", algo_perf.algo, algo_perf.time);

    // Warmup
    {
        float alpha = 1.0f, beta = 0.0f;
        CUDNN_CHECK(cudnnConvolutionForward(cudnn_handle,
            &alpha, input_desc, d_input,
            filter_desc, d_kernel, conv_desc,
            algo_perf.algo, NULL, 0,
            &beta, output_desc, d_output));
        CUDA_CHECK(cudaDeviceSynchronize());
    }

    float t_cudnn = 0.0f;
    for (int r = 0; r < 3; r++) {
        float t = run_cudnn_convolution(
            d_input, d_kernel, d_output,
            C, H, W, C_out, K, H_out, W_out, pad, stride,
            cudnn_handle, input_desc, output_desc,
            filter_desc, conv_desc, start, stop);
        t_cudnn += t;
    }
    t_cudnn /= 3.0f;

    CUDA_CHECK(cudaMemcpy(h_output_cudnn, d_output, output_size, cudaMemcpyDeviceToHost));
    float cudnn_checksum = compute_checksum(h_output_cudnn, C_out * H_out * W_out);
    int cudnn_ok = verify_result(h_output_ref, h_output_cudnn, C_out * H_out * W_out, 1e-4f);
    printf("  Time: %.6f ms, Checksum: %.6f, Verified: %s\n",
           t_cudnn, cudnn_checksum, cudnn_ok ? "PASS" : "FAIL");

    // ============================================================
    // 输出汇总
    // ============================================================
    printf("\n============================================================\n");
    printf("  Summary: H=%d, stride=%d\n", H, stride);
    printf("  Direct Conv:  %.6f ms\n", t_direct);
    printf("  im2col+GEMM:  %.6f ms\n", t_im2col);
    printf("  cuDNN:        %.6f ms\n", t_cudnn);
    printf("============================================================\n");

    // 写入 CSV
    if (csv_file) {
        FILE *fp = fopen(csv_file, "a");
        if (fp) {
            // 如果是新文件，写入表头
            fseek(fp, 0, SEEK_END);
            if (ftell(fp) == 0) {
                fprintf(fp, "H,W,C,C_out,K,stride,pad,H_out,W_out,"
                        "t_direct_ms,t_im2col_ms,t_cudnn_ms,"
                        "direct_ok,im2col_ok,cudnn_ok\n");
            }
            fprintf(fp, "%d,%d,%d,%d,%d,%d,%d,%d,%d,"
                    "%.6f,%.6f,%.6f,%d,%d,%d\n",
                    H, W, C, C_out, K, stride, pad, H_out, W_out,
                    t_direct, t_im2col, t_cudnn,
                    direct_ok, im2col_ok, cudnn_ok);
            fclose(fp);
            printf("  Results appended to %s\n", csv_file);
        }
    }

    // 清理资源
    CUDNN_CHECK(cudnnDestroyTensorDescriptor(input_desc));
    CUDNN_CHECK(cudnnDestroyTensorDescriptor(output_desc));
    CUDNN_CHECK(cudnnDestroyFilterDescriptor(filter_desc));
    CUDNN_CHECK(cudnnDestroyConvolutionDescriptor(conv_desc));
    CUDNN_CHECK(cudnnDestroy(cudnn_handle));

    CUDA_CHECK(cudaEventDestroy(start));
    CUDA_CHECK(cudaEventDestroy(stop));
    CUDA_CHECK(cudaFree(d_input));
    CUDA_CHECK(cudaFree(d_kernel));
    CUDA_CHECK(cudaFree(d_output));
    CUDA_CHECK(cudaFree(d_col));

    free(h_input);
    free(h_kernel);
    free(h_output_ref);
    free(h_output_direct);
    free(h_output_im2col);
    free(h_output_cudnn);

    printf("\nDone.\n");
    return 0;
}
