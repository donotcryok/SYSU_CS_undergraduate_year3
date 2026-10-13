"""
主程序入口
整合所有模块，运行完整的推荐系统流程
"""

import os
import sys
import time
import warnings
warnings.filterwarnings('ignore')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_preprocessing import DataPreprocessor
from collaborative_filtering import ClubBasedCF, PlayerSimilarityCF
from content_based import ContentBasedRecommender
from hybrid_recommender import HybridRecommender
from evaluation import RecommenderEvaluator
from visualization.visualizer import Visualizer


def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def run_data_analysis(preprocessor, visualizer):
    """运行数据分析"""
    print_header("第一阶段：数据探索性分析")
    
    stats = preprocessor.get_statistics()
    print("\n数据集统计信息:")
    print(f"  - 球员数量: {stats['n_players']}")
    print(f"  - 俱乐部数量: {stats['n_clubs']}")
    print(f"  - 转会记录数: {stats['n_transfers']}")
    if 'avg_age' in stats:
        print(f"  - 平均年龄: {stats['avg_age']:.1f}")
    if 'position_distribution' in stats:
        print(f"  - 位置分布: {stats['position_distribution']}")
    
    print("\n身价最高的10位球员:")
    top_players = preprocessor.get_top_players(10)
    if len(top_players) > 0:
        print(top_players[['player_name', 'age', 'main_position', 'current_club_name', 'market_value']].to_string(index=False))
    
    print("\n生成数据可视化图表...")
    visualizer.create_eda_report(preprocessor.players_df)
    
    return stats


def run_individual_models(preprocessor):
    """运行各个独立模型"""
    print_header("第二阶段：训练独立推荐模型")
    
    results = {}
    
    print("\n[1/3] 训练基于内容的推荐...")
    cb = ContentBasedRecommender()
    cb.fit(preprocessor.players_df)
    results['Content-Based'] = cb
    
    if preprocessor.transfers_df is not None:
        print("\n[2/3] 训练俱乐部协同过滤...")
        cf = ClubBasedCF(k_neighbors=10)
        cf.fit(preprocessor.transfers_df, preprocessor.players_df)
        results['Club-CF'] = cf
    
    print("\n[3/3] 训练球员相似度模型...")
    player_cf = PlayerSimilarityCF()
    player_cf.fit(preprocessor.players_df)
    results['Player-Sim'] = player_cf
    
    return results


def run_hybrid_model(preprocessor):
    """运行混合推荐模型"""
    print_header("第三阶段：训练混合推荐模型")
    
    hybrid = HybridRecommender(content_weight=0.4, cf_weight=0.3, position_weight=0.3)
    hybrid.fit(preprocessor.players_df, preprocessor.transfers_df)
    
    return hybrid


def run_evaluation(hybrid_model, preprocessor, visualizer):
    """运行模型评估"""
    print_header("第四阶段：模型评估")
    
    evaluator = RecommenderEvaluator()
    
    # 选择一些俱乐部进行评估
    if preprocessor.transfers_df is not None:
        test_clubs = preprocessor.transfers_df['to_club_id'].unique()[:20].tolist()
    elif 'current_club_id' in preprocessor.players_df.columns:
        test_clubs = preprocessor.players_df['current_club_id'].unique()[:20].tolist()
    else:
        print("没有俱乐部数据，跳过评估")
        return {}
    
    print("\n评估混合推荐模型...")
    results = evaluator.evaluate_model(hybrid_model, test_clubs, preprocessor.players_df)
    
    evaluator.print_results(results, "Hybrid Recommender")
    
    return results


