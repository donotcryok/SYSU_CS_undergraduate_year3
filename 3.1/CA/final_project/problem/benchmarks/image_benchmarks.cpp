#include <benchmark/benchmark.h>
#include "image_algorithms.hpp"
#include <random>
#include <iostream>
#include <iomanip>
#include <sstream> // Added for stringstream

using namespace ImageAlgorithms;

// 测试图像尺寸
constexpr size_t SMALL_SIZE = 1024;
constexpr size_t MEDIUM_SIZE = 4096;
constexpr size_t LARGE_SIZE = 16384;

// 固定迭代次数
constexpr int FIXED_ITERATIONS = 5;

/**
 * @brief 生成随机图像
 */
Image generateRandomImage(size_t width, size_t height, unsigned int seed = 42) {
    Image img(width, height);
    std::mt19937 gen(seed);
    std::uniform_int_distribution<> dis(0, 255);

    for (size_t i = 0; i < img.size(); ++i) {
        img.data()[i] = static_cast<unsigned char>(dis(gen));
    }

    return img;
}

// ============================================================================
// Reference Implementations (用于正确性验证的基准算法)
// ============================================================================
namespace Reference {

void gaussianFilter(const Image& input, Image& output) {
    const size_t width = input.width();
    const size_t height = input.height();
    output.resize(width, height);
    
    for (size_t i = 1; i < height - 1; ++i) {
        for (size_t j = 1; j < width - 1; ++j) {
            int sum = 
                input.at(i-1, j-1) + 2*input.at(i-1, j) + input.at(i-1, j+1) +
                2*input.at(i, j-1) + 4*input.at(i, j) + 2*input.at(i, j+1) +
                input.at(i+1, j-1) + 2*input.at(i+1, j) + input.at(i+1, j+1);
            output.at(i, j) = static_cast<unsigned char>(sum / 16);
        }
    }
    // 边界处理
    for (size_t j = 0; j < width; ++j) {
        output.at(0, j) = input.at(0, j);
        output.at(height-1, j) = input.at(height-1, j);
    }
    for (size_t i = 0; i < height; ++i) {
        output.at(i, 0) = input.at(i, 0);
        output.at(i, width-1) = input.at(i, width-1);
    }
}

void powerLawTransformation(const Image& input, Image& output, float gamma) {
    const size_t size = input.size();
    output.resize(input.width(), input.height());
    for (size_t i = 0; i < size; ++i) {
        float normalized = input.data()[i] / 255.0f;
        float transformed = std::pow(normalized, gamma);
        output.data()[i] = static_cast<unsigned char>(transformed * 255.0f + 0.5f);
    }
}

void sobelEdgeDetection(const Image& input, Image& output) {
    const size_t width = input.width();
    const size_t height = input.height();
    output.resize(width, height);
    for (size_t i = 1; i < height - 1; ++i) {
        for (size_t j = 1; j < width - 1; ++j) {
            int gx = -input.at(i-1, j-1) + input.at(i-1, j+1)
                     -2*input.at(i, j-1) + 2*input.at(i, j+1)
                     -input.at(i+1, j-1) + input.at(i+1, j+1);
            int gy = -input.at(i-1, j-1) - 2*input.at(i-1, j) - input.at(i-1, j+1)
                     +input.at(i+1, j-1) + 2*input.at(i+1, j) + input.at(i+1, j+1);
            int magnitude = static_cast<int>(std::sqrt(gx*gx + gy*gy));
            output.at(i, j) = static_cast<unsigned char>(std::min(magnitude, 255));
        }
    }
    // 边界置零
    for (size_t j = 0; j < width; ++j) {
        output.at(0, j) = 0;
        output.at(height-1, j) = 0;
    }
    for (size_t i = 0; i < height; ++i) {
        output.at(i, 0) = 0;
        output.at(i, width-1) = 0;
    }
}

void transpose(const Image& input, Image& output) {
    const size_t width = input.width();
    const size_t height = input.height();
    output.resize(height, width);
    for (size_t i = 0; i < height; ++i) {
        for (size_t j = 0; j < width; ++j) {
            output.at(j, i) = input.at(i, j);
        }
    }
}

void boxFilter(const Image& input, Image& output, int kernel_size) {
    const size_t width = input.width();
    const size_t height = input.height();
    const int radius = kernel_size / 2;
    output.resize(width, height);
    for (size_t i = 0; i < height; ++i) {
        for (size_t j = 0; j < width; ++j) {
            int sum = 0;
            int count = 0;
            for (int di = -radius; di <= radius; ++di) {
                for (int dj = -radius; dj <= radius; ++dj) {
                    int ni = static_cast<int>(i) + di;
                    int nj = static_cast<int>(j) + dj;
                    if (ni >= 0 && ni < static_cast<int>(height) &&
                        nj >= 0 && nj < static_cast<int>(width)) {
                        sum += input.at(ni, nj);
                        count++;
                    }
                }
            }
            output.at(i, j) = static_cast<unsigned char>(sum / count);
        }
    }
}

void rotate90Clockwise(const Image& input, Image& output) {
    const size_t width = input.width();
    const size_t height = input.height();
    output.resize(height, width);
    for (size_t i = 0; i < height; ++i) {
        for (size_t j = 0; j < width; ++j) {
            output.at(j, height - 1 - i) = input.at(i, j);
        }
    }
}

} // namespace Reference

