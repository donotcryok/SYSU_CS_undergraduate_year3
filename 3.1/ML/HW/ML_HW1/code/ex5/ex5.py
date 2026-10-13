# -*- coding: utf-8 -*-
"""
ex5.py  系统可靠性蒙特卡洛模拟
给定一个由离散元件组成的系统，每个元件有已知可靠性。
系统结构：输入有一半概率经过A，若A成功（≤0.85）则系统成功；
另一半概率经过B和C，B成功（<0.95）且C成功（<0.90）则系统成功。
用蒙特卡洛方法模拟系统可靠性，并与概率理论结果对比。
"""
import numpy as np
import matplotlib.pyplot as plt
import csv
import os

# 设置中文字体显示
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 系统参数
RELIABILITY_A = 0.85
RELIABILITY_B = 0.95
RELIABILITY_C = 0.90
NUM_SIMULATIONS = 100000

def simulate_system_once():
    # 随机选择路径：50%概率走路径A，50%概率走路径B+C
    if np.random.random() < 0.5:
        # 路径A：生成0-1随机数，如果≤0.85则成功
        return 1 if np.random.random() <= RELIABILITY_A else 0
    else:
        # 路径B+C：两个组件都必须成功
        b_success = np.random.random() < RELIABILITY_B
        c_success = np.random.random() < RELIABILITY_C
        return 1 if (b_success and c_success) else 0

def monte_carlo_simulation(num_trials=NUM_SIMULATIONS):
    success_count = 0
    
    for i in range(num_trials):
        success_count += simulate_system_once()
    
    reliability = success_count / num_trials
    return reliability, success_count

def calculate_theoretical_reliability():
    # P(系统成功) = P(路径A成功) + P(路径B+C成功)
    # = 0.5 * 0.85 + 0.5 * 0.95 * 0.90
    prob_a = 0.5 * RELIABILITY_A
    prob_bc = 0.5 * RELIABILITY_B * RELIABILITY_C
    theoretical = prob_a + prob_bc
    return theoretical

def run_multiple_experiments(num_experiments=50, trials_per_exp=10000):
    results = []
    theoretical = calculate_theoretical_reliability()
    
    print(f"运行 {num_experiments} 次实验，每次 {trials_per_exp} 次试验...")
    
    for i in range(num_experiments):
        reliability, _ = monte_carlo_simulation(trials_per_exp)
        error = abs(reliability - theoretical)
        results.append((i+1, reliability, error))
        
        if (i+1) % 10 == 0:
            print(f"实验 {i+1}: 可靠性 = {reliability:.6f}, 误差 = {error:.6f}")
    
    return results

def save_results(sim_reliability, theoretical_reliability, results=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 保存主要结果
    filename = os.path.join(script_dir, 'system_reliability_results.txt')
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("系统可靠性蒙特卡洛模拟结果\n")
        f.write("="*50 + "\n")
        f.write(f"模拟次数: {NUM_SIMULATIONS}\n")
        f.write(f"理论可靠性: {theoretical_reliability:.6f}\n")
        f.write(f"模拟可靠性: {sim_reliability:.6f}\n")
        f.write(f"绝对误差: {abs(sim_reliability - theoretical_reliability):.6f}\n")
        f.write(f"相对误差: {abs(sim_reliability - theoretical_reliability)/theoretical_reliability*100:.3f}%\n")
        f.write("\n系统参数:\n")
        f.write(f"组件A可靠性: {RELIABILITY_A}\n")
        f.write(f"组件B可靠性: {RELIABILITY_B}\n")
        f.write(f"组件C可靠性: {RELIABILITY_C}\n")
    
    print(f"结果已保存到: {filename}")
    
    # 保存收敛性数据
    if results:
        csv_filename = os.path.join(script_dir, 'convergence_data.csv')
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["实验次数", "模拟可靠性", "绝对误差"])
            for exp_num, reliability, error in results:
                writer.writerow([exp_num, f"{reliability:.6f}", f"{error:.6f}"])
        print(f"收敛性数据已保存到: {csv_filename}")

def plot_convergence(results, theoretical_reliability):
    exp_nums = [r[0] for r in results]
    reliabilities = [r[1] for r in results]
    errors = [r[2] for r in results]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    
    # 可靠性收敛图
    ax1.plot(exp_nums, reliabilities, 'b-', alpha=0.7, label='模拟可靠性')
    ax1.axhline(y=theoretical_reliability, color='r', linestyle='--', 
                label=f'理论值 = {theoretical_reliability:.6f}')
    ax1.set_xlabel('实验次数')
    ax1.set_ylabel('系统可靠性')
    ax1.set_title('系统可靠性收敛性分析')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 误差收敛图
    ax2.plot(exp_nums, errors, 'r-', alpha=0.7, label='绝对误差')
    ax2.set_xlabel('实验次数')
    ax2.set_ylabel('绝对误差')
    ax2.set_title('误差收敛性分析')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存图片
    script_dir = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(script_dir, 'system_reliability_convergence.png')
    plt.savefig(save_path, dpi=200, bbox_inches='tight')
    print(f"收敛性图表已保存为: {save_path}")
    plt.show()

if __name__ == "__main__":
    # 设置随机种子以增强随机性
    np.random.seed(None)
    
    print("系统可靠性蒙特卡洛模拟")
    print("="*50)
    
    # 计算理论值
    theoretical_reliability = calculate_theoretical_reliability()
    print(f"理论可靠性: {theoretical_reliability:.6f}")
    
    # 理论计算过程展示
    print(f"\n理论计算过程:")
    print(f"P(系统成功) = P(路径A成功) + P(路径B+C成功)")
    print(f"             = 0.5 × {RELIABILITY_A} + 0.5 × {RELIABILITY_B} × {RELIABILITY_C}")
    print(f"             = {0.5 * RELIABILITY_A:.3f} + {0.5 * RELIABILITY_B * RELIABILITY_C:.3f}")
    print(f"             = {theoretical_reliability:.6f}")
    
    # 执行主要模拟
    print(f"\n开始蒙特卡洛模拟 ({NUM_SIMULATIONS} 次试验)...")
    sim_reliability, success_count = monte_carlo_simulation()
    
    print(f"\n主要模拟结果:")
    print(f"成功次数: {success_count}")
    print(f"模拟可靠性: {sim_reliability:.6f}")
    print(f"理论可靠性: {theoretical_reliability:.6f}")
    print(f"绝对误差: {abs(sim_reliability - theoretical_reliability):.6f}")
    print(f"相对误差: {abs(sim_reliability - theoretical_reliability)/theoretical_reliability*100:.3f}%")
    
    # 运行收敛性分析
    print(f"\n收敛性分析...")
    convergence_results = run_multiple_experiments()
    
    # 保存结果
    save_results(sim_reliability, theoretical_reliability, convergence_results)
    
    # 绘制收敛性图表
    plot_convergence(convergence_results, theoretical_reliability)
    
    print(f"\n结论:")
    print(f"蒙特卡洛模拟结果 ({sim_reliability:.6f}) 与理论值 ({theoretical_reliability:.6f}) 非常接近，")
    print(f"验证了概率理论的正确性和蒙特卡洛方法的有效性。")