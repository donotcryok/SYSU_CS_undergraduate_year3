# -*- coding: utf-8 -*-
"""
聚类算法对比实验
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from scipy.optimize import linear_sum_assignment
import os
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False



class KMeansManual:
    """
    手动实现的 K-means 聚类算法
    使用 K-means++ 初始化方法
    """
    def __init__(self, n_clusters=3, max_iter=300, tol=1e-4, random_state=42):
        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.tol = tol
        self.random_state = random_state
        self.centroids = None
        self.labels = None
        self.inertia_ = None
        self.n_iter_ = 0
        
    def _euclidean_distance(self, x, y):
        """计算欧氏距离"""
        return np.sqrt(np.sum((x - y) ** 2))
    
    def _kmeans_plus_plus_init(self, X):
        """
        选择初始质心，使得它们彼此之间的距离尽可能大
        """
        np.random.seed(self.random_state)
        n_samples, n_features = X.shape
        centroids = np.zeros((self.n_clusters, n_features))
        
        # 随机选择第一个质心
        first_idx = np.random.randint(0, n_samples)
        centroids[0] = X[first_idx]
        
        # 选择剩余的质心
        for k in range(1, self.n_clusters):
            # 计算每个样本到最近质心的距离
            distances = np.zeros(n_samples)
            for i in range(n_samples):
                min_dist = float('inf')
                for j in range(k):
                    dist = self._euclidean_distance(X[i], centroids[j])
                    if dist < min_dist:
                        min_dist = dist
                distances[i] = min_dist
            
            # 按距离的平方概率选择下一个质心
            probabilities = distances ** 2
            probabilities /= probabilities.sum()
            next_idx = np.random.choice(n_samples, p=probabilities)
            centroids[k] = X[next_idx]
        
        return centroids
    
    def _assign_clusters(self, X):
        """
        将每个样本分配到最近的质心
        """
        n_samples = X.shape[0]
        labels = np.zeros(n_samples, dtype=int)
        
        for i in range(n_samples):
            min_dist = float('inf')
            for k in range(self.n_clusters):
                dist = self._euclidean_distance(X[i], self.centroids[k])
                if dist < min_dist:
                    min_dist = dist
                    labels[i] = k
        
        return labels
    
    def _update_centroids(self, X, labels):
        """
        更新质心位置
        """
        n_features = X.shape[1]
        new_centroids = np.zeros((self.n_clusters, n_features))
        
        for k in range(self.n_clusters):
            cluster_points = X[labels == k]
            if len(cluster_points) > 0:
                new_centroids[k] = cluster_points.mean(axis=0)
            else:
                # 如果簇为空，随机重新初始化
                new_centroids[k] = X[np.random.randint(0, X.shape[0])]
        
        return new_centroids
    
    def _compute_inertia(self, X, labels):
        """
        计算簇内平方和
        """
        inertia = 0.0
        for k in range(self.n_clusters):
            cluster_points = X[labels == k]
            if len(cluster_points) > 0:
                inertia += np.sum((cluster_points - self.centroids[k]) ** 2)
        return inertia
    
    def fit(self, X):
        """
        拟合 K-means 模型
        """
        X = np.array(X)
        
        # K-means++ 初始化质心
        self.centroids = self._kmeans_plus_plus_init(X)
        
        for iteration in range(self.max_iter):
            # 分配样本到最近的簇
            labels = self._assign_clusters(X)
            
            # 更新质心
            new_centroids = self._update_centroids(X, labels)
            
            # 检查收敛
            centroid_shift = np.sum((new_centroids - self.centroids) ** 2)
            self.centroids = new_centroids
            
            if centroid_shift < self.tol:
                self.labels = labels
                self.n_iter_ = iteration + 1
                break
            
            self.labels = labels
            self.n_iter_ = iteration + 1
        
        self.inertia_ = self._compute_inertia(X, self.labels)
        return self
    
    def predict(self, X):
        """预测新样本的簇标签"""
        return self._assign_clusters(np.array(X))


class DBSCANManual:
    """
    手动实现的 DBSCAN 聚类算法
    """
    
    def __init__(self, eps=0.5, min_samples=5):
        """
        初始化 DBSCAN 参数
        """
        self.eps = eps
        self.min_samples = min_samples
        self.labels = None
        self.core_sample_indices_ = None
        self.n_clusters_ = 0
        
    def _euclidean_distance(self, x, y):
        """计算欧氏距离"""
        return np.sqrt(np.sum((x - y) ** 2))
    
    def _region_query(self, X, point_idx):
        """
        查询点 point_idx 的 epsilon-邻域
        返回所有距离小于 eps 的点的索引
        """
        n_samples = X.shape[0]
        neighbors = []
        
        for i in range(n_samples):
            if self._euclidean_distance(X[point_idx], X[i]) <= self.eps:
                neighbors.append(i)
        
        return np.array(neighbors)
    
    def _expand_cluster(self, X, point_idx, neighbors, cluster_id, visited, cluster_labels):
        """
        扩展簇
        从核心点开始，将所有密度相连的点加入当前簇
        使用队列实现广度优先搜索
        """
        # 将当前点标记为当前簇
        cluster_labels[point_idx] = cluster_id
        
        # 使用队列进行簇扩展
        queue = list(neighbors)
        
        while queue:
            current_idx = queue.pop(0)
            
            if not visited[current_idx]:
                visited[current_idx] = True
                current_neighbors = self._region_query(X, current_idx)
                
                # 如果当前点也是核心点，将其邻居加入队列
                if len(current_neighbors) >= self.min_samples:
                    for neighbor_idx in current_neighbors:
                        if neighbor_idx not in queue and cluster_labels[neighbor_idx] == -1:
                            queue.append(neighbor_idx)
            
            # 如果点未被分配到任何簇，分配到当前簇
            if cluster_labels[current_idx] == -1:
                cluster_labels[current_idx] = cluster_id
    
    def fit(self, X):
        """
        拟合 DBSCAN 模型
        """
        X = np.array(X)
        n_samples = X.shape[0]
        
        # 初始化
        visited = np.zeros(n_samples, dtype=bool)
        cluster_labels = np.full(n_samples, -1)  # -1 表示噪声点
        cluster_id = 0
        core_samples = []
        
        for point_idx in range(n_samples):
            if visited[point_idx]:
                continue
            
            visited[point_idx] = True
            neighbors = self._region_query(X, point_idx)
            
            if len(neighbors) < self.min_samples:
                # 标记为噪声点（cluster_labels 已初始化为 -1）
                pass
            else:
                # 这是一个核心点，开始新的簇
                core_samples.append(point_idx)
                self._expand_cluster(X, point_idx, neighbors, cluster_id, visited, cluster_labels)
                cluster_id += 1
        
        self.labels = cluster_labels
        self.core_sample_indices_ = np.array(core_samples)
        self.n_clusters_ = cluster_id
        
        return self
    
    def predict(self, X):
        """DBSCAN 不支持 predict，因为新点需要重新计算"""
        raise NotImplementedError("DBSCAN does not support predict. Use fit_predict instead.")
    
    def fit_predict(self, X):
        """拟合并返回标签"""
        self.fit(X)
        return self.labels


# ==================== 评估指标计算 ====================

def compute_accuracy(y_true, y_pred):
    """
    计算聚类准确率
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # 获取唯一标签
    true_labels = np.unique(y_true)
    pred_labels = np.unique(y_pred)
    
    # 过滤噪声点（标签为 -1）
    valid_mask = y_pred >= 0
    y_true_valid = y_true[valid_mask]
    y_pred_valid = y_pred[valid_mask]
    
    if len(y_pred_valid) == 0:
        return 0.0
    
    # 构建混淆矩阵（代价矩阵）
    n_true = len(true_labels)
    n_pred = len(pred_labels[pred_labels >= 0])
    
    if n_pred == 0:
        return 0.0
    
    # 创建标签到索引的映射
    true_to_idx = {label: idx for idx, label in enumerate(true_labels)}
    pred_to_idx = {label: idx for idx, label in enumerate(pred_labels[pred_labels >= 0])}
    
    # 构建代价矩阵（负的匹配数量，因为 linear_sum_assignment 求最小值）
    cost_matrix = np.zeros((n_true, n_pred))
    
    for i, true_label in enumerate(true_labels):
        for j, pred_label in enumerate(pred_labels[pred_labels >= 0]):
            # 计算匹配数量
            matches = np.sum((y_true_valid == true_label) & (y_pred_valid == pred_label))
            cost_matrix[i, j] = -matches
    
    # 使用 Hungarian Algorithm 求解最优匹配
    row_ind, col_ind = linear_sum_assignment(cost_matrix)
    
    # 计算正确匹配的总数
    total_correct = 0
    for i, j in zip(row_ind, col_ind):
        true_label = true_labels[i]
        pred_label = pred_labels[pred_labels >= 0][j]
        matches = np.sum((y_true == true_label) & (y_pred == pred_label))
        total_correct += matches
    
    # 准确率 = 正确匹配数 / 总样本数
    accuracy = total_correct / len(y_true)
    
    return accuracy


