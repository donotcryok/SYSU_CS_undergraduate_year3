# 模式识别课程第一次作业 - 项目记忆库

## 项目概述
**作业名称**：全景图拼接  
**截止日期**：2026年4月30日 24:00  
**提交邮箱**：pr202604@163.com  
**邮件主题**：学号-姓名-第一次平时作业

## 核心目标
1. 实现并熟悉 **Harris 角点检测** 算法
2. 实现并熟悉 **RANSAC 算法**
3. 应用 **SIFT** 和 **HOG** 特征描述子
4. 实现全景图拼接

## 算法流程
```
Harris角点检测 → SIFT/HOG特征描述 → 特征匹配 → RANSAC求解变换矩阵 → 图像变换 → 图像拼接
```

## 目录结构
```
HW1/
├── src/                    # Python 源码目录
│   ├── harris.py          # Harris 角点检测实现
│   ├── feature_match.py   # SIFT/HOG 特征匹配
│   ├── ransac.py          # RANSAC 算法实现
│   ├── stitch.py          # 图像拼接
│   └── utils.py           # 工具函数
├── images/                 # 输入图像目录
│   └── 1/                 # 第一次作业图像
│       ├── sudoku.png     # Harris 角点检测测试图
│       ├── uttower1.jpg   # 拼接图像1
│       ├── uttower2.jpg   # 拼接图像2
│       ├── yosemite1.jpg  # 多图拼接1
│       ├── yosemite2.jpg  # 多图拼接2
│       ├── yosemite3.jpg  # 多图拼接3
│       └── yosemite4.jpg  # 多图拼接4
├── results/1/             # 输出结果目录
│   ├── sudoku_keypoints.png      # Task1: Harris角点检测结果
│   ├── uttower_match.png         # Task2: 特征匹配结果
│   ├── uttower_stitching_sift.png # Task3: SIFT拼接结果
│   ├── uttower_stitching_hog.png  # Task3: HOG拼接结果
│   └── yosemite_stitching.png     # Task4: 多图拼接结果
├── img/                   # LaTeX 报告插图目录
├── lab1.tex               # 实验报告源码
├── todo.md                # 人工操作指南
└── memory_bank.md         # 本文件
```

## 任务分解

### Task 1: Harris 角点检测
**输入**: `images/1/sudoku.png`  
**输出**: `results/1/sudoku_keypoints.png`  
**要求**:
- 自己实现 Harris 算法
- 实现去除假阳性点的后处理逻辑

**Harris 算法核心公式**:
```
M = Σw(x,y) * [Ix²    Ix*Iy]
              [Ix*Iy  Iy²  ]

R = det(M) - k * trace(M)²
  = λ1*λ2 - k*(λ1+λ2)²
```
其中 k 通常取 0.04~0.06

### Task 2: 关键点提取与描述
**输入**: `images/1/uttower1.jpg`, `images/1/uttower2.jpg`  
**输出**: `results/1/uttower_match.png`  
**要求**:
- 使用自建 Harris 检测器提取关键点
- 使用 SIFT 和 HOG 特征作为描述子
- 计算欧氏距离进行匹配

### Task 3: 两图拼接
**输入**: `images/1/uttower1.jpg`, `images/1/uttower2.jpg`  
**输出**: `results/1/uttower_stitching_sift.png`, `results/1/uttower_stitching_hog.png`  
**要求**:
- 使用 RANSAC 求解仿射变换矩阵
- 分别使用 SIFT 和 HOG 特征进行拼接

### Task 4: 多图拼接
**输入**: `images/1/yosemite1.jpg` ~ `yosemite4.jpg`  
**输出**: `results/1/yosemite_stitching.png`  
**要求**:
- 基于 SIFT + RANSAC 方法
- 对四张图像进行多图拼接

## 技术决策

### Harris 角点检测实现要点
1. **梯度计算**: 使用 Sobel 算子计算 Ix, Iy
2. **窗口函数**: 使用高斯窗口进行加权
3. **响应函数**: R = det(M) - k * trace(M)²
4. **非极大值抑制**: 去除局部非极大值点
5. **假阳性过滤**: 
   - 阈值过滤: R > threshold
   - 边缘点过滤: 排除边缘附近的点
   - 角点响应值排序，保留前N个最强角点

### RANSAC 算法流程
1. 随机选择最小样本集（3个点用于仿射变换）
2. 计算变换矩阵模型
3. 计算内点数量（误差小于阈值的点）
4. 重复迭代，选择内点最多的模型
5. 使用所有内点重新估计最终模型

### 仿射变换矩阵
```
[x']   [a  b  tx] [x]
[y'] = [c  d  ty] [y]
[1 ]   [0  0  1 ] [1]
```
需要6个参数，至少3对匹配点

## 进度追踪
- [x] 项目结构分析
- [x] memory_bank.md 创建
- [ ] todo.md 创建
- [ ] Python 代码实现
- [ ] LaTeX 报告撰写
- [ ] 结果验证

## 依赖库
- OpenCV (cv2)
- NumPy
- SciPy
- scikit-image (HOG特征)
- Matplotlib (可视化)

---
*最后更新: 2026-04-15*