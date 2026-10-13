# -*- coding: utf-8 -*-
"""
ex3.py  蒙特卡洛方法估算二维积分
"""
import numpy as np
import matplotlib.pyplot as plt
import csv
import os

def f(x, y):
	# f(x, y) = (y^2 * exp(-y^2) + x^4 * exp(-x^2)) / (x * exp(-x^2))
	return (y**2 * np.exp(-y**2) + x**4 * np.exp(-x**2)) / (x * np.exp(-x**2))

def monte_carlo_integral(N, repeat=100):
	x_low, x_high = 2, 4
	y_low, y_high = -1, 1
	area = (x_high - x_low) * (y_high - y_low)
	estimates = []
	for _ in range(repeat):
		x = np.random.uniform(x_low, x_high, N)
		y = np.random.uniform(y_low, y_high, N)
		vals = f(x, y)
		integral = area * np.mean(vals)
		estimates.append(integral)
	estimates = np.array(estimates)
	mean_val = np.mean(estimates)
	var_val = np.var(estimates)
	std_val = np.std(estimates)
	# 理论值未知，误差以mean_val为主
	return mean_val, var_val, std_val, estimates

def print_table(results, true_val=None):
	print("N\t均值\t\t方差\t\t标准差\t误差")
	for r in results:
		N, mean_val, var_val, std_val = r[:4]
		if true_val is not None:
			error = abs(mean_val - true_val)
		else:
			error = ''
		print(f"{N}\t{mean_val:.6f}\t{var_val:.6f}\t{std_val:.6f}\t{error}")

def save_results(results, true_val=None, filename=None):
	script_dir = os.path.dirname(os.path.abspath(__file__))
	if filename is None:
		filename = os.path.join(script_dir, 'integral_estimation_results.txt')
	else:
		filename = os.path.join(script_dir, filename)
	with open(filename, 'w', encoding='utf-8') as f:
		f.write("二维积分蒙特卡洛估算结果\n")
		f.write(f"{'N':<8} {'均值':<12} {'方差':<12} {'标准差':<12} {'误差':<12}\n")
		for r in results:
			N, mean_val, var_val, std_val = r[:4]
			if true_val is not None:
				error = abs(mean_val - true_val)
				f.write(f"{N:<8} {mean_val:<12.6f} {var_val:<12.6f} {std_val:<12.6f} {error:<12.6f}\n")
			else:
				f.write(f"{N:<8} {mean_val:<12.6f} {var_val:<12.6f} {std_val:<12.6f}\n")
	csv_filename = os.path.splitext(filename)[0] + '.csv'
	with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
		if true_val is not None:
			writer = csv.writer(csvfile)
			writer.writerow(["N", "均值", "方差", "标准差", "误差"])
			for r in results:
				N, mean_val, var_val, std_val = r[:4]
				error = abs(mean_val - true_val)
				writer.writerow([N, f"{mean_val:.6f}", f"{var_val:.6f}", f"{std_val:.6f}", f"{error:.6f}"])
		else:
			writer = csv.writer(csvfile)
			writer.writerow(["N", "均值", "方差", "标准差"])
			for r in results:
				N, mean_val, var_val, std_val = r[:4]
				writer.writerow([N, f"{mean_val:.6f}", f"{var_val:.6f}", f"{std_val:.6f}"])
	print(f"结果已保存: {filename}, {csv_filename}")

def plot_convergence(results, save_dir=None):
	N_values = [r[0] for r in results]
	means = [r[1] for r in results]
	stds = [r[3] for r in results]
	fig, ax = plt.subplots(figsize=(8,5))
	ax.plot(N_values, means, 'bo-', label='均值')
	ax.set_xlabel('采样点数 N')
	ax.set_ylabel('积分估计均值')
	ax.set_title('二维积分蒙特卡洛估算收敛性')
	ax.grid(True)
	plt.tight_layout()
	if save_dir is None:
		save_dir = os.path.dirname(os.path.abspath(__file__))
	save_path = os.path.join(save_dir, 'integral_convergence.png')
	plt.savefig(save_path, dpi=200, bbox_inches='tight')
	print(f"收敛性图已保存: {save_path}")
	plt.show()

if __name__ == "__main__":
	# 设置随机种子以增强随机性
	np.random.seed(None)  # 使用系统时间作为种子
	
	N_list = [10, 20, 30, 40, 50, 60, 70, 80, 100, 200, 500]
	repeat_times = 100
	results = []
	for N in N_list:
		mean_val, var_val, std_val, estimates = monte_carlo_integral(N, repeat_times)
		results.append((N, mean_val, var_val, std_val, estimates))
	# 用最大N的均值作为近似真值
	approx_true_val = results[-1][1]
	print_table(results, true_val=approx_true_val)
	save_results(results, true_val=approx_true_val)
	plot_convergence(results)