/**
 * @brief 验证算法正确性
 */
struct CorrectnessResult {
    std::string algorithm;
    bool passed;
    std::string message;
};

std::vector<CorrectnessResult> verifyCorrectness() {
    std::vector<CorrectnessResult> results;
    const size_t test_size = 512;
    Image input = generateRandomImage(test_size, test_size, 2333);
    Image output(test_size, test_size);
    Image ref_output(test_size, test_size);

    // 1. 测试高斯滤波
    try {
        Reference::gaussianFilter(input, ref_output);
        gaussianFilter(input, output);
        
        bool passed = compareImages(output, ref_output, 0);
        unsigned int checksum = calcChecksum(output);
        
        std::stringstream ss;
        ss << (passed ? "PASS" : "FAIL") << " (Checksum: " << checksum << ")";
        results.push_back({"GaussianFilter", passed, ss.str()});
    } catch (const std::exception& e) {
        results.push_back({"GaussianFilter", false, std::string("FAIL: Exception - ") + e.what()});
    }

    // 2. 测试幂次变换
    try {
        Reference::powerLawTransformation(input, ref_output, 0.5f);
        powerLawTransformation(input, output, 0.5f);
        
        //可设置允许 1 的误差 (LUT vs float)
        bool passed = compareImages(output, ref_output, 0);
        unsigned int checksum = calcChecksum(output);
        
        std::stringstream ss;
        ss << (passed ? "PASS" : "FAIL") << " (Checksum: " << checksum << ")";
        results.push_back({"PowerLawTransformation", passed, ss.str()});
    } catch (const std::exception& e) {
        results.push_back({"PowerLawTransformation", false, std::string("FAIL: Exception - ") + e.what()});
    }

    // 3. 测试Sobel边缘检测
    try {
        Reference::sobelEdgeDetection(input, ref_output);
        sobelEdgeDetection(input, output);
        
        //可设置的误差 (sqrt float vs int, rounding vs truncation)
        bool passed = compareImages(output, ref_output, 0);
        unsigned int checksum = calcChecksum(output);
        
        std::stringstream ss;
        ss << (passed ? "PASS" : "FAIL") << " (Checksum: " << checksum << ")";
        results.push_back({"SobelEdgeDetection", passed, ss.str()});
    } catch (const std::exception& e) {
        results.push_back({"SobelEdgeDetection", false, std::string("FAIL: Exception - ") + e.what()});
    }

    // 4. 测试转置
    try {
        Reference::transpose(input, ref_output);
        transpose(input, output);
        
        bool passed = compareImages(output, ref_output, 0);
        unsigned int checksum = calcChecksum(output);
        
        std::stringstream ss;
        ss << (passed ? "PASS" : "FAIL") << " (Checksum: " << checksum << ")";
        results.push_back({"Transpose", passed, ss.str()});
    } catch (const std::exception& e) {
        results.push_back({"Transpose", false, std::string("FAIL: Exception - ") + e.what()});
    }

    // 5. 测试均值滤波
    try {
        Reference::boxFilter(input, ref_output, 5);
        boxFilter(input, output, 5);
        
        // 允许 1 的误差 (定点数优化 vs 浮点/整数除法)
        bool passed = compareImages(output, ref_output, 1);
        unsigned int checksum = calcChecksum(output);
        
        std::stringstream ss;
        ss << (passed ? "PASS" : "FAIL") << " (Checksum: " << checksum << ")";
        results.push_back({"BoxFilter", passed, ss.str()});
    } catch (const std::exception& e) {
        results.push_back({"BoxFilter", false, std::string("FAIL: Exception - ") + e.what()});
    }

    // 6. 测试旋转
    try {
        Reference::rotate90Clockwise(input, ref_output);
        rotate90Clockwise(input, output);
        
        bool passed = compareImages(output, ref_output, 0);
        unsigned int checksum = calcChecksum(output);
        
        std::stringstream ss;
        ss << (passed ? "PASS" : "FAIL") << " (Checksum: " << checksum << ")";
        results.push_back({"Rotate90Clockwise", passed, ss.str()});
    } catch (const std::exception& e) {
        results.push_back({"Rotate90Clockwise", false, std::string("FAIL: Exception - ") + e.what()});
    }

    return results;
}

