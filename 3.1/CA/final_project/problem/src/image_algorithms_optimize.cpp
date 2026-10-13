#include "image_algorithms.hpp"
#include <cmath>
#include <vector>
#include <algorithm>
#include <omp.h>
#include <immintrin.h>

namespace ImageAlgorithms {

/**
 * @brief 高斯滤波 - 3x3卷积核
 * 
 * 卷积核:
 *   1  2  1
 *   2  4  2
 *   1  2  1
 * 除以16进行归一化
 * 优化点：
 *   - 使用AVX2指令集一次处理16个像素
 *   - 显式展开每步，避免-O0下的函数调用和临时变量开销
 *   - 移位代替乘法，提升效率
 *   - r0/r1/r2指针提升缓存命中率
 */
__attribute__((target("avx2")))
void gaussianFilter(const Image& input, Image& output) {
    const size_t width = input.width();
    const size_t height = input.height();
    const unsigned char* src = input.data();
    
    output.resize(width, height);
    unsigned char* dst = output.data();
    
    // 边界处理
    std::copy(src, src + width, dst);
    std::copy(src + (height - 1) * width, src + height * width, dst + (height - 1) * width);
    
    for (size_t i = 1; i < height - 1; ++i) {
        dst[i * width] = src[i * width];
        dst[i * width + width - 1] = src[i * width + width - 1];
    }

    // 核心处理区域
    #pragma omp parallel for
    for (size_t i = 1; i < height - 1; ++i) {
        const unsigned char* r0 = src + (i - 1) * width;
        const unsigned char* r1 = src + i * width;
        const unsigned char* r2 = src + (i + 1) * width;
        unsigned char* out_row = dst + i * width;

        size_t j = 1;
        
        // AVX2 优化: 每次处理 16 个像素
        for (; j <= width - 17; j += 16) {
            // 加载3x3窗口的每一行数据
            __m128i t0_l = _mm_loadu_si128((const __m128i*)(r0 + j - 1));
            __m128i t0_c = _mm_loadu_si128((const __m128i*)(r0 + j));
            __m128i t0_r = _mm_loadu_si128((const __m128i*)(r0 + j + 1));
            
            __m128i t1_l = _mm_loadu_si128((const __m128i*)(r1 + j - 1));
            __m128i t1_c = _mm_loadu_si128((const __m128i*)(r1 + j));
            __m128i t1_r = _mm_loadu_si128((const __m128i*)(r1 + j + 1));
            
            __m128i t2_l = _mm_loadu_si128((const __m128i*)(r2 + j - 1));
            __m128i t2_c = _mm_loadu_si128((const __m128i*)(r2 + j));
            __m128i t2_r = _mm_loadu_si128((const __m128i*)(r2 + j + 1));

            // 扩展到16位，防止溢出
            __m256i p0_l = _mm256_cvtepu8_epi16(t0_l);
            __m256i p0_c = _mm256_cvtepu8_epi16(t0_c);
            __m256i p0_r = _mm256_cvtepu8_epi16(t0_r);
            
            __m256i p1_l = _mm256_cvtepu8_epi16(t1_l);
            __m256i p1_c = _mm256_cvtepu8_epi16(t1_c);
            __m256i p1_r = _mm256_cvtepu8_epi16(t1_r);
            
            __m256i p2_l = _mm256_cvtepu8_epi16(t2_l);
            __m256i p2_c = _mm256_cvtepu8_epi16(t2_c);
            __m256i p2_r = _mm256_cvtepu8_epi16(t2_r);

            // 卷积计算，移位代替乘法
            __m256i sum0 = _mm256_add_epi16(_mm256_add_epi16(p0_l, p0_r), _mm256_slli_epi16(p0_c, 1));
            __m256i sum1 = _mm256_add_epi16(_mm256_add_epi16(_mm256_slli_epi16(p1_l, 1), _mm256_slli_epi16(p1_r, 1)), _mm256_slli_epi16(p1_c, 2));
            __m256i sum2 = _mm256_add_epi16(_mm256_add_epi16(p2_l, p2_r), _mm256_slli_epi16(p2_c, 1));
            __m256i total = _mm256_add_epi16(_mm256_add_epi16(sum0, sum1), sum2);
            total = _mm256_srli_epi16(total, 4); // 除以16
            
            // 压缩回8位并存储
            __m256i packed = _mm256_packus_epi16(total, _mm256_setzero_si256());
            __m256i perm = _mm256_permute4x64_epi64(packed, _MM_SHUFFLE(3, 1, 2, 0));
            __m128i res = _mm256_castsi256_si128(perm);
            
            _mm_storeu_si128((__m128i*)(out_row + j), res);
        }

        // 处理剩余像素
        for (; j < width - 1; ++j) {
            int sum = 
                r0[j-1] + (r0[j] << 1) + r0[j+1] +
                (r1[j-1] << 1) + (r1[j] << 2) + (r1[j+1] << 1) +
                r2[j-1] + (r2[j] << 1) + r2[j+1];
            out_row[j] = static_cast<unsigned char>(sum >> 4);
        }
    }
    
    // 处理边界（简单复制）
    // 上下边界
    const unsigned char* src_first = src;
    const unsigned char* src_last = src + (height - 1) * width;
    unsigned char* dst_first = dst;
    unsigned char* dst_last = dst + (height - 1) * width;
    
    for (size_t j = 0; j < width; ++j) {
        dst_first[j] = src_first[j];
        dst_last[j] = src_last[j];
    }
    
    // 左右边界
    for (size_t i = 0; i < height; ++i) {
        dst[i * width] = src[i * width];
        dst[i * width + width - 1] = src[i * width + width - 1];
    }
}

/**
 * @brief 幂次变换 - 对比度调整
 * 
 * 公式: output = 255 * (input/255)^gamma
 * 优化点：
 *   - 预先计算查找表，避免重复浮点运算
 *   - 主循环仅为一次访存，极大减少计算量
 *   - OpenMP并行进一步提升吞吐
 */
__attribute__((target("avx2")))
void powerLawTransformation(const Image& input, Image& output, float gamma) {
    const size_t size = input.size();
    const unsigned char* src = input.data();
    
    output.resize(input.width(), input.height());
    unsigned char* dst = output.data();
    
    // 预计算查找表 (LUT)
    unsigned char lut[256];
    for (int i = 0; i < 256; ++i) {
        float normalized = i / 255.0f;
        float transformed = std::pow(normalized, gamma);
        lut[i] = static_cast<unsigned char>(transformed * 255.0f + 0.5f);
    }
    
    // OpenMP并行查表
    #pragma omp parallel for
    for (size_t i = 0; i < size; ++i) {
        dst[i] = lut[src[i]];
    }
}

/**
 * @brief Sobel边缘检测
 * 
 * Gx = [-1 0 1]    Gy = [-1 -2 -1]
 *      [-2 0 2]         [ 0  0  0]
 *      [-1 0 1]         [ 1  2  1]
 * Sobel算子计算图像梯度，常用于边缘检测。
 * 优化点：
 *   - AVX2并行计算Gx/Gy和幅值
 *   - 利用SIMD指令并行计算平方根
 *   - 极大提升边缘检测效率
 */
__attribute__((target("avx2")))
void sobelEdgeDetection(const Image& input, Image& output) {
    const size_t width = input.width();
    const size_t height = input.height();
    const unsigned char* src = input.data();
    
    output.resize(width, height);
    unsigned char* dst = output.data();
    
    // 边界置零
    unsigned char* dst_last = dst + (height - 1) * width;
    for (size_t j = 0; j < width; ++j) {
        dst[j] = 0;
        dst_last[j] = 0;
    }
    for (size_t i = 0; i < height; ++i) {
        dst[i * width] = 0;
        dst[i * width + width - 1] = 0;
    }

    #pragma omp parallel for
    for (size_t i = 1; i < height - 1; ++i) {
        const unsigned char* r0 = src + (i - 1) * width;
        const unsigned char* r1 = src + i * width;
        const unsigned char* r2 = src + (i + 1) * width;
        unsigned char* out_row = dst + i * width;

        size_t j = 1;
        
        // AVX2 优化: 每次处理 8 个像素
        for (; j <= width - 9; j += 8) {
            // 直接展开 lambda
            __m128i p0_l = _mm_cvtepu8_epi16(_mm_loadl_epi64((const __m128i*)(r0 + j - 1)));
            __m128i p0_c = _mm_cvtepu8_epi16(_mm_loadl_epi64((const __m128i*)(r0 + j)));
            __m128i p0_r = _mm_cvtepu8_epi16(_mm_loadl_epi64((const __m128i*)(r0 + j + 1)));
            
            __m128i p1_l = _mm_cvtepu8_epi16(_mm_loadl_epi64((const __m128i*)(r1 + j - 1)));
            __m128i p1_r = _mm_cvtepu8_epi16(_mm_loadl_epi64((const __m128i*)(r1 + j + 1)));
            
            __m128i p2_l = _mm_cvtepu8_epi16(_mm_loadl_epi64((const __m128i*)(r2 + j - 1)));
            __m128i p2_c = _mm_cvtepu8_epi16(_mm_loadl_epi64((const __m128i*)(r2 + j)));
            __m128i p2_r = _mm_cvtepu8_epi16(_mm_loadl_epi64((const __m128i*)(r2 + j + 1)));

            __m128i right = _mm_add_epi16(_mm_add_epi16(p0_r, p2_r), _mm_slli_epi16(p1_r, 1));
            __m128i left  = _mm_add_epi16(_mm_add_epi16(p0_l, p2_l), _mm_slli_epi16(p1_l, 1));
            __m128i gx_16 = _mm_sub_epi16(right, left);

            __m128i bottom = _mm_add_epi16(_mm_add_epi16(p2_l, p2_r), _mm_slli_epi16(p2_c, 1));
            __m128i top    = _mm_add_epi16(_mm_add_epi16(p0_l, p0_r), _mm_slli_epi16(p0_c, 1));
            __m128i gy_16  = _mm_sub_epi16(bottom, top);

            __m256i gx_32 = _mm256_cvtepi16_epi32(gx_16);
            __m256i gy_32 = _mm256_cvtepi16_epi32(gy_16);

            __m256 gx_f = _mm256_cvtepi32_ps(gx_32);
            __m256 gy_f = _mm256_cvtepi32_ps(gy_32);

            __m256 mag_f = _mm256_sqrt_ps(_mm256_add_ps(_mm256_mul_ps(gx_f, gx_f), _mm256_mul_ps(gy_f, gy_f)));

            // 使用截断 (Truncation) 而非舍入 (Rounding) 以匹配 static_cast<int> 的行为
            __m256i mag_32 = _mm256_cvttps_epi32(mag_f);

            __m128i mag_lo = _mm256_castsi256_si128(mag_32);
            __m128i mag_hi = _mm256_extracti128_si256(mag_32, 1);
            
            __m128i mag_16 = _mm_packus_epi32(mag_lo, mag_hi);
            __m128i mag_8  = _mm_packus_epi16(mag_16, _mm_setzero_si128());

            _mm_storel_epi64((__m128i*)(out_row + j), mag_8);
        }

        // Scalar cleanup
        for (; j < width - 1; ++j) {
            int gx = -r0[j-1] + r0[j+1]
                     - (r1[j-1] << 1) + (r1[j+1] << 1)
                     - r2[j-1] + r2[j+1];
            
            int gy = -r0[j-1] - (r0[j] << 1) - r0[j+1]
                     + r2[j-1] + (r2[j] << 1) + r2[j+1];
            
            int magnitude = static_cast<int>(std::sqrt(gx*gx + gy*gy));
            out_row[j] = static_cast<unsigned char>(std::min(magnitude, 255));
        }
    }
    
}

/**
 * @brief 图像转置
 */
__attribute__((target("avx2")))
void transpose(const Image& input, Image& output) {
    const size_t width = input.width();
    const size_t height = input.height();
    const unsigned char* src = input.data();
    
    output.resize(height, width);
    unsigned char* dst = output.data();
    
    const size_t BLOCK_SIZE = 32;
    
    #pragma omp parallel for collapse(2)
    for (size_t i = 0; i < height; i += BLOCK_SIZE) {
        for (size_t j = 0; j < width; j += BLOCK_SIZE) {
            size_t i_end = std::min(i + BLOCK_SIZE, height);
            size_t j_end = std::min(j + BLOCK_SIZE, width);
            
            // 快速路径：完整块 (32x32) 使用 AVX2 8x8 转置
            if (i_end - i == BLOCK_SIZE && j_end - j == BLOCK_SIZE) {
                for (size_t ii = i; ii < i + BLOCK_SIZE; ii += 8) {
                    for (size_t jj = j; jj < j + BLOCK_SIZE; jj += 8) {
                        const unsigned char* s = src + ii * width + jj;
                        
                        // 使用 _mm_loadu_si128 替代 _mm_loadl_epi64 以减少指令数
                        // 虽然我们只需要低64位，但加载128位通常不比加载64位慢，且能利用更宽的加载端口
                        // 注意：需要确保不越界。由于我们处理的是内部完整块，且图像通常有padding或对齐，
                        // 或者至少最后一行可能越界。为了安全，我们还是用 loadl_epi64
                        
                        __m128i r0 = _mm_loadl_epi64((const __m128i*)(s + 0 * width));
                        __m128i r1 = _mm_loadl_epi64((const __m128i*)(s + 1 * width));
                        __m128i r2 = _mm_loadl_epi64((const __m128i*)(s + 2 * width));
                        __m128i r3 = _mm_loadl_epi64((const __m128i*)(s + 3 * width));
                        __m128i r4 = _mm_loadl_epi64((const __m128i*)(s + 4 * width));
                        __m128i r5 = _mm_loadl_epi64((const __m128i*)(s + 5 * width));
                        __m128i r6 = _mm_loadl_epi64((const __m128i*)(s + 6 * width));
                        __m128i r7 = _mm_loadl_epi64((const __m128i*)(s + 7 * width));

                        // 8x8 字节转置
                        __m128i t0 = _mm_unpacklo_epi8(r0, r1);
                        __m128i t1 = _mm_unpacklo_epi8(r2, r3);
                        __m128i t2 = _mm_unpacklo_epi8(r4, r5);
                        __m128i t3 = _mm_unpacklo_epi8(r6, r7);
                        
                        __m128i m0 = _mm_unpacklo_epi16(t0, t1);
                        __m128i m1 = _mm_unpackhi_epi16(t0, t1);
                        __m128i m2 = _mm_unpacklo_epi16(t2, t3);
                        __m128i m3 = _mm_unpackhi_epi16(t2, t3);
                        
                        __m128i out01 = _mm_unpacklo_epi32(m0, m2);
                        __m128i out23 = _mm_unpackhi_epi32(m0, m2);
                        __m128i out45 = _mm_unpacklo_epi32(m1, m3);
                        __m128i out67 = _mm_unpackhi_epi32(m1, m3);

                        unsigned char* d = dst + jj * height + ii;
                        
                        _mm_storel_epi64((__m128i*)(d + 0 * height), out01);
                        _mm_storel_epi64((__m128i*)(d + 1 * height), _mm_unpackhi_epi64(out01, out01));
                        _mm_storel_epi64((__m128i*)(d + 2 * height), out23);
                        _mm_storel_epi64((__m128i*)(d + 3 * height), _mm_unpackhi_epi64(out23, out23));
                        _mm_storel_epi64((__m128i*)(d + 4 * height), out45);
                        _mm_storel_epi64((__m128i*)(d + 5 * height), _mm_unpackhi_epi64(out45, out45));
                        _mm_storel_epi64((__m128i*)(d + 6 * height), out67);
                        _mm_storel_epi64((__m128i*)(d + 7 * height), _mm_unpackhi_epi64(out67, out67));
                    }
                }
            } else {
                // 边界处理
                for (size_t jj = j; jj < j_end; ++jj) {
                    unsigned char* dst_ptr = dst + jj * height + i;
                    const unsigned char* src_ptr = src + i * width + jj;
                    for (size_t ii = i; ii < i_end; ++ii) {
                        *dst_ptr++ = *src_ptr;
                        src_ptr += width;
                    }
                }
            }
        }
    }
}

/**
 * @brief 均值滤波
 */
__attribute__((target("avx2")))
void boxFilter(const Image& input, Image& output, int kernel_size) {
    const size_t width = input.width();
    const size_t height = input.height();
    const int radius = kernel_size / 2;
    const unsigned char* src = input.data();
    
    output.resize(width, height);
    unsigned char* dst = output.data();
    
    // 预计算定点数倒数 (用于中心区域)
    // 使用 16 位定点数: scale = 65536
    const int area = kernel_size * kernel_size;
    const int scale = 1 << 16;
    const int inv_area = scale / area; 

    // 并行化行处理
    // 每个线程维护自己的列和缓冲区，避免分配大内存
    #pragma omp parallel
    {
        // 使用原始数组替代 vector 以减少 -O0 下的开销
        int* col_sums = new int[width];
        
        #pragma omp for
        for (size_t i = 0; i < height; ++i) {
            // 边界行：使用原始慢速代码
            if (i < (size_t)radius || i >= height - radius) {
                for (size_t j = 0; j < width; ++j) {
                    int j_min = std::max(0, static_cast<int>(j) - radius);
                    int j_max = std::min(static_cast<int>(width) - 1, static_cast<int>(j) + radius);
                    int sum = 0; int count = 0;
                    for (int ni = std::max(0, static_cast<int>(i) - radius); ni <= std::min(static_cast<int>(height) - 1, static_cast<int>(i) + radius); ++ni) {
                        for (int nj = j_min; nj <= j_max; ++nj) {
                            sum += src[ni * width + nj];
                            count++;
                        }
                    }
                    dst[i * width + j] = static_cast<unsigned char>(sum / count);
                }
                continue;
            }
            
            // 中心行：
            // 1. 计算 col_sums (垂直方向 sum)
            for (size_t j = 0; j < width; ++j) {
                int sum = 0;
                const unsigned char* col_ptr = src + (i - radius) * width + j;
                for (int k = 0; k < kernel_size; ++k) {
                    sum += *col_ptr;
                    col_ptr += width;
                }
                col_sums[j] = sum;
            }
            
            // 2. 水平滑动窗口
            int window_sum = 0;
            
            // 左边界 (j < radius)
            for (size_t j = 0; j < (size_t)radius; ++j) {
                int sum = 0; int count = 0;
                int j_min = 0; 
                int j_max = j + radius;
                for (int nj = j_min; nj <= j_max; ++nj) sum += col_sums[nj];
                count = kernel_size * (j_max - j_min + 1);
                dst[i * width + j] = static_cast<unsigned char>(sum / count);
            }
            
            // 中心部分 (j: radius ~ width-radius)
            window_sum = 0; // Reset
            for (int k = 0; k < kernel_size; ++k) window_sum += col_sums[k];
            
            dst[i * width + radius] = static_cast<unsigned char>((window_sum * inv_area) >> 16);
            
            for (size_t j = radius + 1; j < width - radius; ++j) {
                window_sum -= col_sums[j - radius - 1];
                window_sum += col_sums[j + radius];
                dst[i * width + j] = static_cast<unsigned char>((window_sum * inv_area) >> 16);
            }
            
            // 右边界
            for (size_t j = width - radius; j < width; ++j) {
                int sum = 0; int count = 0;
                int j_min = j - radius;
                int j_max = width - 1;
                for (int nj = j_min; nj <= j_max; ++nj) sum += col_sums[nj];
                count = kernel_size * (j_max - j_min + 1);
                dst[i * width + j] = static_cast<unsigned char>(sum / count);
            }
        }
        delete[] col_sums;
    }
}

/**
 * @brief 图像旋转90度（顺时针）
 */
__attribute__((target("avx2")))
void rotate90Clockwise(const Image& input, Image& output) {
    const size_t width = input.width();
    const size_t height = input.height();
    const unsigned char* src = input.data();
    
    output.resize(height, width);
    unsigned char* dst = output.data();
    
    const size_t BLOCK_SIZE = 32;
    // 字节反转掩码
    __m128i rev_mask = _mm_setr_epi8(7, 6, 5, 4, 3, 2, 1, 0, -1, -1, -1, -1, -1, -1, -1, -1);
    
    #pragma omp parallel for collapse(2)
    for (size_t i = 0; i < height; i += BLOCK_SIZE) {
        for (size_t j = 0; j < width; j += BLOCK_SIZE) {
            size_t i_end = std::min(i + BLOCK_SIZE, height);
            size_t j_end = std::min(j + BLOCK_SIZE, width);
            
            // 快速路径：完整块 (32x32)
            if (i_end - i == BLOCK_SIZE && j_end - j == BLOCK_SIZE) {
                for (size_t ii = i; ii < i + BLOCK_SIZE; ii += 8) {
                    for (size_t jj = j; jj < j + BLOCK_SIZE; jj += 8) {
                        // 加载 8x8
                        const unsigned char* s = src + ii * width + jj;
                        __m128i r0 = _mm_loadl_epi64((const __m128i*)(s + 0 * width));
                        __m128i r1 = _mm_loadl_epi64((const __m128i*)(s + 1 * width));
                        __m128i r2 = _mm_loadl_epi64((const __m128i*)(s + 2 * width));
                        __m128i r3 = _mm_loadl_epi64((const __m128i*)(s + 3 * width));
                        __m128i r4 = _mm_loadl_epi64((const __m128i*)(s + 4 * width));
                        __m128i r5 = _mm_loadl_epi64((const __m128i*)(s + 5 * width));
                        __m128i r6 = _mm_loadl_epi64((const __m128i*)(s + 6 * width));
                        __m128i r7 = _mm_loadl_epi64((const __m128i*)(s + 7 * width));

                        // 转置
                        __m128i t0 = _mm_unpacklo_epi8(r0, r1);
                        __m128i t1 = _mm_unpacklo_epi8(r2, r3);
                        __m128i t2 = _mm_unpacklo_epi8(r4, r5);
                        __m128i t3 = _mm_unpacklo_epi8(r6, r7);
                        __m128i m0 = _mm_unpacklo_epi16(t0, t1);
                        __m128i m1 = _mm_unpackhi_epi16(t0, t1);
                        __m128i m2 = _mm_unpacklo_epi16(t2, t3);
                        __m128i m3 = _mm_unpackhi_epi16(t2, t3);
                        __m128i out01 = _mm_unpacklo_epi32(m0, m2);
                        __m128i out23 = _mm_unpackhi_epi32(m0, m2);
                        __m128i out45 = _mm_unpacklo_epi32(m1, m3);
                        __m128i out67 = _mm_unpackhi_epi32(m1, m3);

                        // 反转并存储
                        // dst row: jj + k
                        // dst col start: H - 8 - ii
                        unsigned char* d = dst + jj * height + (height - 8 - ii);
                        
                        // 展开 lambda
                        _mm_storel_epi64((__m128i*)(d + 0 * height), _mm_shuffle_epi8(out01, rev_mask));
                        _mm_storel_epi64((__m128i*)(d + 1 * height), _mm_shuffle_epi8(_mm_unpackhi_epi64(out01, out01), rev_mask));
                        _mm_storel_epi64((__m128i*)(d + 2 * height), _mm_shuffle_epi8(out23, rev_mask));
                        _mm_storel_epi64((__m128i*)(d + 3 * height), _mm_shuffle_epi8(_mm_unpackhi_epi64(out23, out23), rev_mask));
                        _mm_storel_epi64((__m128i*)(d + 4 * height), _mm_shuffle_epi8(out45, rev_mask));
                        _mm_storel_epi64((__m128i*)(d + 5 * height), _mm_shuffle_epi8(_mm_unpackhi_epi64(out45, out45), rev_mask));
                        _mm_storel_epi64((__m128i*)(d + 6 * height), _mm_shuffle_epi8(out67, rev_mask));
                        _mm_storel_epi64((__m128i*)(d + 7 * height), _mm_shuffle_epi8(_mm_unpackhi_epi64(out67, out67), rev_mask));
                    }
                }
            } else {
                // 边界处理
                for (size_t jj = j; jj < j_end; ++jj) {
                    unsigned char* dst_ptr = dst + jj * height + (height - 1 - i);
                    const unsigned char* src_ptr = src + i * width + jj;
                    for (size_t ii = i; ii < i_end; ++ii) {
                        *dst_ptr-- = *src_ptr;
                        src_ptr += width;
                    }
                }
            }
        }
    }
}

/**
 * @brief 计算校验和
 */
unsigned int calcChecksum(const Image& img) {
    unsigned int sum = 0;
    constexpr size_t mod = 1000000007;
    const size_t size = img.size();
    const unsigned char* data = img.data();
    
    for (size_t i = 0; i < size; ++i) {
        sum = (sum + data[i]) % mod;
    }
    
    return sum;
}

/**
 * @brief 比较两个图像
 */
bool compareImages(const Image& img1, const Image& img2, unsigned char tolerance) {
    if (img1.width() != img2.width() || img1.height() != img2.height()) {
        return false;
    }
    
    const size_t size = img1.size();
    for (size_t i = 0; i < size; ++i) {
        int diff = std::abs(static_cast<int>(img1.data()[i]) - static_cast<int>(img2.data()[i]));
        if (diff > tolerance) {
            return false;
        }
    }
    
    return true;
}

} // namespace ImageAlgorithms

