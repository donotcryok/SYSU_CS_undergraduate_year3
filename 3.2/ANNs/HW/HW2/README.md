# 中文短新闻主题分类

基于 BiLSTM+Attention 与 Transformer 的中文短新闻主题多分类系统，使用 TNEWS 数据集（CLUE 基准），将新闻文本自动分类到 15 个主题类别。

## 项目结构

```
lab2/
├── src/
│   ├── dataset.py      # 数据预处理：清洗、字符级切分、词表构建、DataLoader
│   ├── models.py       # 双模型定义：BiLSTM+Bahdanau Attention / Transformer Encoder
│   ├── train.py        # 训练流水线（AdamW + Label Smoothing + EarlyStopping）
│   └── eval.py         # 评估与可视化（混淆矩阵、损失曲线、Top-K 错误分析）
├── data/
│   ├── train.json      # 训练集（53,360 条）
│   ├── dev.json        # 测试集（10,000 条）
│   └── labels.json     # 15 个类别名称映射
├── models/             # 模型权重与训练历史
├── img/                # 可视化输出
├── HW2.tex             # LaTeX 实验报告
└── README.md           # 本文件
```

## 环境要求

| 组件 | 版本/说明 |
|------|----------|
| OS | Linux (WSL2 Ubuntu 22.04 测试) |
| Python | 3.10+ |
| Conda Env | `nlp_hw2` |
| PyTorch | 2.6.0+cu124 |
| CUDA | 12.4（RTX 4060 8GB 测试；≥6GB VRAM 可运行） |
| jieba | 0.42.1 |
| scikit-learn | 1.7+ |
| matplotlib | 3.10+（需中文字体，如 WenQuanYi Micro Hei） |

## 开始指南（本机）
```bash
conda create -n nlp_hw2 python=3.10 -y
conda activate nlp_hw2
```

### 2. 安装 PyTorch（CUDA 12.4）

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

> 若无需 GPU 训练，将 `cu124` 替换为 `cpu`。

### 3. 安装其他依赖

```bash
pip install jieba scikit-learn matplotlib
```

### 4. 安装中文字体（Linux/WSL）

```bash
sudo apt update && sudo apt install fonts-wqy-microhei -y
```

> macOS 用户可使用系统自带的中文字体，无需此步骤。

### 5. 验证环境

```bash
python -c "import torch; print(f'PyTorch {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}')"
```

预期输出：

```
PyTorch 2.6.0+cu124
CUDA Available: True
```

### 6. 下载数据集

TNEWS 数据集应已包含在 `data/` 目录下：

```
data/train.json    # 训练集（53,360 条）
data/dev.json      # 测试集（10,000 条）
data/labels.json   # 类别标签映射
```

> 若缺失，可从 [CLUE 官网](https://github.com/CLUEbenchmark/CLUE) 下载 TNEWS 数据集并放入 `data/` 目录。

### 7. 训练模型

```bash
# 训练 BiLSTM + Bahdanau Attention（≈5 分钟，RTX 4060）
python src/train.py --model_type bilstm --lr 1e-3 --dropout 0.4 --patience 8

# 训练 Transformer Encoder + 均值池化（≈6 分钟，RTX 4060）
python src/train.py --model_type transformer --lr 1e-3 --dropout 0.4 --patience 8
```

训练完成后，模型权重和训练历史保存至 `models/` 目录：

| 文件 | 说明 |
|------|------|
| `models/bilstm_best.pt` | BiLSTM 最佳模型权重 |
| `models/transformer_best.pt` | Transformer 最佳模型权重 |
| `models/bilstm_history.json` | BiLSTM 训练历史（损失、准确率、F1） |
| `models/transformer_history.json` | Transformer 训练历史 |

### 8. 评估模型

```bash
python src/eval.py --num_workers 0
```

评估输出：

| 输出 | 位置 |
|------|------|
| 整体指标（Acc/Macro-F1/逐类 P/R/F1） | 控制台 |
| Top-5 混淆对 | 控制台 |
| 完整评估数据 | `models/eval_results.json` |
| 损失曲线 | `img/loss_curves_loss.png` |
| 准确率曲线 | `img/loss_curves_accuracy.png` |
| 验证损失对比 | `img/loss_curves_val_loss.png` |
| 验证 Macro-F1 对比 | `img/loss_curves_val_f1.png` |
| BiLSTM 混淆矩阵 | `img/confusion_matrix_bilstm.png` |
| Transformer 混淆矩阵 | `img/confusion_matrix_transformer.png` |

