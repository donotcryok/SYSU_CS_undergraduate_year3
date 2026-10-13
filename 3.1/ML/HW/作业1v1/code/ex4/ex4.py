# -*- coding: utf-8 -*-
"""
ex4.py  蚂蚁走迷宫的概率蒙特卡洛模拟
一只蚂蚁试图从点A(1,1)走到点B(7,7)的7x7网格。每次可上下左右移动，不能出界，
只有中心点(4,4)可被访问0、1或2次，其余点最多访问1次。用蒙特卡洛方法模拟蚂蚁到达B点的概率，模拟20000次。
"""
import numpy as np

n = 7
start = (1, 1)
goal = (n, n)
center = (4, 4)
SIM_TIMES = 20000

# 四个方向：上下左右
directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

def simulate_once():
    pos = start
    visited = {start: 1}  # 记录每个位置被访问的次数
    max_steps = 1000  # 防止无限循环
    steps = 0
    
    while steps < max_steps:
        if pos == goal:
            return 1
        
        # 寻找所有可行的移动方向
        valid_moves = []
        for dx, dy in directions:
            new_x, new_y = pos[0] + dx, pos[1] + dy
            new_pos = (new_x, new_y)
            
            # 检查是否在边界内
            if not (1 <= new_x <= n and 1 <= new_y <= n):
                continue
            
            # 检查访问次数限制
            if new_pos == center:
                # 中心点最多访问2次
                if visited.get(new_pos, 0) < 2:
                    valid_moves.append(new_pos)
            else:
                # 其他点最多访问1次
                if visited.get(new_pos, 0) < 1:
                    valid_moves.append(new_pos)
        
        # 如果没有可行的移动，返回失败
        if not valid_moves:
            return 0
        
        # 随机选择一个可行的移动
        next_pos = valid_moves[np.random.randint(len(valid_moves))]
        
        # 更新位置和访问次数
        pos = next_pos
        visited[pos] = visited.get(pos, 0) + 1
        steps += 1
    
    # 超过最大步数，返回失败
    return 0

def monte_carlo_simulation(num_simulations=SIM_TIMES):
    #执行蒙特卡洛模拟
    success_count = 0
    
    for i in range(num_simulations):
        if i % 5000 == 0:
            print(f"已完成 {i} 次模拟...")
        
        success_count += simulate_once()
    
    probability = success_count / num_simulations
    return probability, success_count

if __name__ == "__main__":
    # 使用系统时间增强随机性
    np.random.seed(None)  # 使用系统时间作为种子
    
    print(f"开始蒙特卡洛模拟，共进行 {SIM_TIMES} 次...")
    probability, success_count = monte_carlo_simulation()
    
    print(f"\n模拟结果:")
    print(f"总模拟次数: {SIM_TIMES}")
    print(f"成功次数: {success_count}")
    print(f"蚂蚁从A(1,1)到B(7,7)的概率估计为: {probability:.5f}")