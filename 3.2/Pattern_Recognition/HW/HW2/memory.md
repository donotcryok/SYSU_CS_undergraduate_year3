# 工作日志 (Memory)

## 项目概述
- **项目名称**: 基于 PCA 的图像压缩实验
- **实验编号**: Lab 2
- **开始时间**: 2026年5月23日
- **状态**: ✅ 全部完成，两脚本均已通过运行验证

---

## 已完成步骤

### Step 1: 环境与文档初始化 ✅
- 创建 `todo.md`，包含虚拟环境创建、激活、依赖安装的完整命令
- 创建 `memory.md`，初始化工作日志基础结构

### Step 2: 核心 PCA 算法实现 ✅
- 文件: [`src/pca_core.py`](src/pca_core.py)
- 实现 `PCA` 类，包含 `fit()`, `transform()`, `fit_transform()`, `inverse_transform()`, `compression_ratio()`
- 自测: 全成分重建 RMSE = 9.59e-16（数值精度范围内完美重建）

### Step 3: Eigen Face 压缩实验 ✅
- 文件: [`src/face_task.py`](src/face_task.py)
- 实际数据: 5000 张人脸，32×32（1024 维），像素范围 [-127.87, 127.13]
- 实验结果:
  - k=10:  累计方差贡献率 67.44%，RMSE 23.18，维度压缩比 0.98%
  - k=50:  累计方差贡献率 86.97%，RMSE 14.66，维度压缩比 4.88%
  - k=100: 累计方差贡献率 93.29%，RMSE 10.52，维度压缩比 9.77%
  - k=150: 累计方差贡献率 95.94%，RMSE 8.18，维度压缩比 14.65%
- 输出 7 张图: eigen_faces.jpg, face_variance.jpg, recovered_faces_comparison.jpg, recovered_faces_top_{10,50,100,150}.jpg

### Step 4: 彩色图像压缩实验 ✅
- 文件: [`src/rgb_task.py`](src/rgb_task.py)
- 实际数据: woman.png，1024×1024 RGB
- 实验结果 (三通道平均):
  - k=10:  RMSE 0.052，压缩比 0.021，耗时 0.87s
  - k=50:  RMSE 0.022，压缩比 0.099，耗时 0.87s
  - k=100: RMSE 0.015，压缩比 0.196，耗时 0.86s
  - k=150: RMSE 0.011，压缩比 0.294，耗时 0.86s
- 输出 5 张图: rgb_comparison.jpg, rgb_recovered_k{10,50,100,150}.jpg, rgb_metrics.jpg

### Step 5: 撰写实验报告 ✅
- 文件: [`lab2.tex`](lab2.tex)，共 ~600 行
- 报告结构完整: 实验简述 → 分析设计(含完整数学推导) → 核心代码 → 结果分析(含 10+ 张图表) → 实验总结

### Step 6: 运行验证 ✅
- `pca_core.py` 自测: 通过 (Exit 0)
- `face_task.py`: 通过 (Exit 0)，生成 7 张结果图
- `rgb_task.py`: 通过 (Exit 0)，生成 5 张结果图

---

## 踩坑记录
1. **图像尺寸假设错误**: 初始假设 faces.mat 为 64×64 (4096维)，实际为 32×32 (1024维)。已修正 `FACE_H, FACE_W = 32, 32` 并同步更新 lab2.tex 中所有引用。
2. **图像后缀**: 用户指定 `woman.jpg` 但实际文件为 `woman.png`，脚本中已使用正确路径。
3. **matplotlib 中文字体缺失**: Windows 环境默认无中文字体，Eigenfaces 标题中的"主成分/特征脸"显示为方框。不影响图像保存和 LaTeX 报告使用。
4. **LaTeX 模板覆盖**: `lab2.tex` 原有实验1（全景图拼接）内容，全文重写为 PCA 实验报告。
5. **SVD full_matrices=False**: 对 5000×1024 的人脸数据矩阵，使用 `full_matrices=False` 大幅节省内存，是正确的选择。
6. **按列压缩设计**: RGB 图像按列压缩（W=1024个 H=1024维样本），三通道 SVD 复杂度均为 O(1024³)，每个 k 值约 2.6s 完成三个通道。
