# -*- coding: utf-8 -*-
"""
主程序入口
1. Harris 角点检测 (sudoku.png)
2. 特征提取与匹配 (uttower1.jpg, uttower2.jpg)
3. 两图拼接 (uttower1.jpg, uttower2.jpg) - SIFT 和 HOG
4. 多图拼接 (yosemite1.jpg ~ yosemite4.jpg)
"""

import os
import sys

# 确保结果目录存在
os.makedirs("../results/1", exist_ok=True)

print("=" * 60)
print("模式识别课程第一次作业 - 全景图拼接")
print("=" * 60)

# ========== Task 1: Harris 角点检测 ==========
print("\n" + "=" * 60)
print("Task 1: Harris 角点检测")
print("=" * 60)

from harris import main as harris_main
harris_main()

# ========== Task 2: 特征提取与匹配 ==========
print("\n" + "=" * 60)
print("Task 2: 特征提取与匹配")
print("=" * 60)

from feature_match import main as feature_match_main
feature_match_main()

# ========== Task 3: 两图拼接 ==========
print("\n" + "=" * 60)
print("Task 3: 两图拼接")
print("=" * 60)

from stitch import main as stitch_main
stitch_main()

# ========== Task 4: 多图拼接 ==========
print("\n" + "=" * 60)
print("Task 4: 多图拼接")
print("=" * 60)

from multi_stitch import main as multi_stitch_main
multi_stitch_main()

# ========== 完成 ==========
print("\n" + "=" * 60)
print("所有任务完成！")
print("=" * 60)