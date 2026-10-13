# -*- coding: utf-8 -*-
"""
ex1.py  蒙特卡洛方法估算π
  1. 在单位正方形内随机撒点，判断是否落在1/4圆内。
  2. 计算每组N下100次实验的π均值和方差。
  3. 输出详细统计表格，包括标准差和误差分析。
  4. 可选绘制撒点示意图和收敛性分析图。
"""

import numpy as np
import matplotlib.pyplot as plt
# 中文字体显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def monte_carlo_pi(N, repeat=100):
    pi_estimates = []
    for i in range(repeat):
        x = np.random.uniform(0, 1, N)
        y = np.random.uniform(0, 1, N)
        inside = (x**2 + y**2) <= 1
        pi_estimate = 4 * np.sum(inside) / N
        pi_estimates.append(pi_estimate)
    
    pi_estimates = np.array(pi_estimates)
    mean_val = np.mean(pi_estimates)
    var_val = np.var(pi_estimates)
    std_val = np.std(pi_estimates)
    
    return mean_val, var_val, std_val, pi_estimates

def print_detailed_table(results):
    print("\n" + "="*80)
    print("蒙特卡洛方法估算π - 实验结果统计表")
    print("="*80)
    print(f"{'N':<8} {'均值':<12} {'方差':<12} {'标准差':<12} {'误差':<12} {'相对误差(%)':<12}")
    print("-"*80)
    
    true_pi = np.pi
    for result in results:
        N, mean_val, var_val, std_val = result[:4]
        error = abs(mean_val - true_pi)
        relative_error = (error / true_pi) * 100
        
        print(f"{N:<8} {mean_val:<12.6f} {var_val:<12.6f} {std_val:<12.6f} {error:<12.6f} {relative_error:<12.2f}")
    
    print("-"*80)
    print(f"真实π值: {true_pi:.6f}")
    print("="*80)

def analyze_convergence(results):
    print("\n收敛性分析:")
    print("-"*50)
    N_values = [result[0] for result in results]
    errors = [abs(result[1] - np.pi) for result in results]
    
    for i, (N, error) in enumerate(zip(N_values, errors)):
        if i > 0:
            improvement = errors[i-1] - error
            print(f"N={N:>4}: 误差={error:.6f}, 相比N={N_values[i-1]}改善: {improvement:+.6f}")
        else:
            print(f"N={N:>4}: 误差={error:.6f}")

import csv
import os

def save_results_to_file(results, filename=None):
    # 自动定位到ex1.py所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if filename is None:
        filename = os.path.join(script_dir, 'pi_estimation_results.txt')
    else:
        filename = os.path.join(script_dir, filename)
    # 保存txt
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("蒙特卡洛方法估算π - 实验结果\n")
        f.write("="*50 + "\n")
        f.write(f"实验时间: {np.datetime64('now')}\n")
        f.write(f"每组实验重复次数: 100次\n\n")
        f.write(f"{'N':<8} {'均值':<12} {'方差':<12} {'标准差':<12} {'误差':<12}\n")
        f.write("-"*60 + "\n")
        for result in results:
            N, mean_val, var_val, std_val = result[:4]
            error = abs(mean_val - np.pi)
            f.write(f"{N:<8} {mean_val:<12.6f} {var_val:<12.6f} {std_val:<12.6f} {error:<12.6f}\n")
        f.write(f"\n真实π值: {np.pi:.6f}\n")
    print(f"\n结果已保存到文件: {filename}")

    # 保存csv
    csv_filename = os.path.splitext(filename)[0] + '.csv'
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["N", "均值", "方差", "标准差", "误差"])
        for result in results:
            N, mean_val, var_val, std_val = result[:4]
            error = abs(mean_val - np.pi)
            writer.writerow([N, f"{mean_val:.6f}", f"{var_val:.6f}", f"{std_val:.6f}", f"{error:.6f}"])
    print(f"结果已保存为CSV: {csv_filename}")

def plot_convergence(results, save_dir=None):
    import os
    N_values = [result[0] for result in results]
    means = [result[1] for result in results]
    errors = [abs(mean - np.pi) for mean in means]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))

    # 估算值随N变化
    ax1.plot(N_values, means, 'bo-', label='估算值')
    ax1.axhline(y=np.pi, color='r', linestyle='--', label=f'真实π={np.pi:.6f}')
    ax1.set_xlabel('样本数量 N')
    ax1.set_ylabel('π 估算值')
    ax1.set_title('蒙特卡洛估算π的收敛性')
    ax1.legend()
    ax1.grid(True)

    # 误差随N变化
    ax2.loglog(N_values, errors, 'ro-', label='绝对误差')
    ax2.set_xlabel('样本数量 N')
    ax2.set_ylabel('绝对误差')
    ax2.set_title('估算误差随样本数量变化')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()

    # 保存图片
    if save_dir is None:
        save_dir = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(save_dir, 'pi_convergence.png')
    plt.savefig(save_path, dpi=200, bbox_inches='tight')
    print(f"收敛性图表已保存为: {save_path}")
    plt.show()

def plot_points(N):
	x = np.random.uniform(0, 1, N)
	y = np.random.uniform(0, 1, N)
	inside = (x**2 + y**2) <= 1
	plt.figure(figsize=(5,5))
	plt.scatter(x[inside], y[inside], color='red', s=10, label='Inside (红)')
	plt.scatter(x[~inside], y[~inside], color='green', s=10, label='Outside (绿)')
	circle = plt.Circle((0,0),1, color='blue', fill=False, linewidth=2, linestyle='--', label='1/4圆')
	plt.gca().add_patch(circle)
	plt.xlim(0,1)
	plt.ylim(0,1)
	plt.xlabel('x')
	plt.ylabel('y')
	plt.title(f'蒙特卡洛撒点示意图 (N={N})')
	plt.legend()
	plt.gca().set_aspect('equal')
	plt.show()

if __name__ == "__main__":
    # 设置随机种子以增强随机性
    np.random.seed(None)  # 使用系统时间作为种子，随机性更强
    
    print("开始蒙特卡洛方法估算π实验...")
    # 定义实验参数
    N_list = [20, 50, 100, 200, 300, 500, 1000, 5000]
    repeat_times = 100

    # 存储所有结果
    results = []

    for N in N_list:
        mean_val, var_val, std_val, pi_estimates = monte_carlo_pi(N, repeat_times)
        results.append((N, mean_val, var_val, std_val, pi_estimates))

    print("实验完成，主要统计结果如下：")
    print_detailed_table(results)
    analyze_convergence(results)
    save_results_to_file(results)
    plot_convergence(results)
    plot_points(500)
