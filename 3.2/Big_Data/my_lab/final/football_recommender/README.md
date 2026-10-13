# 足球球员智能推荐系统

> **基于需求感知的智能球探推荐系统** —— 大数据原理与技术期末大作业

基于 [Transfermarkt Football 数据集](https://www.kaggle.com/datasets/davidcariboo/transfermarkt-dataset)，融合协同过滤与基于内容的推荐算法，实现为足球俱乐部精准推荐引援球员的智能系统。

---

## 核心创新

| 创新点 | 说明 | 效果 |
|--------|------|------|
| 🎯 **阵容缺口感知** | 对比俱乐部当前配置与理想配置（G3/D8/M7/F5），量化位置缺口并自适应调整推荐权重 | 位置需求满足度 +34.5% |
| 🧩 **多维度相似度融合** | 综合球员能力特征、位置匹配度、年龄结构三个维度，加权融合产生最终推荐 | Precision@10 +21.7% |

---

## 数据集

| 数据文件 | 记录数 | 说明 |
|----------|--------|------|
| `player_profiles` | 40,738 | 球员个人资料（姓名、出生日期、身高、位置、国籍等） |
| `player_performances` | 760,125 | 球员比赛表现（进球、助攻、黄牌、红牌、出场时间等） |
| `transfer_history` | 279,164 | 转会历史记录（转入/转出俱乐部、转会费、赛季等） |
| `player_market_value` | 426,878 | 球员历史身价时间序列 |
| `player_latest_market_value` | 31,026 | 球员最新市场估值 |
| `team_details` | 1,304 | 俱乐部详情（名称、国家、联赛） |
| `player_injuries` | 77,871 | 伤病记录（伤病类型、起止日期） |

> 数据清洗后：**32,795** 位球员 · **1,304** 家俱乐部 · **279,164** 条转会记录

---

## 项目结构

```
football_recommender/
├── src/
│   ├── __init__.py
│   ├── data_preprocessing.py      # 数据预处理（加载/清洗/特征工程）
│   ├── collaborative_filtering.py # 协同过滤（Club-CF + Player-Similarity）
│   ├── content_based.py           # 基于内容推荐 + 位置推荐
│   ├── hybrid_recommender.py      # 混合推荐（自适应权重融合）
│   ├── evaluation.py              # 评估指标（Precision/Recall/NDCG/Coverage/Div./PosSatisfaction）
│   ├── visualization/
│   │   ├── __init__.py
│   │   └── visualizer.py          # 数据可视化（Matplotlib + Seaborn）
│   ├── demo/
│   │   ├── __init__.py
│   │   └── app.py                 # Web 演示界面（Flask）
│   ├── main.py                    # 主程序入口
│   └── requirements.txt           # Python 依赖清单
├── data/                          # 原始数据集（7 个 CSV 子目录）
├── img/                           # 输出图表
└── README.md
```

---

## 环境与运行

### 依赖

| 库 | 最低版本 |
|----|----------|
| pandas | ≥1.5.0 |
| numpy | ≥1.23.0 |
| scikit-learn | ≥1.1.0 |
| matplotlib | ≥3.6.0 |
| seaborn | ≥0.12.0 |
| flask | ≥2.2.0 |

### 安装

```bash
pip install -r src/requirements.txt
```

### 运行完整实验

```bash
python src/main.py
```

执行后将依次完成：数据探索性分析 → 独立模型训练 → 混合模型训练 → 模型评估 → 推荐演示，输出图表至 `img/` 目录。

### 启动 Web 演示

```bash
python src/demo/app.py
```

浏览器访问 **http://127.0.0.1:5000** 进入交互界面。

---

## Web 演示功能

| 功能 | 路由 | 说明 |
|------|------|------|
| 首页 | `GET /` | 交互式 Web 界面 |
| 数据概览 | `GET /api/stats` | 球员/俱乐部/转会统计 |
| 俱乐部列表 | `GET /api/clubs` | 所有俱乐部下拉数据 |
| 球员列表 | `GET /api/players` | Top 200 球员下拉数据 |
| 需求分析 | `POST /api/team_needs` | 位置缺口 + 年龄结构分析 |
| 俱乐部推荐 | `POST /api/recommend/club` | 为俱乐部推荐球员 |
| 相似球员 | `POST /api/recommend/similar` | 查找相似球员 |

### 交互流程

1. **选择俱乐部**：从下拉列表选择目标俱乐部
2. **分析需求**：查看位置需求卡片（绿/黄/红）与年龄结构
3. **获取推荐**：获得 Top-N 球员推荐及详细理由
4. **位置过滤**：按位置筛选推荐结果
5. **相似球员**：切换模式查找与某球员能力相近的球员

---

## 模型性能对比

| 指标 | Content-Based | Club-CF | **Hybrid** |
|------|:---:|:---:|:---:|
| Precision@10 | 0.152 | 0.138 | **0.185** |
| Recall@10 | 0.224 | 0.201 | **0.268** |
| NDCG@10 | 0.178 | 0.162 | **0.215** |
| Coverage | 0.45 | 0.32 | **0.58** |
| Diversity | 0.62 | 0.55 | **0.71** |
| 位置需求满足度 | 0.58 | 0.45 | **0.78** |

---

## 算法详解

### 基于俱乐部的协同过滤 (Club-Based CF)
- 构建俱乐部-球员转会矩阵，计算俱乐部间余弦相似度
- 聚合相似俱乐部的引援历史生成推荐
- 冷启动退化策略：按球员身价进行流行度推荐

### 基于内容的推荐 (Content-Based)
- 特征体系：比赛表现（进球/助攻/出场）+ 派生特征（场均进球/助攻）+ 个体属性（年龄/身高）
- 余弦相似度 + StandardScaler 标准化
- 位置推荐器：构建各位置 Top 25% 球员的理想特征画像

### 混合推荐 (Hybrid)
- 三路融合：Content(0.4) + CF(0.3) + Position(0.3)
- 自适应权重：检测位置缺口 → 放大 position 权重 ×1.3 → L1 归一化
- 年龄感知：`needs_young` 标志引导年轻球员倾斜

---

## 团队成员

| 成员 | 职责 | 工作量 |
|------|------|:---:|
| **熊彦钧** | 数据预处理与特征工程 | 33.3% |
| **马福泉** | 推荐算法实现（CF/CB/Hybrid/需求感知） | 33.3% |
| **牛渲淏** | 系统集成、评估模块、Web 演示、实验报告 | 33.3% |

---

## 参考资料

1. Ricci, Rokach & Shapira — *Recommender Systems Handbook* (2015)
2. Beggs — *Soccer Analytics: An Introduction Using R* (2019)
3. Cariboo — *Transfermarkt Football Dataset*, Kaggle
4. Koren, Bell & Volinsky — *Matrix Factorization Techniques for Recommender Systems*, IEEE Computer (2009)

---

## License

MIT — 仅供学术研究与教学用途。数据集版权归属 Transfermarkt 及 Kaggle 原作者。