def run_recommendation_demo(hybrid_model, preprocessor, visualizer):
    """运行推荐演示"""
    print_header("第五阶段：推荐演示")
    
    # 选择几个俱乐部进行演示
    if preprocessor.transfers_df is not None:
        test_clubs = preprocessor.transfers_df['to_club_id'].unique()[:3]
    elif 'current_club_id' in preprocessor.players_df.columns:
        test_clubs = preprocessor.players_df['current_club_id'].unique()[:3]
    else:
        print("没有俱乐部数据，跳过演示")
        return
    
    for club_id in test_clubs:
        print(f"\n{'='*40}")
        
        # 获取俱乐部名称
        club_name = f"俱乐部 {club_id}"
        if 'current_club_name' in preprocessor.players_df.columns:
            club_players = preprocessor.players_df[preprocessor.players_df['current_club_id'] == club_id]
            if len(club_players) > 0:
                club_name = club_players.iloc[0].get('current_club_name', club_name)
        
        print(f"俱乐部: {club_name}")
        print(f"{'='*40}")
        
        # 球队现有阵容
        if 'current_club_id' in preprocessor.players_df.columns:
            club_players = preprocessor.players_df[preprocessor.players_df['current_club_id'] == club_id]
            print(f"现有球员数: {len(club_players)}")
            if len(club_players) > 0 and 'age' in club_players.columns:
                print(f"平均年龄: {club_players['age'].mean():.1f}")
        
        # 获取推荐
        print("\n推荐签约球员:")
        try:
            recommendations = hybrid_model.recommend_for_club(club_id, n_items=5)
            
            for i, (player_id, score) in enumerate(recommendations, 1):
                player = preprocessor.players_df[preprocessor.players_df['player_id'] == player_id]
                if len(player) > 0:
                    p = player.iloc[0]
                    explanation = hybrid_model.get_recommendation_explanation(player_id, club_id)
                    player_name = p.get('player_name', f'Player_{player_id}')
                    position = p.get('main_position', p.get('position_category', '-'))
                    age = p.get('age', '-')
                    market_value = p.get('market_value', 0)
                    
                    print(f"  {i}. {player_name} ({position})")
                    print(f"     年龄: {age} | 身价: {market_value/1000000:.1f}M€")
                    print(f"     推荐理由: {explanation}")
        except Exception as e:
            print(f"  推荐失败: {e}")
    
    # 测试相似球员推荐
    print("\n\n测试相似球员推荐:")
    # 找一个高身价球员
    if 'market_value' in preprocessor.players_df.columns:
        top_player = preprocessor.players_df.nlargest(1, 'market_value').iloc[0]
    else:
        top_player = preprocessor.players_df.iloc[0]
    
    player_name = top_player.get('player_name', 'Unknown')
    position = top_player.get('main_position', '-')
    print(f"目标球员: {player_name} ({position})")
    
    try:
        similar = hybrid_model.recommend_similar_player(top_player['player_id'], n_items=5)
        print("\n相似球员:")
        for pid, score in similar:
            p = preprocessor.players_df[preprocessor.players_df['player_id'] == pid].iloc[0]
            name = p.get('player_name', pid)
            pos = p.get('main_position', '-')
            print(f"  - {name} ({pos}): 相似度 {score:.3f}")
    except Exception as e:
        print(f"  推荐失败: {e}")


def main():
    """主函数"""
    start_time = time.time()
    
    print_header("足球球员智能推荐系统")
    print("\n项目特点:")
    print("  1. 球队需求感知：根据球队阵容缺口调整推荐权重")
    print("  2. 多维度相似度融合：综合球员能力、身价、年龄的相似度")
    print("  3. 混合推荐策略：结合协同过滤和基于内容的推荐")
    
    # 1. 数据准备
    print("\n正在准备数据...")
    preprocessor = DataPreprocessor()
    preprocessor.load_data().clean_data().feature_engineering()
    
    # 2. 数据分析
    visualizer = Visualizer(output_dir='img')
    stats = run_data_analysis(preprocessor, visualizer)
    
    # 3. 训练独立模型
    individual_models = run_individual_models(preprocessor)
    
    # 4. 训练混合模型
    hybrid_model = run_hybrid_model(preprocessor)
    
    # 5. 评估
    eval_results = run_evaluation(hybrid_model, preprocessor, visualizer)
    
    # 6. 推荐演示
    run_recommendation_demo(hybrid_model, preprocessor, visualizer)
    
    # 7. 保存结果
    print_header("保存结果")
    output_dir = 'img'
    os.makedirs(output_dir, exist_ok=True)
    
    elapsed_time = time.time() - start_time
    print(f"\n总运行时间: {elapsed_time:.2f} 秒")
    
    print_header("实验完成!")
    
    return hybrid_model, preprocessor


if __name__ == '__main__':
    main()