// ============================================================================
// Benchmark Fixtures
// ============================================================================

template<size_t SIZE>
class ImageFixture : public benchmark::Fixture {
public:
    Image input;
    Image output;

    void SetUp(const ::benchmark::State&) override {
        input = generateRandomImage(SIZE, SIZE, 2333);
        output.resize(SIZE, SIZE);
    }
};

// ============================================================================
// 详细的分部测试（所有测试固定5次迭代）
// ============================================================================

// ============================================================================
// Gaussian Filter Benchmarks
// ============================================================================

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, GaussianFilter_Small, SMALL_SIZE)
(benchmark::State& state) {
    for (auto _ : state) {
        gaussianFilter(input, output);
        benchmark::DoNotOptimize(output.data());
    }
    state.SetItemsProcessed(state.iterations() * SMALL_SIZE * SMALL_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, GaussianFilter_Small)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, GaussianFilter_Medium, MEDIUM_SIZE)
(benchmark::State& state) {
    for (auto _ : state) {
        gaussianFilter(input, output);
        benchmark::DoNotOptimize(output.data());
    }
    state.SetItemsProcessed(state.iterations() * MEDIUM_SIZE * MEDIUM_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, GaussianFilter_Medium)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, GaussianFilter_Large, LARGE_SIZE)
(benchmark::State& state) {
    for (auto _ : state) {
        gaussianFilter(input, output);
        benchmark::DoNotOptimize(output.data());
    }
    state.SetItemsProcessed(state.iterations() * LARGE_SIZE * LARGE_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, GaussianFilter_Large)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

// ============================================================================
// Power Law Transformation Benchmarks
// ============================================================================

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, PowerLaw_Small, SMALL_SIZE)
(benchmark::State& state) {
    for (auto _ : state) {
        powerLawTransformation(input, output, 0.5f);
        benchmark::DoNotOptimize(output.data());
    }
    state.SetItemsProcessed(state.iterations() * SMALL_SIZE * SMALL_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, PowerLaw_Small)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, PowerLaw_Medium, MEDIUM_SIZE)
(benchmark::State& state) {
    for (auto _ : state) {
        powerLawTransformation(input, output, 0.5f);
        benchmark::DoNotOptimize(output.data());
    }
    state.SetItemsProcessed(state.iterations() * MEDIUM_SIZE * MEDIUM_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, PowerLaw_Medium)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, PowerLaw_Large, LARGE_SIZE)
(benchmark::State& state) {
    for (auto _ : state) {
        powerLawTransformation(input, output, 0.5f);
        benchmark::DoNotOptimize(output.data());
    }
    state.SetItemsProcessed(state.iterations() * LARGE_SIZE * LARGE_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, PowerLaw_Large)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

// ============================================================================
// Sobel Edge Detection Benchmarks
// ============================================================================

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, Sobel_Small, SMALL_SIZE)
(benchmark::State& state) {
    for (auto _ : state) {
        sobelEdgeDetection(input, output);
        benchmark::DoNotOptimize(output.data());
    }
    state.SetItemsProcessed(state.iterations() * SMALL_SIZE * SMALL_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, Sobel_Small)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, Sobel_Medium, MEDIUM_SIZE)
(benchmark::State& state) {
    for (auto _ : state) {
        sobelEdgeDetection(input, output);
        benchmark::DoNotOptimize(output.data());
    }
    state.SetItemsProcessed(state.iterations() * MEDIUM_SIZE * MEDIUM_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, Sobel_Medium)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, Sobel_Large, LARGE_SIZE)
(benchmark::State& state) {
    for (auto _ : state) {
        sobelEdgeDetection(input, output);
        benchmark::DoNotOptimize(output.data());
    }
    state.SetItemsProcessed(state.iterations() * LARGE_SIZE * LARGE_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, Sobel_Large)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

// ============================================================================
// Transpose Benchmarks
// ============================================================================

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, Transpose_Small, SMALL_SIZE)
(benchmark::State& state) {
    Image transposed(SMALL_SIZE, SMALL_SIZE);
    for (auto _ : state) {
        transpose(input, transposed);
        benchmark::DoNotOptimize(transposed.data());
    }
    state.SetItemsProcessed(state.iterations() * SMALL_SIZE * SMALL_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, Transpose_Small)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, Transpose_Medium, MEDIUM_SIZE)
