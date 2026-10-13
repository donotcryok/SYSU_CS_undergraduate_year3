# -*- coding: utf-8 -*-
"""
推荐系统评估模块
计算召回率、覆盖率、多样性等评估指标
添加采样逻辑和进度提示
"""

import numpy as np
import pandas as pd
import random
from collections import defaultdict

# 尝试导入tqdm，如果不可用则使用简单的进度提示
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("提示: 安装tqdm可获得更好的进度显示 (pip install tqdm)")


class RecommenderEvaluator:
    """
    推荐系统评估器
    
    评估指标:
    1. 召回率 (Recall Rate): 推荐命中数 / 用户实际喜欢数
    2. 覆盖率 (Coverage): 被推荐电影数 / 总电影数
    3. 多样性 (Diversity): 推荐列表中物品间的平均不相似度
    4. 精确率 (Precision): 推荐命中数 / 推荐总数
    
    优化:
    1. 采样评估：默认只评估部分用户，大幅减少计算时间
    2. 进度提示：使用tqdm或简单log显示进度
    3. 批量处理：减少重复计算
    """
    
    def __init__(self, rating_threshold=4.0, default_sample_size=100):
        """
        初始化评估器
        
        Args:
            rating_threshold: 判断用户喜欢的评分阈值
            default_sample_size: 默认采样用户数量
        """
        self.rating_threshold = rating_threshold
        self.default_sample_size = default_sample_size
        
    def evaluate(self, recommender, train_matrix, test_data, movie_features=None, 
                 n_recommendations=10, sample_users=None, show_progress=True):
        """
        评估推荐系统
        
        Args:
            recommender: 推荐模型 (CF/CB/Hybrid)
            train_matrix: 训练集用户-电影矩阵
            test_data: 测试集数据 (DataFrame)
            movie_features: 电影特征字典 (用于计算多样性)
            n_recommendations: 推荐数量
            sample_users: 采样用户列表 (None表示自动采样)
            show_progress: 是否显示进度
            
        Returns:
            dict: 评估指标字典
        """
        print(f"开始评估 (推荐数量: {n_recommendations})...")
        
        # 构建测试集用户-电影映射
        test_user_movies = defaultdict(set)
        for _, row in test_data.iterrows():
            user_id = row['userId']
            movie_id = row['movieId']
            rating = row['rating']
            # 只考虑高分电影作为"用户喜欢"
            if rating >= self.rating_threshold:
                test_user_movies[user_id].add(movie_id)
        
        # 获取测试用户
        all_test_users = list(test_user_movies.keys())
        
        # 采样逻辑：如果未指定采样用户，则自动采样
        if sample_users is None:
            # 过滤掉训练集中没有的用户
            valid_test_users = [uid for uid in all_test_users if uid in train_matrix.index]
            
            # 采样
            sample_size = min(self.default_sample_size, len(valid_test_users))
            sample_users = random.sample(valid_test_users, sample_size)
            
            print(f"自动采样 {sample_size} 个用户进行评估 (共 {len(valid_test_users)} 个有效测试用户)")
        else:
            # 过滤采样用户中训练集没有的
            sample_users = [uid for uid in sample_users if uid in train_matrix.index]
            print(f"使用指定的 {len(sample_users)} 个采样用户进行评估")
        
        # 计算电影相似度矩阵（用于多样性）
        movie_similarity = self._compute_movie_similarity(movie_features) if movie_features else None
        
        # 初始化统计变量
        total_recall = 0.0
        total_precision = 0.0
        total_diversity = 0.0
        all_recommended_movies = set()
        valid_users = 0
        
        # 进度显示
        if show_progress:
            if HAS_TQDM:
                user_iterator = tqdm(sample_users, desc="评估用户", unit="用户")
            else:
                user_iterator = sample_users
                print(f"开始评估 {len(sample_users)} 个用户...")
        else:
            user_iterator = sample_users
        
        # 评估每个用户
        for i, user_id in enumerate(user_iterator):
            # 获取用户实际喜欢的电影
            actual_movies = test_user_movies.get(user_id, set())
            
            if len(actual_movies) == 0:
                continue
            
            valid_users += 1
            
            try:
                # 获取推荐列表
                recommendations = recommender.recommend(user_id, n_recommendations, exclude_rated=True)
                recommended_movies = set([mid for mid, _ in recommendations])
                
                # 更新被推荐电影集合
                all_recommended_movies.update(recommended_movies)
                
                # 计算命中数
                hits = len(recommended_movies & actual_movies)
                
                # 召回率
                recall = hits / len(actual_movies)
                total_recall += recall
                
                # 精确率
                precision = hits / n_recommendations
                total_precision += precision
                
                # 多样性
                if movie_similarity is not None and len(recommendations) > 1:
                    diversity = self._compute_diversity(recommendations, movie_similarity)
                    total_diversity += diversity
                    
            except Exception as e:
                print(f"用户 {user_id} 推荐失败: {e}")
                continue
            
            # 简单进度提示（无tqdm时）
            if show_progress and not HAS_TQDM:
                if (i + 1) % 10 == 0 or (i + 1) == len(sample_users):
                    print(f"  已评估 {i + 1}/{len(sample_users)} 个用户...")
        
        # 计算平均值
        n_valid_users = max(valid_users, 1)
        avg_recall = total_recall / n_valid_users
        avg_precision = total_precision / n_valid_users
        avg_diversity = total_diversity / n_valid_users if movie_similarity else 0
        
        # 覆盖率
        total_movies = len(train_matrix.columns)
        coverage = len(all_recommended_movies) / total_movies if total_movies > 0 else 0
        
        # F1分数
        f1 = 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall) if (avg_precision + avg_recall) > 0 else 0
        
        results = {
            'recall': avg_recall,
            'precision': avg_precision,
            'f1_score': f1,
            'coverage': coverage,
            'diversity': avg_diversity,
            'n_users': valid_users,
            'n_movies_recommended': len(all_recommended_movies)
        }
        
        print(f"评估完成! 有效用户数: {valid_users}")
        
        return results
    
    def _compute_movie_similarity(self, movie_features):
        """
        计算电影相似度矩阵（基于内容特征）
        
        Args:
            movie_features: 电影特征字典
            
        Returns:
            dict: 电影对相似度字典
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        movie_ids = list(movie_features.keys())
        documents = [movie_features[mid].get('combined', '') for mid in movie_ids]
        
        if not any(documents):
            return None
        
        try:
            print("计算电影相似度矩阵（用于多样性评估）...")
            vectorizer = TfidfVectorizer(max_features=1000)
            tfidf_matrix = vectorizer.fit_transform(documents)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # 转换为字典（只存储非零相似度，节省内存）
            movie_sim = {}
            n_movies = len(movie_ids)
            
            for i in range(n_movies):
                for j in range(i + 1, n_movies):
                    sim = similarity_matrix[i, j]
                    if sim > 0.01:  # 只存储有意义的相似度
                        mid_i = movie_ids[i]
                        mid_j = movie_ids[j]
                        movie_sim[(mid_i, mid_j)] = sim
                        movie_sim[(mid_j, mid_i)] = sim
            
            print(f"电影相似度计算完成，共 {len(movie_sim)} 对")
            return movie_sim
        except Exception as e:
            print(f"计算电影相似度失败: {e}")
            return None
    
    def _compute_diversity(self, recommendations, movie_similarity):
        """
        计算推荐列表的多样性
        
        多样性 = 推荐列表中物品对的平均不相似度
        
        Args:
            recommendations: 推荐列表 [(movie_id, score), ...]
            movie_similarity: 电影相似度字典
            
        Returns:
            float: 多样性值
        """
        movie_ids = [mid for mid, _ in recommendations]
        n = len(movie_ids)
        
        if n < 2:
            return 0
        
        total_dissimilarity = 0
        count = 0
        
        for i in range(n):
            for j in range(i + 1, n):
                sim = movie_similarity.get((movie_ids[i], movie_ids[j]), 0)
                total_dissimilarity += (1 - sim)
                count += 1
        
        return total_dissimilarity / count if count > 0 else 0
    
    def compare_recommenders(self, recommenders, train_matrix, test_data, 
                            movie_features=None, n_recommendations=10, 
                            sample_size=None, show_progress=True):
        """
        比较多个推荐系统的性能
        
        Args:
            recommenders: 推荐模型字典 {'name': model}
            train_matrix: 训练集用户-电影矩阵
            test_data: 测试集数据
            movie_features: 电影特征字典
            n_recommendations: 推荐数量
            sample_size: 采样用户数量
            show_progress: 是否显示进度
            
        Returns:
            DataFrame: 比较结果表格
        """
        results = []
        
        # 设置采样大小
        if sample_size is None:
            sample_size = self.default_sample_size
        
        # 构建测试集用户-电影映射
        test_user_movies = defaultdict(set)
        for _, row in test_data.iterrows():
            if row['rating'] >= self.rating_threshold:
                test_user_movies[row['userId']].add(row['movieId'])
        
        # 获取有效测试用户并采样
        all_test_users = list(test_user_movies.keys())
        valid_test_users = [uid for uid in all_test_users if uid in train_matrix.index]
        actual_sample_size = min(sample_size, len(valid_test_users))
        sample_users = random.sample(valid_test_users, actual_sample_size)
        
        print(f"\n使用 {actual_sample_size} 个采样用户进行模型对比评估")
        
        # 计算电影相似度（所有模型共用）
        movie_similarity = self._compute_movie_similarity(movie_features) if movie_features else None
        
        for name, model in recommenders.items():
            print(f"\n{'='*50}")
            print(f"评估模型: {name}")
            print(f"{'='*50}")
            
            metrics = self._evaluate_single_model(
                model, train_matrix, test_user_movies, 
                movie_similarity, n_recommendations, 
                sample_users, show_progress
            )
            metrics['model'] = name
            results.append(metrics)
        
        # 转换为DataFrame
        df = pd.DataFrame(results)
        df = df.set_index('model')
        
        return df
    
    def _evaluate_single_model(self, model, train_matrix, test_user_movies, 
                               movie_similarity, n_recommendations, 
                               sample_users, show_progress):
        """
        评估单个模型
        
        Args:
            model: 推荐模型
            train_matrix: 训练集矩阵
            test_user_movies: 测试集用户-电影映射
            movie_similarity: 电影相似度字典
            n_recommendations: 推荐数量
            sample_users: 采样用户列表
            show_progress: 是否显示进度
            
        Returns:
            dict: 评估指标
        """
        # 初始化统计变量
        total_recall = 0.0
        total_precision = 0.0
        total_diversity = 0.0
        all_recommended_movies = set()
        valid_users = 0
        
        # 进度显示
        if show_progress:
            if HAS_TQDM:
                user_iterator = tqdm(sample_users, desc=f"评估", unit="用户")
            else:
                user_iterator = sample_users
                print(f"开始评估 {len(sample_users)} 个用户...")
        else:
            user_iterator = sample_users
        
        # 评估每个用户
        for i, user_id in enumerate(user_iterator):
            actual_movies = test_user_movies.get(user_id, set())
            
            if len(actual_movies) == 0:
                continue
            
            valid_users += 1
            
            try:
                recommendations = model.recommend(user_id, n_recommendations, exclude_rated=True)
                recommended_movies = set([mid for mid, _ in recommendations])
                
                all_recommended_movies.update(recommended_movies)
                
                hits = len(recommended_movies & actual_movies)
                
                recall = hits / len(actual_movies)
                total_recall += recall
                
                precision = hits / n_recommendations
                total_precision += precision
                
                if movie_similarity is not None and len(recommendations) > 1:
                    diversity = self._compute_diversity(recommendations, movie_similarity)
                    total_diversity += diversity
                    
            except Exception as e:
                print(f"用户 {user_id} 推荐失败: {e}")
                continue
            
            # 简单进度提示
            if show_progress and not HAS_TQDM:
                if (i + 1) % 10 == 0 or (i + 1) == len(sample_users):
                    print(f"  已评估 {i + 1}/{len(sample_users)} 个用户...")
        
        # 计算平均值
        n_valid_users = max(valid_users, 1)
        avg_recall = total_recall / n_valid_users
        avg_precision = total_precision / n_valid_users
        avg_diversity = total_diversity / n_valid_users if movie_similarity else 0
        
        total_movies = len(train_matrix.columns)
        coverage = len(all_recommended_movies) / total_movies if total_movies > 0 else 0
        
        f1 = 2 * (avg_precision * avg_recall) / (avg_precision + avg_recall) if (avg_precision + avg_recall) > 0 else 0
        
        return {
            'recall': avg_recall,
            'precision': avg_precision,
            'f1_score': f1,
            'coverage': coverage,
            'diversity': avg_diversity,
            'n_users': valid_users,
            'n_movies_recommended': len(all_recommended_movies)
        }


def print_evaluation_results(results, model_name="模型"):
    """
    打印评估结果
    
    Args:
        results: 评估结果字典
        model_name: 模型名称
    """
    print(f"\n{'='*50}")
    print(f"{model_name} 评估结果")
    print(f"{'='*50}")
    print(f"召回率 (Recall):    {results['recall']:.4f}")
    print(f"精确率 (Precision): {results['precision']:.4f}")
    print(f"F1分数:             {results['f1_score']:.4f}")
    print(f"覆盖率 (Coverage):  {results['coverage']:.4f}")
    print(f"多样性 (Diversity): {results['diversity']:.4f}")
    print(f"有效用户数:          {results['n_users']}")
    print(f"推荐电影数:          {results['n_movies_recommended']}")
    print(f"{'='*50}")


if __name__ == '__main__':
    # 测试代码
    from data_loader import DataLoader
    from collaborative_filtering import CollaborativeFiltering
    from content_based import ContentBasedRecommender
    from hybrid_recommender import HybridRecommender
    
    loader = DataLoader()
    if loader.load_data():
        loader.split_data()
        train_matrix = loader.get_user_movie_matrix()
        movie_features = loader.get_movie_features()
        
        # 训练模型（使用优化版）
        print("\n训练模型...")
        cf = CollaborativeFiltering(k_neighbors=20)
        cf.fit(train_matrix)
        
        cb = ContentBasedRecommender()
        cb.fit(movie_features, train_matrix)
        
        hybrid = HybridRecommender(cf_weight=0.6, cb_weight=0.4)
        hybrid.fit(train_matrix, movie_features)
        
        # 评估（使用采样）
        evaluator = RecommenderEvaluator(rating_threshold=4.0, default_sample_size=50)
        
        results = evaluator.compare_recommenders(
            {'CF': cf, 'CB': cb, 'Hybrid': hybrid},
            train_matrix, loader.test_data,
            movie_features, n_recommendations=10,
            sample_size=50
        )
        
        print("\n模型对比结果:")
        print(results)