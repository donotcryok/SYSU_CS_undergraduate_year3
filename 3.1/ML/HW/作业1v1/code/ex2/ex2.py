# -*- coding: utf-8 -*-
"""
ex2.py  蒙特卡洛方法估算积分 ∫₀¹ x³ dx
"""
import numpy as np
import os
import matplotlib.pyplot as plt

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def monte_carlo_integral(N, repeat=100):
    estimates = []
    for _ in range(repeat):
        x = np.random.uniform(0, 1, N)
        fx = x ** 3
        estimate = np.mean(fx)  # 区间长度为1
        estimates.append(estimate)
    estimates = np.array(estimates)
    mean_val = np.mean(estimates)
    var_val = np.var(estimates)
    abs_err = abs(mean_val - 0.25)
    return mean_val, var_val, abs_err, estimates

def print_table(results):
    print("\n蒙特卡洛方法估算∫₀¹ x³ dx 结果统计表")
    print(f"{'N':<8}{'均值':<12}{'方差':<12}{'绝对误差':<12}")
    for r in results:
        print(f"{r[0]:<8}{r[1]:<12.6f}{r[2]:<12.6f}{r[3]:<12.6f}")
    print(f"真实值: 0.25")

def save_results(results, filename=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if filename is None:
        filename = os.path.join(script_dir, 'integral_estimation_results.txt')
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("N\t均值\t方差\t绝对误差\n")
        for r in results:
            f.write(f"{r[0]}\t{r[1]:.6f}\t{r[2]:.6f}\t{r[3]:.6f}\n")
    csv_filename = os.path.splitext(filename)[0] + '.csv'
    with open(csv_filename, 'w', encoding='utf-8') as f:
        f.write("N,均值,方差,绝对误差\n")
        for r in results:
            f.write(f"{r[0]},{r[1]:.6f},{r[2]:.6f},{r[3]:.6f}\n")
    print(f"结果已保存到: {filename} 和 {csv_filename}")

def plot_convergence(results, save_dir=None):
    N_list = [r[0] for r in results]
    means = [r[1] for r in results]
    errors = [r[3] for r in results]
    plt.figure(figsize=(8,6))
    plt.plot(N_list, means, 'bo-', label='估算均值')
    plt.axhline(y=0.25, color='r', linestyle='--', label='真实值0.25')
    plt.xlabel('样本数量 N')
    plt.ylabel('积分估算值')
    plt.title('蒙特卡洛估算∫₀¹ x³ dx的收敛性')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    if save_dir is None:
        save_dir = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(save_dir, 'integral_convergence.png')
    plt.savefig(save_path, dpi=200, bbox_inches='tight')
    print(f"收敛性图表已保存为: {save_path}")
    plt.close()

if __name__ == "__main__":
    # 设置随机种子以增强随机性
    np.random.seed(None)  # 使用系统时间作为种子
    
    N_list = [5, 10, 20, 30, 40, 50, 60, 70, 80, 100]
    repeat_times = 100
    results = []
    for N in N_list:
        mean_val, var_val, abs_err, _ = monte_carlo_integral(N, repeat_times)
        results.append((N, mean_val, var_val, abs_err))
    print_table(results)
    save_results(results)
    plot_convergence(results)
