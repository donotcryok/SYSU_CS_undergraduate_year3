# -*- coding: utf-8 -*-
"""
混合推荐策略模块
结合协同过滤和基于内容推荐的优势
"""

import numpy as np
from collaborative_filtering import CollaborativeFiltering, ItemBasedCF
from content_based import ContentBasedRecommender


class HybridRecommender:
    """
    混合推荐系统
    
    策略: 加权混合 (Weighted Hybrid)
    将CF和CB的预测评分按权重组合
    
    优化:
    1. 继承CF和CB的预计算优化
    2. 批量预测方法
    3. 减少重复计算
    
    优势:
    1. CF能发现用户潜在兴趣，但存在冷启动问题
    2. CB能处理新物品，但推荐结果较为保守
    3. 混合策略结合两者优势，提升召回率和多样性
    """
    
    def __init__(self, cf_weight=0.6, cb_weight=0.4, cf_type='user'):
        """
        初始化混合推荐模型
        
        Args:
            cf_weight: 协同过滤权重
            cb_weight: 基于内容推荐权重
            cf_type: 协同过滤类型 ('user' 或 'item')
        """
        # 归一化权重
        total = cf_weight + cb_weight
        self.cf_weight = cf_weight / total
        self.cb_weight = cb_weight / total
        self.cf_type = cf_type
        
        self.cf_model = None
        self.cb_model = None
        self.user_movie_matrix = None
        
    def fit(self, user_movie_matrix, movie_features):
        """
        训练混合模型
        
        Args:
            user_movie_matrix: 用户-电影评分矩阵 (DataFrame)
            movie_features: 电影特征字典
        """
        print(f"训练混合推荐模型 (CF权重: {self.cf_weight:.2f}, CB权重: {self.cb_weight:.2f})...")
        
        # 训练协同过滤模型（使用优化版）
        if self.cf_type == 'user':
            self.cf_model = CollaborativeFiltering(k_neighbors=20, min_sim=0.1)
        else:
            self.cf_model = ItemBasedCF(k_neighbors=20, min_sim=0.1)
        
        self.cf_model.fit(user_movie_matrix)
        
        # 训练基于内容模型
        self.cb_model = ContentBasedRecommender()
        self.cb_model.fit(movie_features, user_movie_matrix)
        
        self.user_movie_matrix = user_movie_matrix
        
        print("混合模型训练完成!")
        
    def predict_rating(self, user_id, movie_id):
        """
        预测用户对电影的评分
        
        使用加权平均: score = w_cf * cf_score + w_cb * cb_score
        
        Args:
            user_id: 用户ID
            movie_id: 电影ID
            
        Returns:
            float: 预测评分
        """
        # 获取CF预测
        cf_score = self.cf_model.predict_rating(user_id, movie_id)
        
        # 获取CB预测
        cb_score = self.cb_model.predict_rating(user_id, movie_id)
        
        # 加权平均
        hybrid_score = self.cf_weight * cf_score + self.cb_weight * cb_score
        
        return hybrid_score
    
    def predict_ratings_batch(self, user_id, movie_ids):
        """
        批量预测用户对多个电影的评分
        
        Args:
            user_id: 用户ID
            movie_ids: 电影ID列表
            
        Returns:
            dict: {movie_id: (hybrid_score, cf_score, cb_score)}
        """
        # 批量获取CF预测
        if hasattr(self.cf_model, 'predict_ratings_batch'):
            cf_predictions = self.cf_model.predict_ratings_batch(user_id, movie_ids)
        else:
            cf_predictions = {mid: self.cf_model.predict_rating(user_id, mid) for mid in movie_ids}
        
        # 批量获取CB预测
        cb_predictions = {}
        for movie_id in movie_ids:
            cb_predictions[movie_id] = self.cb_model.predict_rating(user_id, movie_id)
        
        # 计算混合评分
        hybrid_predictions = {}
        for movie_id in movie_ids:
            cf_score = cf_predictions.get(movie_id, 3.0)
            cb_score = cb_predictions.get(movie_id, 3.0)
            hybrid_score = self.cf_weight * cf_score + self.cb_weight * cb_score
            hybrid_predictions[movie_id] = (hybrid_score, cf_score, cb_score)
        
        return hybrid_predictions
    
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
        if user_id not in self.user_movie_matrix.index:
            return []
        
        # 获取用户已评分的电影
        user_ratings = self.user_movie_matrix.loc[user_id]
        rated_movies = set(user_ratings.dropna().index) if exclude_rated else set()
        
        # 获取所有电影（取CF和CB的交集）
        all_movies_cf = set(self.cf_model.user_movie_matrix.columns)
        all_movies_cb = set(self.cb_model.movie_ids)
        all_movies = list(all_movies_cf & all_movies_cb)
        
        # 待预测的电影
        to_predict = [mid for mid in all_movies if mid not in rated_movies]
        
        # 批量预测（优化）
        predictions = self.predict_ratings_batch(user_id, to_predict)
        
        # 转换为列表并排序
        pred_list = [(mid, scores[0]) for mid, scores in predictions.items()]
        pred_list.sort(key=lambda x: x[1], reverse=True)
        
        return pred_list[:n_recommendations]
    
    def recommend_with_details(self, user_id, n_recommendations=10, exclude_rated=True):
        """
        为用户生成推荐列表（包含详细分数）
        
        Args:
            user_id: 目标用户ID
            n_recommendations: 推荐数量
            exclude_rated: 是否排除已评分电影
            
        Returns:
            list: 推荐列表 [(movie_id, hybrid_score, cf_score, cb_score), ...]
        """
        if user_id not in self.user_movie_matrix.index:
            return []
        
        # 获取用户已评分的电影
        user_ratings = self.user_movie_matrix.loc[user_id]
        rated_movies = set(user_ratings.dropna().index) if exclude_rated else set()
        
        # 获取所有电影
        all_movies_cf = set(self.cf_model.user_movie_matrix.columns)
        all_movies_cb = set(self.cb_model.movie_ids)
        all_movies = list(all_movies_cf & all_movies_cb)
        
        # 待预测的电影
        to_predict = [mid for mid in all_movies if mid not in rated_movies]
        
        # 批量预测（优化）
        predictions = self.predict_ratings_batch(user_id, to_predict)
        
        # 转换为列表并排序
        pred_list = [(mid, hybrid, cf, cb) for mid, (hybrid, cf, cb) in predictions.items()]
        pred_list.sort(key=lambda x: x[1], reverse=True)
        
        return pred_list[:n_recommendations]


