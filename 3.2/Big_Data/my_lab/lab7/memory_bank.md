# 混合推荐系统项目 - Memory Bank

## 项目概述
本项目基于 MovieLens (ml-latest-small) 数据集实现混合推荐系统，包含协同过滤(CF)、基于内容推荐(CB)和混合策略(Hybrid)三种方法。

## 数据集结构
- `movies.csv`: 电影信息 (movieId, title, genres)
- `ratings.csv`: 用户评分 (userId, movieId, rating, timestamp)
- `tags.csv`: 用户标签 (userId, movieId, tag, timestamp)
- `links.csv`: 外部链接ID

## 算法架构设计

### 1. 协同过滤 (Collaborative Filtering - CF)
- **方法**: 基于用户的协同过滤 (User-based CF)
- **相似度计算**: 余弦相似度
- **核心思想**: 找到与目标用户兴趣相似的邻居用户，推荐邻居喜欢但目标用户未看过的电影

### 2. 基于内容推荐 (Content-Based - CB)
- **特征构建**: 
  - 电影类型 (Genres) 使用 TF-IDF 向量化
  - 用户标签 (Tags) 聚合后使用 TF-IDF
- **相似度计算**: 余弦相似度
- **核心思想**: 推荐与用户历史偏好内容相似的电影

### 3. 混合策略 (Hybrid)
- **方法**: 加权混合
- **权重设计**: CF权重0.6, CB权重0.4 (可调优)
- **目标**: 结合CF的协同优势和CB的内容理解，提升召回率和多样性

## 评估指标
- **召回率 (Recall Rate)**: 推荐命中数 / 用户实际喜欢数
- **覆盖率 (Coverage)**: 被推荐电影数 / 总电影数
- **多样性 (Diversity)**: 推荐列表中物品间的平均不相似度

## 代码模块结构
```
src/
├── data_loader.py      # 数据加载与预处理
├── collaborative_filtering.py  # 协同过滤算法（优化版）
├── content_based.py    # 基于内容推荐算法
├── hybrid_recommender.py       # 混合推荐策略（优化版）
├── evaluation.py       # 评估指标计算（优化版）
├── visualization.py    # 可视化图表生成
└── main.py            # 主程序入口（优化版）
```

---

## 🚀 性能优化记录（重要更新）

### 问题诊断
在评估混合推荐模型时出现严重的性能瓶颈，导致终端卡死。通过Traceback分析，瓶颈位于 `collaborative_filtering.py` 的 `_get_neighbors` 函数中使用的 `pandas.Series.nlargest`。在最内层循环反复调用 `nlargest` 查找近邻，导致时间复杂度爆炸。

### 优化策略

#### 1. 矩阵化与预计算 (Pre-computation & Vectorization)

**核心改动**：彻底废弃在 `predict_rating` 内实时调用 pandas 的 `nlargest`。

**实现方式**：
- 在模型 `fit` 阶段，**一次性计算好相似度矩阵**
- **预筛选并缓存每个用户的 Top-K 邻居**：使用字典 `{user_id: [(neighbor_id, sim), ...]}` 存储
- 预测时，直接查表获取近邻，使用 numpy 数组进行加权求和
- 使用 `numpy.argsort` 替代 `pandas.nlargest`，性能提升显著

**代码示例**：
```python
def _precompute_neighbors(self):
    """预计算每个用户的Top-K邻居"""
    self.user_neighbors_cache = {}
    
    for i in range(n_users):
        similarities = self.user_similarity[i]
        similarities_copy = similarities.copy()
        similarities_copy[i] = -1  # 排除自己
        
        # 使用numpy的argsort（比pandas nlargest快得多）
        valid_indices = np.where(similarities_copy >= self.min_sim)[0]
        if len(valid_indices) > self.k_neighbors:
            top_k_indices = np.argsort(valid_sims)[-self.k_neighbors:][::-1]
        
        # 缓存邻居列表
        neighbors = [(self.idx_to_user_id[idx], sim) for idx, sim in zip(...)]
        self.user_neighbors_cache[user_id] = neighbors
```

#### 2. 限制评估规模 (Sampling for Evaluation)

**核心改动**：不对全量用户进行耗时的 Top-N 生成和评估。

**实现方式**：
- 在 `evaluate` 方法中增加采样逻辑
- 默认随机抽取 **100 个测试用户** 进行计算
- 确保本地 CPU 环境下可在 **1~2 分钟内** 跑完整个流程

**代码示例**：
```python
def evaluate(self, recommender, ..., sample_users=None):
    # 自动采样
    if sample_users is None:
        sample_size = min(self.default_sample_size, len(valid_test_users))
        sample_users = random.sample(valid_test_users, sample_size)
        print(f"自动采样 {sample_size} 个用户进行评估")
```

#### 3. 异常与进度提示

**核心改动**：在核心计算循环中引入进度显示。

**实现方式**：
- 尝试导入 `tqdm` 进度条，如果不可用则使用简单 log
- 每处理 10 个用户打印一次进度，让用户明确知道程序在推进

**代码示例**：
```python
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# 使用进度条
if HAS_TQDM:
    user_iterator = tqdm(sample_users, desc="评估用户", unit="用户")
else:
    # 简单进度提示
    if (i + 1) % 10 == 0:
        print(f"  已评估 {i + 1}/{len(sample_users)} 个用户...")
```

### 优化效果

| 优化项 | 原方案 | 优化后 | 效果 |
|--------|--------|--------|------|
| 邻居查找 | 实时 `nlargest` | 预计算缓存 | O(n) → O(1) 查表 |
| 相似度计算 | pandas DataFrame | numpy 矩阵 | 减少开销 |
| 评估规模 | 全量用户 | 采样100用户 | 时间从数小时 → 1-2分钟 |
| 进度提示 | 无 | tqdm/log | 用户体验提升 |

### 架构优化心得

**从实时计算到预计算的转变**：

1. **预计算的本质**：将重复计算的工作提前完成并缓存，用空间换时间。在推荐系统中，用户相似度和邻居关系在短期内不会频繁变化，非常适合预计算。

2. **numpy vs pandas**：在数值计算密集的场景，numpy 的性能远优于 pandas。pandas 提供了便利的数据操作接口，但在循环中频繁调用其方法（如 `nlargest`）会带来巨大开销。

3. **采样评估的合理性**：在学术实验和原型开发阶段，采样评估是合理的做法。100个用户的评估结果足以反映算法的相对性能差异，同时大幅节省时间。

4. **进度提示的重要性**：长时间运行的程序必须有进度提示，否则用户无法判断程序是否正常运行还是已经卡死。

---

## 当前状态
- [x] 数据分析完成
- [x] 代码开发完成
- [x] 性能优化完成
- [x] 报告撰写完成

## 关键技术点
1. 数据稀疏性处理: 使用均值填充或降维
2. 冷启动问题: CB方法可部分缓解新用户/新物品问题
3. 评估方法: 留出法 (Train/Test split) + 采样评估
4. 性能优化: 预计算 + numpy矩阵化 + 采样 + 进度提示