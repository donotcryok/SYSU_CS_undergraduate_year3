# 用户手动任务清单

## 一、环境准备

### 1. 创建并激活 Python 虚拟环境

**步骤 1: 创建虚拟环境**

在项目根目录 `e:/3.2/Big_Data/my_lab/lab7` 下执行以下命令：

```bash
python -m venv .venv
```

这将创建一个名为 `.venv` 的虚拟环境文件夹。

**步骤 2: 激活虚拟环境**

根据您的操作系统，选择对应的激活命令：

- **Windows (CMD)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```

- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

- **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

激活成功后，终端提示符前会出现 `(.venv)` 标识。

### 2. 安装依赖包

在激活虚拟环境后，执行以下命令安装本次实验所需的依赖库：

```bash
pip install pandas numpy scikit-learn matplotlib seaborn tqdm
```

或者逐个安装：

```bash
pip install pandas
pip install numpy
pip install scikit-learn
pip install matplotlib
pip install seaborn
pip install tqdm
```

**依赖库说明**：
- `pandas`: 数据处理与分析
- `numpy`: 数值计算
- `scikit-learn`: 机器学习算法（TF-IDF、余弦相似度等）
- `matplotlib`: 数据可视化
- `seaborn`: 统计数据可视化
- `tqdm`: 进度条显示（可选，用于评估过程进度提示）

---

## 二、运行步骤

1. [ ] 进入项目目录: `cd e:/3.2/Big_Data/my_lab/lab7`
2. [ ] 创建虚拟环境: `python -m venv .venv`
3. [ ] 激活虚拟环境（根据操作系统选择命令）
4. [ ] 安装依赖包: `pip install pandas numpy scikit-learn matplotlib seaborn`
5. [ ] 进入源代码目录: `cd src`
6. [ ] 运行主程序: `python main.py`
7. [ ] 检查 `img/` 目录下生成的可视化图表
8. [ ] 编译 LaTeX 报告: `xelatex lab7.tex`

---

## 三、注意事项

- 确保 `data/` 目录下有完整的数据文件 (movies.csv, ratings.csv, tags.csv)
- 首次运行可能需要较长时间进行数据预处理和模型训练
- 如遇到内存问题，可调整 `main.py` 中的数据采样比例
- 运行完成后，虚拟环境可通过 `deactivate` 命令退出

---

## 四、预期输出

运行 `python main.py` 后，将在 `img/` 目录下生成以下可视化图表：

- `img/recall_comparison.png` - 召回率对比柱状图
- `img/coverage_comparison.png` - 覆盖率对比柱状图
- `img/diversity_comparison.png` - 多样性对比柱状图
- `img/metrics_comparison.png` - 综合指标对比柱状图
- `img/radar_chart.png` - 性能雷达图
- `img/all_metrics_comparison.png` - 综合指标子图对比
- `img/evaluation_results.csv` - 评估结果数据表