class SwitchingHybridRecommender:
    """
    切换式混合推荐
    
    根据用户/电影特征动态选择使用CF或CB
    """
    
    def __init__(self, min_ratings_for_cf=5):
        """
        初始化切换式混合模型
        
        Args:
            min_ratings_for_cf: 使用CF的最小评分数量阈值
        """
        self.min_ratings_for_cf = min_ratings_for_cf
        self.cf_model = None
        self.cb_model = None
        self.user_movie_matrix = None
        
    def fit(self, user_movie_matrix, movie_features):
        """
        训练模型
        """
        print("训练切换式混合推荐模型...")
        
        # 训练CF模型（优化版）
        self.cf_model = CollaborativeFiltering(k_neighbors=20, min_sim=0.1)
        self.cf_model.fit(user_movie_matrix)
        
        # 训练CB模型
        self.cb_model = ContentBasedRecommender()
        self.cb_model.fit(movie_features, user_movie_matrix)
        
        self.user_movie_matrix = user_movie_matrix
        
        print("切换式混合模型训练完成!")
        
    def recommend(self, user_id, n_recommendations=10, exclude_rated=True):
        """
        为用户生成推荐
        
        策略: 
        - 用户评分多 -> 使用CF
        - 用户评分少 -> 使用CB
        """
        if user_id not in self.user_movie_matrix.index:
            return []
        
        # 获取用户评分数量
        user_ratings = self.user_movie_matrix.loc[user_id].dropna()
        n_ratings = len(user_ratings)
        
        # 选择模型
        if n_ratings >= self.min_ratings_for_cf:
            return self.cf_model.recommend(user_id, n_recommendations, exclude_rated)
        else:
            return self.cb_model.recommend(user_id, n_recommendations, exclude_rated)


class CascadeHybridRecommender:
    """
    级联式混合推荐
    
    先用CB过滤，再用CF精排
    """
    
    def __init__(self, candidate_size=50):
        """
        初始化级联式混合模型
        
        Args:
            candidate_size: CB阶段生成的候选数量
        """
        self.candidate_size = candidate_size
        self.cf_model = None
        self.cb_model = None
        self.user_movie_matrix = None
        
    def fit(self, user_movie_matrix, movie_features):
        """
        训练模型
        """
        print("训练级联式混合推荐模型...")
        
        # 训练CF模型（优化版）
        self.cf_model = CollaborativeFiltering(k_neighbors=20, min_sim=0.1)
        self.cf_model.fit(user_movie_matrix)
        
        # 训练CB模型
        self.cb_model = ContentBasedRecommender()
        self.cb_model.fit(movie_features, user_movie_matrix)
        
        self.user_movie_matrix = user_movie_matrix
        
        print("级联式混合模型训练完成!")
        
    def recommend(self, user_id, n_recommendations=10, exclude_rated=True):
        """
        为用户生成推荐
        
        策略:
        1. CB生成候选集
        2. CF对候选集精排
        """
        if user_id not in self.user_movie_matrix.index:
            return []
        
        # CB生成候选
        candidates = self.cb_model.recommend(user_id, self.candidate_size, exclude_rated)
        candidate_ids = [mid for mid, _ in candidates]
        
        # CF精排（使用批量预测优化）
        if hasattr(self.cf_model, 'predict_ratings_batch'):
            predictions = self.cf_model.predict_ratings_batch(user_id, candidate_ids)
            ranked = [(mid, predictions.get(mid, 3.0)) for mid in candidate_ids]
        else:
            ranked = [(mid, self.cf_model.predict_rating(user_id, mid)) for mid in candidate_ids]
        
        # 排序
        ranked.sort(key=lambda x: x[1], reverse=True)
        
        return ranked[:n_recommendations]


if __name__ == '__main__':
    # 测试代码
    from data_loader import DataLoader
    
    loader = DataLoader()
    if loader.load_data():
        loader.split_data()
        matrix = loader.get_user_movie_matrix()
        movie_features = loader.get_movie_features()
        
        # 测试加权混合
        print("\n测试优化后的混合推荐...")
        hybrid = HybridRecommender(cf_weight=0.6, cb_weight=0.4)
        hybrid.fit(matrix, movie_features)
        
        # 为第一个用户推荐
        user_id = matrix.index[0]
        recommendations = hybrid.recommend(user_id, n_recommendations=5)
        
        print(f"\n用户 {user_id} 的混合推荐:")
        for movie_id, score in recommendations:
            title = loader.movie_id_to_title.get(movie_id, "Unknown")
            print(f"  {title}: {score:.2f}")
        
        # 详细分数
        print("\n详细分数:")
        details = hybrid.recommend_with_details(user_id, n_recommendations=5)
        for movie_id, hybrid_score, cf_score, cb_score in details:
            title = loader.movie_id_to_title.get(movie_id, "Unknown")
            print(f"  {title}: 混合={hybrid_score:.2f}, CF={cf_score:.2f}, CB={cb_score:.2f}")