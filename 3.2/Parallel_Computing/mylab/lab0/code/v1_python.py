#!/usr/bin/env python3
"""
V1: Python 基准版本
使用 NumPy 进行矩阵乘法，作为性能基准参考
"""

import numpy as np
import time
import random

def matrix_multiplication_python(A, B):
    """纯 Python 实现的矩阵乘法（不使用 NumPy 的 dot）"""
    N = len(A)
    C = [[0.0] * N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            for k in range(N):
                C[i][j] += A[i][k] * B[k][j]
    return C

def matrix_multiplication_numpy(A, B):
    """使用 NumPy 的 dot 函数进行矩阵乘法"""
    return np.dot(A, B)

def main():
    # 设置随机种子以保证可重复性
    np.random.seed(42)
    
    # 生成随机矩阵大小 (512-2048)
    N = random.randint(512, 2048)
    print(f"矩阵大小: N = {N}")
    print(f"浮点运算次数: 2 * {N}^3 = {2 * N**3:,}")
    
    # 生成随机矩阵
    A = np.random.rand(N, N)
    B = np.random.rand(N, N)
    
    # 使用 NumPy 进行矩阵乘法
    print("\n使用 NumPy 进行矩阵乘法...")
    start_time = time.time()
    C = matrix_multiplication_numpy(A, B)
    end_time = time.time()
    
    elapsed_time = end_time - start_time
    
    # 计算性能指标
    flops = 2 * N**3
    gflops = flops / (elapsed_time * 1e9)
    
    print(f"\n========== V1: Python (NumPy) 结果 ==========")
    print(f"矩阵大小: {N} x {N}")
    print(f"运行时间: {elapsed_time:.6f} 秒")
    print(f"GFLOPS: {gflops:.4f}")
    print(f"=============================================")
    
    return elapsed_time, gflops, N

if __name__ == "__main__":
    main()