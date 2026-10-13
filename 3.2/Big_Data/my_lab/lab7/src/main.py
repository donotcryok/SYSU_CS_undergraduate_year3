# -*- coding: utf-8 -*-
"""
混合推荐系统主程序
整合协同过滤、基于内容推荐和混合策略，并进行评估对比
"""

import os
import sys
import time
import warnings
import random
import numpy as np
warnings.filterwarnings('ignore')

# 添加src目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_loader import DataLoader
from collaborative_filtering import CollaborativeFiltering, ItemBasedCF
from content_based import ContentBasedRecommender
from hybrid_recommender import HybridRecommender
from evaluation import RecommenderEvaluator, print_evaluation_results
from visualization import RecommenderVisualizer


def main():
    """
    主函数：执行完整的推荐系统实验流程
    """
    print("=" * 60)
    print("混合推荐系统实验（优化版）")
    print("=" * 60)
    
    # ==================== 1. 数据加载 ====================
    print("\n[步骤1] 加载数据...")
    loader = DataLoader(data_dir='../data/')
    
    if not loader.load_data():
        print("数据加载失败，程序退出!")
        return
    
    # 划分训练集和测试集
    loader.split_data(test_size=0.2, random_state=42)
    
    # 获取用户-电影评分矩阵
    train_matrix = loader.get_user_movie_matrix()
    print(f"评分矩阵形状: {train_matrix.shape}")
    
    # 获取电影特征
    movie_features = loader.get_movie_features()
    print(f"电影特征数量: {len(movie_features)}")
    
    # ==================== 2. 模型训练 ====================
    print("\n[步骤2] 训练推荐模型...")
    
    # 2.1 协同过滤 (User-based CF) - 使用优化版
    print("\n--- 协同过滤 (User-based CF) ---")
    start_time = time.time()
    cf_model = CollaborativeFiltering(k_neighbors=20, min_sim=0.1)
    cf_model.fit(train_matrix)
    cf_train_time = time.time() - start_time
    print(f"训练时间: {cf_train_time:.2f}秒")
    
    # 2.2 基于内容推荐 (CB)
    print("\n--- 基于内容推荐 (CB) ---")
    start_time = time.time()
    cb_model = ContentBasedRecommender(min_df=1, max_features=5000)
    cb_model.fit(movie_features, train_matrix)
    cb_train_time = time.time() - start_time
    print(f"训练时间: {cb_train_time:.2f}秒")
    
    # 2.3 混合推荐 (Hybrid) - 使用优化版
    print("\n--- 混合推荐 (Hybrid) ---")
    start_time = time.time()
    hybrid_model = HybridRecommender(cf_weight=0.6, cb_weight=0.4, cf_type='user')
    hybrid_model.fit(train_matrix, movie_features)
    hybrid_train_time = time.time() - start_time
    print(f"训练时间: {hybrid_train_time:.2f}秒")
    
    # ==================== 3. 模型评估 ====================
    print("\n[步骤3] 评估模型性能...")
    
    # 使用优化后的评估器，设置采样大小
    # 默认采样100个用户，可在1-2分钟内完成评估
    evaluator = RecommenderEvaluator(rating_threshold=4.0, default_sample_size=100)
    
    n_recommendations = 10
    
    # 使用compare_recommenders方法进行批量评估
    # 该方法会自动采样用户并显示进度
    results_df = evaluator.compare_recommenders(
        {'CF': cf_model, 'CB': cb_model, 'Hybrid': hybrid_model},
        train_matrix, loader.test_data,
        movie_features, n_recommendations,
        sample_size=100,  # 采样100个用户
        show_progress=True
    )
    
    # 打印各模型结果
    for model_name in results_df.index:
        results = results_df.loc[model_name].to_dict()
        print_evaluation_results(results, model_name)
    
    # ==================== 4. 结果对比 ====================
    print("\n[步骤4] 生成对比结果...")
    
    # 添加训练时间
    results_df['train_time'] = [cf_train_time, cb_train_time, hybrid_train_time]
    
    print("\n" + "=" * 60)
    print("模型性能对比汇总")
    print("=" * 60)
    print(results_df.to_string())
    
    # ==================== 5. 可视化 ====================
    print("\n[步骤5] 生成可视化图表...")
    
    visualizer = RecommenderVisualizer(output_dir='../img/')
    visualizer.generate_all_plots(results_df)
    
    # ==================== 6. 示例推荐 ====================
    print("\n[步骤6] 示例推荐展示...")
    
    # 选择一个测试用户
    test_users = list(train_matrix.index[:5])
    test_user = test_users[0]
    print(f"\n为用户 {test_user} 生成推荐:")
    
    # CF推荐
    cf_recs = cf_model.recommend(test_user, n_recommendations=5)
    print("\n协同过滤推荐:")
    for i, (movie_id, score) in enumerate(cf_recs, 1):
        title = loader.movie_id_to_title.get(movie_id, "Unknown")
        print(f"  {i}. {title} (预测评分: {score:.2f})")
    
    # CB推荐
    cb_recs = cb_model.recommend(test_user, n_recommendations=5)
    print("\n基于内容推荐:")
    for i, (movie_id, score) in enumerate(cb_recs, 1):
        title = loader.movie_id_to_title.get(movie_id, "Unknown")
        print(f"  {i}. {title} (预测评分: {score:.2f})")
    
    # Hybrid推荐
    hybrid_recs = hybrid_model.recommend_with_details(test_user, n_recommendations=5)
    print("\n混合推荐:")
    for i, (movie_id, hybrid_score, cf_score, cb_score) in enumerate(hybrid_recs, 1):
        title = loader.movie_id_to_title.get(movie_id, "Unknown")
        print(f"  {i}. {title} (混合: {hybrid_score:.2f}, CF: {cf_score:.2f}, CB: {cb_score:.2f})")
    
    # ==================== 7. 保存结果 ====================
    print("\n[步骤7] 保存结果...")
    
    # 保存结果到CSV
    results_path = '../img/evaluation_results.csv'
    results_df.to_csv(results_path, encoding='utf-8-sig')
    print(f"评估结果已保存: {results_path}")
    
    # ==================== 8. 结果持久化到result.txt ====================
    print("\n[步骤8] 写入结果报告...")
    
    from datetime import datetime
    result_txt_path = 'result.txt'
    
    with open(result_txt_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("混合推荐系统实验结果报告\n")
        f.write("=" * 60 + "\n\n")
        
        # 时间戳
        f.write(f"实验时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"数据集: MovieLens ml-latest-small\n")
        f.write(f"采样用户数: 100\n")
        f.write(f"推荐数量: {n_recommendations}\n\n")
        
        # 各模型核心指标
        f.write("-" * 60 + "\n")
        f.write("各模型评估指标\n")
        f.write("-" * 60 + "\n\n")
        
        for model_name in results_df.index:
            f.write(f"【{model_name} 模型】\n")
            f.write(f"  召回率 (Recall):    {results_df.loc[model_name, 'recall']:.4f}\n")
            f.write(f"  精确率 (Precision): {results_df.loc[model_name, 'precision']:.4f}\n")
            f.write(f"  F1分数:             {results_df.loc[model_name, 'f1_score']:.4f}\n")
            f.write(f"  覆盖率 (Coverage):  {results_df.loc[model_name, 'coverage']:.4f}\n")
            f.write(f"  多样性 (Diversity): {results_df.loc[model_name, 'diversity']:.4f}\n")
            f.write(f"  有效用户数:         {results_df.loc[model_name, 'n_users']}\n")
            f.write(f"  推荐电影数:         {results_df.loc[model_name, 'n_movies_recommended']}\n")
            f.write(f"  训练时间:           {results_df.loc[model_name, 'train_time']:.2f}秒\n")
            f.write("\n")
        
        # 关键结论
        f.write("-" * 60 + "\n")
        f.write("关键结论\n")
        f.write("-" * 60 + "\n\n")
        
        f.write(f"1. 召回率最高: {results_df['recall'].idxmax()} ({results_df['recall'].max():.4f})\n")
        f.write(f"2. 覆盖率最高: {results_df['coverage'].idxmax()} ({results_df['coverage'].max():.4f})\n")
        f.write(f"3. 多样性最高: {results_df['diversity'].idxmax()} ({results_df['diversity'].max():.4f})\n\n")
        
        # 混合策略分析
        cf_recall = results_df.loc['CF', 'recall']
        cb_recall = results_df.loc['CB', 'recall']
        hybrid_recall = results_df.loc['Hybrid', 'recall']
        
        f.write("混合策略分析:\n")
        if hybrid_recall > max(cf_recall, cb_recall):
            f.write(f"  混合策略成功提升了召回率! (提升: {hybrid_recall - max(cf_recall, cb_recall):.4f})\n")
        elif hybrid_recall > min(cf_recall, cb_recall):
            f.write(f"  混合策略召回率介于CF和CB之间，实现了折中。\n")
        else:
            f.write(f"  混合策略召回率较低，可能需要调整权重。\n")
        
        f.write("\n")
        
        f.write("\n" + "=" * 60 + "\n")
        f.write("报告结束\n")
        f.write("=" * 60 + "\n")
    
    print(f"结果报告已保存: {result_txt_path}")
    
    print("\n" + "=" * 60)
    print("实验完成!")
    print("=" * 60)

if __name__ == '__main__':
    # 设置随机种子，确保结果可复现
    random.seed(42)
    np.random.seed(42)
    
    main()