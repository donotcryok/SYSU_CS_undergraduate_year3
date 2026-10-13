# -*- coding: utf-8 -*-
"""
协同过滤推荐算法模块
实现基于用户的协同过滤 (User-based CF)
采用预计算和矩阵化运算优化性能
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


class CollaborativeFiltering:
    """
    基于用户的协同过滤推荐系统
    核心思想: 找到与目标用户兴趣相似的邻居用户，
    推荐邻居喜欢但目标用户未看过的电影
    """
    
    def __init__(self, k_neighbors=20, min_sim=0.1):
        """
        初始化协同过滤模型
        Args:
            k_neighbors: 邻居用户数量
            min_sim: 最小相似度阈值
        """
        self.k_neighbors = k_neighbors
        self.min_sim = min_sim
        self.user_movie_matrix = None
        self.user_similarity = None
        self.user_mean = None
        
        # 预计算的邻居缓存
        self.user_neighbors_cache = None  # {user_id: [(neighbor_id, sim), ...]}
        self.user_id_to_idx = None
        self.idx_to_user_id = None
        self.movie_id_to_idx = None
        self.idx_to_movie_id = None
        
        # numpy矩阵形式的数据
        self.rating_matrix_np = None  # numpy评分矩阵
        self.user_mean_np = None  # numpy用户均值数组
        
    def fit(self, user_movie_matrix):
        """
        训练模型：计算用户相似度矩阵并预计算邻居
        Args:
            user_movie_matrix: 用户-电影评分矩阵 (DataFrame)
        """
        print("训练协同过滤模型...")
        
        self.user_movie_matrix = user_movie_matrix.copy()
        
        # 创建ID到索引的映射
        user_ids = list(user_movie_matrix.index)
        movie_ids = list(user_movie_matrix.columns)
        
        self.user_id_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}
        self.idx_to_user_id = {idx: uid for uid, idx in self.user_id_to_idx.items()}
        self.movie_id_to_idx = {mid: idx for idx, mid in enumerate(movie_ids)}
        self.idx_to_movie_id = {idx: mid for mid, idx in self.movie_id_to_idx.items()}
        
        n_users = len(user_ids)
        n_movies = len(movie_ids)
        
        print(f"用户数: {n_users}, 电影数: {n_movies}")
        
        # 计算每个用户的平均评分
        self.user_mean = user_movie_matrix.mean(axis=1)
        self.user_mean_np = np.array([self.user_mean.get(uid, 3.0) for uid in user_ids])
        
        # 转换为numpy矩阵（NaN用0填充）
        print("构建numpy评分矩阵...")
        self.rating_matrix_np = user_movie_matrix.fillna(0).values
        
        # 计算用户相似度矩阵（使用余弦相似度）
        print("计算用户相似度矩阵...")
        self.user_similarity = cosine_similarity(self.rating_matrix_np)
        
        # 预计算每个用户的Top-K邻居
        print("预计算用户邻居缓存...")
        self._precompute_neighbors()
        
        print(f"模型训练完成! 用户数: {n_users}")
        
    def _precompute_neighbors(self):
        """
        预计算每个用户的Top-K邻居
        """
        self.user_neighbors_cache = {}
        
        n_users = self.user_similarity.shape[0]
        
        for i in range(n_users):
            user_id = self.idx_to_user_id[i]
            
            # 获取相似度向量
            similarities = self.user_similarity[i]
            
            # 排除自己（设为-1）
            similarities_copy = similarities.copy()
            similarities_copy[i] = -1
            
            # 过滤低相似度
            valid_mask = similarities_copy >= self.min_sim
            
            # 获取满足条件的索引
            valid_indices = np.where(valid_mask)[0]
            
            if len(valid_indices) == 0:
                self.user_neighbors_cache[user_id] = []
                continue
            
            # 获取有效相似度值
            valid_sims = similarities_copy[valid_indices]
            
            # 取Top-K（使用numpy的argsort，比pandas nlargest快得多）
            if len(valid_indices) > self.k_neighbors:
                top_k_indices = np.argsort(valid_sims)[-self.k_neighbors:][::-1]
                neighbor_indices = valid_indices[top_k_indices]
                neighbor_sims = valid_sims[top_k_indices]
            else:
                # 按相似度降序排列
                sorted_indices = np.argsort(valid_sims)[::-1]
                neighbor_indices = valid_indices[sorted_indices]
                neighbor_sims = valid_sims[sorted_indices]
            
            # 转换为(user_id, similarity)列表
            neighbors = [(self.idx_to_user_id[idx], sim) for idx, sim in zip(neighbor_indices, neighbor_sims)]
            self.user_neighbors_cache[user_id] = neighbors
        
        print(f"邻居缓存完成，共缓存 {len(self.user_neighbors_cache)} 个用户的邻居")
        
    def _get_neighbors_fast(self, user_id):
        """
        快速获取目标用户的邻居（从缓存查表）
        Args:
            user_id: 目标用户ID
        Returns:
            list: [(neighbor_id, similarity), ...]
        """
        return self.user_neighbors_cache.get(user_id, [])
    
    def predict_rating(self, user_id, movie_id):
        """
        预测用户对电影的评分
        使用预计算的邻居缓存，避免实时nlargest调用
        Args:
            user_id: 用户ID
            movie_id: 电影ID
        Returns:
            float: 预测评分
        """
        # 检查用户和电影是否在矩阵中
        if user_id not in self.user_id_to_idx:
            return 3.0
        if movie_id not in self.movie_id_to_idx:
            return 3.0
        
        user_idx = self.user_id_to_idx[user_id]
        movie_idx = self.movie_id_to_idx[movie_id]
        
        # 从缓存获取邻居
        neighbors = self._get_neighbors_fast(user_id)
        
        if len(neighbors) == 0:
            return self.user_mean_np[user_idx]
        
        # 使用numpy快速计算加权评分
        user_mean = self.user_mean_np[user_idx]
        weighted_sum = 0.0
        sim_sum = 0.0
        
        for neighbor_id, sim in neighbors:
            if neighbor_id not in self.user_id_to_idx:
                continue
            
            neighbor_idx = self.user_id_to_idx[neighbor_id]
            neighbor_rating = self.rating_matrix_np[neighbor_idx, movie_idx]
            
            # 检查邻居是否评分（原始矩阵中为NaN的位置现在为0）
            # 需要检查原始矩阵
            original_rating = self.user_movie_matrix.loc[neighbor_id, movie_id]
            if pd.isna(original_rating):
                continue
            
            neighbor_mean = self.user_mean_np[neighbor_idx]
            weighted_sum += (neighbor_rating - neighbor_mean) * sim
            sim_sum += abs(sim)
        
        if sim_sum == 0:
            return user_mean
        
        predicted = user_mean + weighted_sum / sim_sum
        
        # 限制评分范围 [0.5, 5.0]
        return np.clip(predicted, 0.5, 5.0)
    
    def predict_ratings_batch(self, user_id, movie_ids):
        """
        批量预测用户对多个电影的评分（进一步优化）
        Args:
            user_id: 用户ID
            movie_ids: 电影ID列表
        Returns:
            dict: {movie_id: predicted_rating}
        """
        if user_id not in self.user_id_to_idx:
            return {mid: 3.0 for mid in movie_ids}
        
        user_idx = self.user_id_to_idx[user_id]
        user_mean = self.user_mean_np[user_idx]
        neighbors = self._get_neighbors_fast(user_id)
        
        if len(neighbors) == 0:
            return {mid: user_mean for mid in movie_ids}
        
        predictions = {}
        
        for movie_id in movie_ids:
            if movie_id not in self.movie_id_to_idx:
                predictions[movie_id] = 3.0
                continue
            
            movie_idx = self.movie_id_to_idx[movie_id]
            
            weighted_sum = 0.0
            sim_sum = 0.0
            
            for neighbor_id, sim in neighbors:
                if neighbor_id not in self.user_id_to_idx:
                    continue
                
                neighbor_idx = self.user_id_to_idx[neighbor_id]
                
                # 检查原始评分是否存在
                original_rating = self.user_movie_matrix.loc[neighbor_id, movie_id]
                if pd.isna(original_rating):
                    continue
                
                neighbor_rating = self.rating_matrix_np[neighbor_idx, movie_idx]
                neighbor_mean = self.user_mean_np[neighbor_idx]
                
                weighted_sum += (neighbor_rating - neighbor_mean) * sim
                sim_sum += abs(sim)
            
            if sim_sum == 0:
                predictions[movie_id] = user_mean
            else:
                predicted = user_mean + weighted_sum / sim_sum
                predictions[movie_id] = np.clip(predicted, 0.5, 5.0)
        
        return predictions
    
    def recommend(self, user_id, n_recommendations=10, exclude_rated=True):
        """
        为用户生成推荐列表（优化版）
        Args:
            user_id: 目标用户ID
            n_recommendations: 推荐数量
            exclude_rated: 是否排除已评分电影
        Returns:
            list: 推荐电影ID列表 [(movie_id, predicted_rating), ...]
        """
        if user_id not in self.user_id_to_idx:
            return []
        
        # 获取用户已评分的电影
        user_ratings = self.user_movie_matrix.loc[user_id]
        rated_movies = set(user_ratings.dropna().index) if exclude_rated else set()
        
        # 待预测的电影
        all_movie_ids = list(self.user_movie_matrix.columns)
        to_predict = [mid for mid in all_movie_ids if mid not in rated_movies]
        
        # 批量预测（使用优化方法）
        predictions = self.predict_ratings_batch(user_id, to_predict)
        
        # 转换为列表并排序
        pred_list = [(mid, score) for mid, score in predictions.items()]
        pred_list.sort(key=lambda x: x[1], reverse=True)
        
        return pred_list[:n_recommendations]
    
    def get_user_similarity_matrix(self):
        """返回用户相似度矩阵"""
        return self.user_similarity


class ItemBasedCF:
    """
    基于物品的协同过滤推荐系统
    核心思想: 推荐与用户历史偏好物品相似的其他物品
    """
    
    def __init__(self, k_neighbors=20, min_sim=0.1):
        """
        初始化物品协同过滤模型
        
        Args:
            k_neighbors: 邻居物品数量
            min_sim: 最小相似度阈值
        """
        self.k_neighbors = k_neighbors
        self.min_sim = min_sim
        self.user_movie_matrix = None
        self.item_similarity = None
        
        # 预计算的邻居缓存
        self.item_neighbors_cache = None
        self.user_id_to_idx = None
        self.idx_to_user_id = None
        self.movie_id_to_idx = None
        self.idx_to_movie_id = None
        
        # numpy矩阵形式的数据
        self.rating_matrix_np = None
        
    def fit(self, user_movie_matrix):
        """
        训练模型：计算物品相似度矩阵并预计算邻居
        Args:
            user_movie_matrix: 用户-电影评分矩阵 (DataFrame)
        """
        print("训练物品协同过滤模型...")
        
        self.user_movie_matrix = user_movie_matrix.copy()
        
        # 创建ID到索引的映射
        user_ids = list(user_movie_matrix.index)
        movie_ids = list(user_movie_matrix.columns)
        
        self.user_id_to_idx = {uid: idx for idx, uid in enumerate(user_ids)}
        self.idx_to_user_id = {idx: uid for uid, idx in self.user_id_to_idx.items()}
        self.movie_id_to_idx = {mid: idx for idx, mid in enumerate(movie_ids)}
        self.idx_to_movie_id = {idx: mid for mid, idx in self.movie_id_to_idx.items()}
        
        n_users = len(user_ids)
        n_movies = len(movie_ids)
        
        print(f"用户数: {n_users}, 电影数: {n_movies}")
        
        # 转换为numpy矩阵
        self.rating_matrix_np = user_movie_matrix.fillna(0).values
        
        # 计算物品相似度矩阵（转置后计算）
        print("计算物品相似度矩阵...")
        self.item_similarity = cosine_similarity(self.rating_matrix_np.T)
        
        # 预计算每个物品的Top-K邻居
        print("预计算物品邻居缓存...")
        self._precompute_neighbors()
        
        print(f"模型训练完成! 电影数: {n_movies}")
        
    def _precompute_neighbors(self):
        """
        预计算每个物品的Top-K邻居
        """
        self.item_neighbors_cache = {}
        
        n_items = self.item_similarity.shape[0]
        
        for i in range(n_items):
            movie_id = self.idx_to_movie_id[i]
            
            similarities = self.item_similarity[i]
            similarities_copy = similarities.copy()
            similarities_copy[i] = -1
            
            valid_mask = similarities_copy >= self.min_sim
            valid_indices = np.where(valid_mask)[0]
            
            if len(valid_indices) == 0:
                self.item_neighbors_cache[movie_id] = []
                continue
            
            valid_sims = similarities_copy[valid_indices]
            
            if len(valid_indices) > self.k_neighbors:
                top_k_indices = np.argsort(valid_sims)[-self.k_neighbors:][::-1]
                neighbor_indices = valid_indices[top_k_indices]
                neighbor_sims = valid_sims[top_k_indices]
            else:
                sorted_indices = np.argsort(valid_sims)[::-1]
                neighbor_indices = valid_indices[sorted_indices]
                neighbor_sims = valid_sims[sorted_indices]
            
            neighbors = [(self.idx_to_movie_id[idx], sim) for idx, sim in zip(neighbor_indices, neighbor_sims)]
            self.item_neighbors_cache[movie_id] = neighbors
        
        print(f"物品邻居缓存完成，共缓存 {len(self.item_neighbors_cache)} 个物品的邻居")
        
    def predict_rating(self, user_id, movie_id):
        """
        预测用户对电影的评分
        Args:
            user_id: 用户ID
            movie_id: 电影ID
        Returns:
            float: 预测评分
        """
        if user_id not in self.user_id_to_idx:
            return 3.0
        if movie_id not in self.movie_id_to_idx:
            return 3.0
        
        user_idx = self.user_id_to_idx[user_id]
        
        # 获取用户已评分的电影
        user_ratings = self.user_movie_matrix.loc[user_id].dropna()
        
        if len(user_ratings) == 0:
            return 3.0
        
        # 获取与目标电影相似的物品（从缓存）
        similar_items = self.item_neighbors_cache.get(movie_id, [])
        
        if len(similar_items) == 0:
            return 3.0
        
        # 只考虑用户已评分的相似物品
        weighted_sum = 0.0
        sim_sum = 0.0
        
        for item_id, sim in similar_items:
            if item_id not in user_ratings.index:
                continue
            
            rating = user_ratings.get(item_id)
            if pd.notna(rating):
                weighted_sum += rating * sim
                sim_sum += abs(sim)
        
        if sim_sum == 0:
            return 3.0
        
        return weighted_sum / sim_sum
    
    def recommend(self, user_id, n_recommendations=10, exclude_rated=True):
        """
        为用户生成推荐列表
        Args:
            user_id: 目标用户ID
            n_recommendations: 推荐数量
            exclude_rated: 是否排除已评分电影
            
        Returns:
            list: 推荐电影ID列表 [(movie_id, predicted_rating), ...]
        """
        if user_id not in self.user_id_to_idx:
            return []
        
        user_ratings = self.user_movie_matrix.loc[user_id]
        rated_movies = set(user_ratings.dropna().index) if exclude_rated else set()
        
        all_movie_ids = list(self.user_movie_matrix.columns)
        to_predict = [mid for mid in all_movie_ids if mid not in rated_movies]
        
        predictions = []
        for movie_id in to_predict:
            pred_rating = self.predict_rating(user_id, movie_id)
            predictions.append((movie_id, pred_rating))
        
        predictions.sort(key=lambda x: x[1], reverse=True)
        
        return predictions[:n_recommendations]


if __name__ == '__main__':
    # 测试代码
    from data_loader import DataLoader
    
    loader = DataLoader()
    if loader.load_data():
        loader.split_data()
        matrix = loader.get_user_movie_matrix()
        
        # 测试优化后的User-based CF
        print("\n测试优化后的协同过滤...")
        cf = CollaborativeFiltering(k_neighbors=20)
        cf.fit(matrix)
        
        # 为第一个用户推荐
        user_id = matrix.index[0]
        recommendations = cf.recommend(user_id, n_recommendations=5)
        
        print(f"\n用户 {user_id} 的推荐:")
        for movie_id, score in recommendations:
            title = loader.movie_id_to_title.get(movie_id, "Unknown")
            print(f"  {title}: {score:.2f}")