def compute_silhouette_score_safe(X, labels):
    """
    安全计算轮廓系数
    处理只有一个簇或全是噪声点的情况
    """
    # 过滤噪声点
    valid_mask = labels >= 0
    X_valid = X[valid_mask]
    labels_valid = labels[valid_mask]
    
    if len(np.unique(labels_valid)) < 2:
        return 0.0
    
    return silhouette_score(X_valid, labels_valid)


def compute_calinski_harabasz_score_safe(X, labels):
    """
    安全计算 Calinski-Harabasz 指数
    处理只有一个簇或全是噪声点的情况
    """
    # 过滤噪声点
    valid_mask = labels >= 0
    X_valid = X[valid_mask]
    labels_valid = labels[valid_mask]
    
    if len(np.unique(labels_valid)) < 2:
        return 0.0
    
    return calinski_harabasz_score(X_valid, labels_valid)



def run_experiment():
    """运行聚类对比实验"""
    
    # 创建图片保存目录
    os.makedirs('../img', exist_ok=True)
    
    # 1. 加载 Iris 数据集
    print("=" * 60)
    print("加载 Iris 数据集...")
    iris = load_iris()
    X = iris.data
    y_true = iris.target
    feature_names = iris.feature_names
    target_names = iris.target_names
    
    print(f"数据集形状: {X.shape}")
    print(f"特征名称: {feature_names}")
    print(f"类别名称: {target_names}")
    
    # 2. 数据标准化
    print("\n数据标准化...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 3. K-means 实验
    print("\n" + "=" * 60)
    print("K-means 聚类实验")
    print("=" * 60)
    
    k_values = [2, 3, 4, 5]
    kmeans_results = []
    
    for k in k_values:
        print(f"\nK-means (k={k}):")
        kmeans = KMeansManual(n_clusters=k, random_state=42)
        kmeans.fit(X_scaled)
        
        # 计算评估指标
        accuracy = compute_accuracy(y_true, kmeans.labels)
        silhouette = compute_silhouette_score_safe(X_scaled, kmeans.labels)
        calinski = compute_calinski_harabasz_score_safe(X_scaled, kmeans.labels)
        
        print(f"  迭代次数: {kmeans.n_iter_}")
        print(f"  准确率: {accuracy:.4f}")
        print(f"  轮廓系数: {silhouette:.4f}")
        print(f"  Calinski-Harabasz 指数: {calinski:.4f}")
        
        kmeans_results.append({
            'k': k,
            'accuracy': accuracy,
            'silhouette': silhouette,
            'calinski': calinski,
            'labels': kmeans.labels.copy(),
            'centroids': kmeans.centroids.copy()
        })
    
    # 4. DBSCAN 实验
    print("\n" + "=" * 60)
    print("DBSCAN 聚类实验")
    print("=" * 60)
    
    eps_values = [0.2, 0.5, 0.8, 1.2]
    min_samples = 5
    dbscan_results = []
    
    for eps in eps_values:
        print(f"\nDBSCAN (eps={eps}, min_samples={min_samples}):")
        dbscan = DBSCANManual(eps=eps, min_samples=min_samples)
        dbscan.fit(X_scaled)
        
        # 计算评估指标
        accuracy = compute_accuracy(y_true, dbscan.labels)
        silhouette = compute_silhouette_score_safe(X_scaled, dbscan.labels)
        calinski = compute_calinski_harabasz_score_safe(X_scaled, dbscan.labels)
        
        n_noise = np.sum(dbscan.labels == -1)
        n_clusters = dbscan.n_clusters_
        
        print(f"  簇数量: {n_clusters}")
        print(f"  噪声点数量: {n_noise}")
        print(f"  准确率: {accuracy:.4f}")
        print(f"  轮廓系数: {silhouette:.4f}")
        print(f"  Calinski-Harabasz 指数: {calinski:.4f}")
        
        dbscan_results.append({
            'eps': eps,
            'min_samples': min_samples,
            'accuracy': accuracy,
            'silhouette': silhouette,
            'calinski': calinski,
            'labels': dbscan.labels.copy(),
            'n_clusters': n_clusters,
            'n_noise': n_noise
        })
    
    # 5. 可视化
    print("\n" + "=" * 60)
    print("生成可视化图表...")
    print("=" * 60)
    
    # 使用前两个特征进行可视化
    x_axis = 0  # sepal length
    y_axis = 1  # sepal width
    
    # K-means 可视化
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle('K-means 聚类结果对比 (不同 k 值)', fontsize=16, fontweight='bold')
    
    for idx, result in enumerate(kmeans_results):
        ax = axes[idx // 2, idx % 2]
        scatter = ax.scatter(X_scaled[:, x_axis], X_scaled[:, y_axis], 
                           c=result['labels'], cmap='viridis', alpha=0.6, s=50)
        ax.scatter(result['centroids'][:, x_axis], result['centroids'][:, y_axis],
                  c='red', marker='x', s=200, linewidths=3, label='质心')
        ax.set_xlabel(feature_names[x_axis], fontsize=12)
        ax.set_ylabel(feature_names[y_axis], fontsize=12)
        ax.set_title(f'k={result["k"]}, Accuracy={result["accuracy"]:.3f}, '
                    f'Silhouette={result["silhouette"]:.3f}', fontsize=11)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../img/kmeans_result.png', dpi=150, bbox_inches='tight')
    print("保存: ../img/kmeans_result.png")
    plt.close()
    
    # DBSCAN 可视化
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle('DBSCAN 聚类结果对比 (不同 eps 值, MinPts=5)', fontsize=16, fontweight='bold')
    
    for idx, result in enumerate(dbscan_results):
        ax = axes[idx // 2, idx % 2]
        
        # 绘制聚类点
        unique_labels = np.unique(result['labels'])
        colors = plt.cm.viridis(np.linspace(0, 1, len(unique_labels)))
        
        for label, color in zip(unique_labels, colors):
            if label == -1:
                # 噪声点用黑色表示
                mask = result['labels'] == label
                ax.scatter(X_scaled[mask, x_axis], X_scaled[mask, y_axis],
                          c='black', marker='x', s=50, alpha=0.6, label='噪声点')
            else:
                mask = result['labels'] == label
                ax.scatter(X_scaled[mask, x_axis], X_scaled[mask, y_axis],
                          c=[color], s=50, alpha=0.6, label=f'簇 {label}')
        
        ax.set_xlabel(feature_names[x_axis], fontsize=12)
        ax.set_ylabel(feature_names[y_axis], fontsize=12)
        ax.set_title(f'eps={result["eps"]}, 簇数={result["n_clusters"]}, '
                    f'噪声点={result["n_noise"]}, Accuracy={result["accuracy"]:.3f}', fontsize=11)
        ax.legend(loc='upper right', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../img/dbscan_result.png', dpi=150, bbox_inches='tight')
    print("保存: ../img/dbscan_result.png")
    plt.close()
    
    # 生成组合对比图
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('K-means 与 DBSCAN 聚类结果对比', fontsize=16, fontweight='bold')
    
    # 真实标签
    ax = axes[0, 0]
    scatter = ax.scatter(X_scaled[:, x_axis], X_scaled[:, y_axis], 
                        c=y_true, cmap='viridis', alpha=0.6, s=50)
    ax.set_xlabel(feature_names[x_axis], fontsize=12)
    ax.set_ylabel(feature_names[y_axis], fontsize=12)
    ax.set_title('真实标签', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # K-means 最佳结果 (k=3)
    ax = axes[0, 1]
    best_kmeans = kmeans_results[1]  # k=3
    ax.scatter(X_scaled[:, x_axis], X_scaled[:, y_axis], 
              c=best_kmeans['labels'], cmap='viridis', alpha=0.6, s=50)
    ax.scatter(best_kmeans['centroids'][:, x_axis], best_kmeans['centroids'][:, y_axis],
              c='red', marker='x', s=200, linewidths=3, label='质心')
    ax.set_xlabel(feature_names[x_axis], fontsize=12)
    ax.set_ylabel(feature_names[y_axis], fontsize=12)
    ax.set_title(f'K-means (k=3)\nAccuracy={best_kmeans["accuracy"]:.3f}', fontsize=12)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    
    # DBSCAN 最佳结果 (eps=0.8)
    ax = axes[0, 2]
    best_dbscan = dbscan_results[2]  # eps=0.8
    unique_labels = np.unique(best_dbscan['labels'])
    colors = plt.cm.viridis(np.linspace(0, 1, len(unique_labels)))
    for label, color in zip(unique_labels, colors):
        mask = best_dbscan['labels'] == label
        if label == -1:
            ax.scatter(X_scaled[mask, x_axis], X_scaled[mask, y_axis],
                      c='black', marker='x', s=50, alpha=0.6, label='噪声点')
        else:
            ax.scatter(X_scaled[mask, x_axis], X_scaled[mask, y_axis],
                      c=[color], s=50, alpha=0.6, label=f'簇 {label}')
    ax.set_xlabel(feature_names[x_axis], fontsize=12)
    ax.set_ylabel(feature_names[y_axis], fontsize=12)
    ax.set_title(f'DBSCAN (eps=0.8, MinPts=5)\nAccuracy={best_dbscan["accuracy"]:.3f}', fontsize=12)
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3)
    
    # K-means 所有 k 值对比 (第二行显示 k=2,3,4)
    for idx in range(3):
        if idx < len(kmeans_results):
            result = kmeans_results[idx]
            ax = axes[1, idx]
            ax.scatter(X_scaled[:, x_axis], X_scaled[:, y_axis],
                      c=result['labels'], cmap='viridis', alpha=0.6, s=30)
            ax.scatter(result['centroids'][:, x_axis], result['centroids'][:, y_axis],
                      c='red', marker='x', s=100, linewidths=2)
            ax.set_xlabel(feature_names[x_axis], fontsize=10)
            ax.set_ylabel(feature_names[y_axis], fontsize=10)
            ax.set_title(f'K-means k={result["k"]}', fontsize=10)
            ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('../img/comparison_result.png', dpi=150, bbox_inches='tight')
    print("保存: ../img/comparison_result.png")
    plt.close()
    
    # 6. 输出结果表格
    print("\n" + "=" * 60)
    print("实验结果汇总")
    print("=" * 60)
    
    print("\nK-means 结果表格:")
    print("-" * 70)
    print(f"{'k值':<8}{'准确率':<15}{'轮廓系数':<15}{'Calinski-Harabasz':<20}")
    print("-" * 70)
    for result in kmeans_results:
        print(f"{result['k']:<8}{result['accuracy']:<15.4f}{result['silhouette']:<15.4f}"
              f"{result['calinski']:<20.4f}")
    
    print("\nDBSCAN 结果表格:")
    print("-" * 80)
    print(f"{'eps':<8}{'簇数':<8}{'噪声点':<10}{'准确率':<12}{'轮廓系数':<12}{'Calinski-Harabasz':<20}")
    print("-" * 80)
    for result in dbscan_results:
        print(f"{result['eps']:<8}{result['n_clusters']:<8}{result['n_noise']:<10}"
              f"{result['accuracy']:<12.4f}{result['silhouette']:<12.4f}{result['calinski']:<20.4f}")
    
    print("\n实验完成！")
    return kmeans_results, dbscan_results


if __name__ == "__main__":
    kmeans_results, dbscan_results = run_experiment()