# -*- coding: utf-8 -*-
"""
基于内容的推荐算法模块
利用电影的标签(Tags)和类型(Genres)特征进行推荐
"""

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ContentBasedRecommender:
    """
    基于内容的推荐系统
    
    核心思想: 
    1. 使用TF-IDF将电影类型和标签向量化
    2. 计算电影间的内容相似度
    3. 根据用户历史偏好推荐内容相似的电影
    """
    
    def __init__(self, min_df=1, max_features=5000):
        """
        初始化基于内容的推荐模型
        
        Args:
            min_df: 最小文档频率
            max_features: 最大特征数量
        """
        self.min_df = min_df
        self.max_features = max_features
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.movie_features = None
        self.movie_similarity = None
        self.movie_ids = None
        self.user_movie_matrix = None
        self.user_profiles = None
        
    def fit(self, movie_features, user_movie_matrix):
        """
        训练模型：构建TF-IDF特征矩阵和相似度矩阵
        
        Args:
            movie_features: 电影特征字典 {movie_id: {'combined': '...'}}
            user_movie_matrix: 用户-电影评分矩阵 (DataFrame)
        """
        print("训练基于内容的推荐模型...")
        
        self.movie_features = movie_features
        self.user_movie_matrix = user_movie_matrix.copy()
        
        # 准备电影内容文本
        movie_ids = list(movie_features.keys())
        self.movie_ids = movie_ids
        
        # 构建文档列表
        documents = []
        for movie_id in movie_ids:
            content = movie_features[movie_id].get('combined', '')
            documents.append(content)
        
        # 使用TF-IDF向量化
        print("构建TF-IDF特征矩阵...")
        self.tfidf_vectorizer = TfidfVectorizer(
            min_df=self.min_df,
            max_features=self.max_features,
            stop_words='english'
        )
        
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)
        
        # 计算电影相似度矩阵
        print("计算电影内容相似度矩阵...")
        self.movie_similarity = cosine_similarity(self.tfidf_matrix)
        
        # 构建用户画像
        print("构建用户画像...")
        self._build_user_profiles()
        
        print(f"模型训练完成! 电影数: {len(movie_ids)}, 特征维度: {self.tfidf_matrix.shape[1]}")
        
    def _build_user_profiles(self):
        """
        构建用户画像
        
        用户画像 = 用户已评分电影的TF-IDF向量的加权平均
        权重为用户评分
        """
        self.user_profiles = {}
        
        # 创建电影ID到矩阵索引的映射
        movie_id_to_idx = {mid: idx for idx, mid in enumerate(self.movie_ids)}
        
        for user_id in self.user_movie_matrix.index:
            # 获取用户评分
            user_ratings = self.user_movie_matrix.loc[user_id].dropna()
            
            if len(user_ratings) == 0:
                # 新用户：使用平均向量
                self.user_profiles[user_id] = np.zeros(self.tfidf_matrix.shape[1])
                continue
            
            # 计算加权特征向量
            weighted_vector = np.zeros(self.tfidf_matrix.shape[1])
            weight_sum = 0
            
            for movie_id, rating in user_ratings.items():
                if movie_id in movie_id_to_idx:
                    idx = movie_id_to_idx[movie_id]
                    # 使用评分作为权重，减去均值以强调偏好
                    weight = rating - 2.5  # 中心化
                    weighted_vector += weight * self.tfidf_matrix[idx].toarray().flatten()
                    weight_sum += abs(weight)
            
            if weight_sum > 0:
                weighted_vector /= weight_sum
                
            self.user_profiles[user_id] = weighted_vector
    
    def predict_rating(self, user_id, movie_id):
        """
        预测用户对电影的评分
        
        Args:
            user_id: 用户ID
            movie_id: 电影ID
            
        Returns:
            float: 预测评分
        """
        # 检查电影是否在特征中
        if movie_id not in self.movie_ids:
            return 3.0
        
        # 检查用户是否有画像
        if user_id not in self.user_profiles:
            return 3.0
        
        # 获取电影TF-IDF向量
        movie_idx = self.movie_ids.index(movie_id)
        movie_vector = self.tfidf_matrix[movie_idx].toarray().flatten()
        
        # 计算用户画像与电影的相似度
        user_vector = self.user_profiles[user_id]
        
        # 余弦相似度
        dot_product = np.dot(user_vector, movie_vector)
        norm_user = np.linalg.norm(user_vector)
        norm_movie = np.linalg.norm(movie_vector)
        
        if norm_user == 0 or norm_movie == 0:
            return 3.0
        
        similarity = dot_product / (norm_user * norm_movie)
        
        # 将相似度映射到评分范围 [0.5, 5.0]
        # 相似度范围 [-1, 1] -> 评分范围 [0.5, 5.0]
        predicted = 2.75 + similarity * 2.25
        
        return np.clip(predicted, 0.5, 5.0)
    
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
        # 获取用户已评分的电影
        user_ratings = self.user_movie_matrix.loc[user_id]
        rated_movies = set(user_ratings.dropna().index) if exclude_rated else set()
        
        # 待预测的电影
        to_predict = [mid for mid in self.movie_ids if mid not in rated_movies]
        
        # 预测评分
        predictions = []
        for movie_id in to_predict:
            pred_rating = self.predict_rating(user_id, movie_id)
            predictions.append((movie_id, pred_rating))
        
        # 按预测评分排序
        predictions.sort(key=lambda x: x[1], reverse=True)
        
        return predictions[:n_recommendations]
    
    def get_similar_movies(self, movie_id, n_similar=10):
        """
        获取与指定电影内容相似的电影
        
        Args:
            movie_id: 电影ID
            n_similar: 返回数量
            
        Returns:
            list: 相似电影列表 [(movie_id, similarity), ...]
        """
        if movie_id not in self.movie_ids:
            return []
        
        movie_idx = self.movie_ids.index(movie_id)
        
        # 获取相似度
        similarities = self.movie_similarity[movie_idx]
        
        # 获取最相似的电影（排除自己）
        similar_indices = np.argsort(similarities)[::-1][1:n_similar+1]
        
        similar_movies = []
        for idx in similar_indices:
            similar_movie_id = self.movie_ids[idx]
            sim = similarities[idx]
            similar_movies.append((similar_movie_id, sim))
        
        return similar_movies
    
    def get_movie_features(self, movie_id):
        """
        获取电影的特征词
        
        Args:
            movie_id: 电影ID
            
        Returns:
            list: 重要特征词列表
        """
        if movie_id not in self.movie_ids:
            return []
        
        movie_idx = self.movie_ids.index(movie_id)
        feature_vector = self.tfidf_matrix[movie_idx].toarray().flatten()
        
        # 获取TF-IDF值最高的特征
        feature_names = self.tfidf_vectorizer.get_feature_names_out()
        top_indices = np.argsort(feature_vector)[::-1][:10]
        
        top_features = [(feature_names[i], feature_vector[i]) for i in top_indices if feature_vector[i] > 0]
        
        return top_features


if __name__ == '__main__':
    # 测试代码
    from data_loader import DataLoader
    
    loader = DataLoader()
    if loader.load_data():
        loader.split_data()
        matrix = loader.get_user_movie_matrix()
        movie_features = loader.get_movie_features()
        
        # 测试CB推荐
        cb = ContentBasedRecommender()
        cb.fit(movie_features, matrix)
        
        # 为第一个用户推荐
        user_id = matrix.index[0]
        recommendations = cb.recommend(user_id, n_recommendations=5)
        
        print(f"\n用户 {user_id} 的推荐:")
        for movie_id, score in recommendations:
            title = loader.movie_id_to_title.get(movie_id, "Unknown")
            print(f"  {title}: {score:.2f}")
        
        # 测试相似电影
        print("\n与电影1相似的电影:")
        similar = cb.get_similar_movies(1, n_similar=5)
        for movie_id, sim in similar:
            title = loader.movie_id_to_title.get(movie_id, "Unknown")
            print(f"  {title}: {sim:.3f}")