(benchmark::State& state) {
    Image transposed(MEDIUM_SIZE, MEDIUM_SIZE);
    for (auto _ : state) {
        transpose(input, transposed);
        benchmark::DoNotOptimize(transposed.data());
    }
    state.SetItemsProcessed(state.iterations() * MEDIUM_SIZE * MEDIUM_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, Transpose_Medium)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, Transpose_Large, LARGE_SIZE)
(benchmark::State& state) {
    Image transposed(LARGE_SIZE, LARGE_SIZE);
    for (auto _ : state) {
        transpose(input, transposed);
        benchmark::DoNotOptimize(transposed.data());
    }
    state.SetItemsProcessed(state.iterations() * LARGE_SIZE * LARGE_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, Transpose_Large)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

// ============================================================================
// Box Filter Benchmarks
// ============================================================================

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, BoxFilter_Small, SMALL_SIZE)
(benchmark::State& state) {
    for (auto _ : state) {
        boxFilter(input, output, 5);
        benchmark::DoNotOptimize(output.data());
    }
    state.SetItemsProcessed(state.iterations() * SMALL_SIZE * SMALL_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, BoxFilter_Small)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, BoxFilter_Medium, MEDIUM_SIZE)
(benchmark::State& state) {
    for (auto _ : state) {
        boxFilter(input, output, 5);
        benchmark::DoNotOptimize(output.data());
    }
    state.SetItemsProcessed(state.iterations() * MEDIUM_SIZE * MEDIUM_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, BoxFilter_Medium)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, BoxFilter_Large, LARGE_SIZE)
(benchmark::State& state) {
    for (auto _ : state) {
        boxFilter(input, output, 5);
        benchmark::DoNotOptimize(output.data());
    }
    state.SetItemsProcessed(state.iterations() * LARGE_SIZE * LARGE_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, BoxFilter_Large)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

// ============================================================================
// Rotate90 Benchmarks
// ============================================================================

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, Rotate90_Small, SMALL_SIZE)
(benchmark::State& state) {
    Image rotated(SMALL_SIZE, SMALL_SIZE);
    for (auto _ : state) {
        rotate90Clockwise(input, rotated);
        benchmark::DoNotOptimize(rotated.data());
    }
    state.SetItemsProcessed(state.iterations() * SMALL_SIZE * SMALL_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, Rotate90_Small)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, Rotate90_Medium, MEDIUM_SIZE)
(benchmark::State& state) {
    Image rotated(MEDIUM_SIZE, MEDIUM_SIZE);
    for (auto _ : state) {
        rotate90Clockwise(input, rotated);
        benchmark::DoNotOptimize(rotated.data());
    }
    state.SetItemsProcessed(state.iterations() * MEDIUM_SIZE * MEDIUM_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, Rotate90_Medium)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

BENCHMARK_TEMPLATE_DEFINE_F(ImageFixture, Rotate90_Large, LARGE_SIZE)
(benchmark::State& state) {
    Image rotated(LARGE_SIZE, LARGE_SIZE);
    for (auto _ : state) {
        rotate90Clockwise(input, rotated);
        benchmark::DoNotOptimize(rotated.data());
    }
    state.SetItemsProcessed(state.iterations() * LARGE_SIZE * LARGE_SIZE);
}
BENCHMARK_REGISTER_F(ImageFixture, Rotate90_Large)
    ->Unit(benchmark::kMillisecond)
    ->Iterations(FIXED_ITERATIONS);

// ============================================================================
// 主函数：运行benchmark并显示正确性验证结果
// ============================================================================

int main(int argc, char** argv) {
    // 运行正确性验证
    std::cout << "\n========================================\n";
    std::cout << "正确性验证\n";
    std::cout << "========================================\n";

    auto correctness_results = verifyCorrectness();

    // 显示每个算法的详细结果
    std::cout << "\n详细测试结果：\n";
    std::cout << std::left << std::setw(25) << "算法"
              << std::setw(10) << "状态"
              << "信息\n";
    std::cout << std::string(60, '-') << "\n";

    bool all_passed = true;
    for (const auto& result : correctness_results) {
        std::cout << std::left << std::setw(25) << result.algorithm
                  << std::setw(10) << (result.passed ? "✓ PASS" : "✗ FAIL")
                  << result.message << "\n";
        if (!result.passed) all_passed = false;
    }

    std::cout << "\n总体结果: " << (all_passed ? "✓ 所有测试通过" : "✗ 存在失败的测试") << "\n";
    std::cout << "========================================\n\n";

    // 运行性能测试
    ::benchmark::Initialize(&argc, argv);
    if (::benchmark::ReportUnrecognizedArguments(argc, argv)) return 1;
    ::benchmark::RunSpecifiedBenchmarks();
    ::benchmark::Shutdown();

    return all_passed ? 0 : 1;
}

