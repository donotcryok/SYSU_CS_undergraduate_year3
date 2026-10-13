# -*- coding: utf-8 -*-
"""
推荐系统评估模块
包含多种评估指标
"""

import numpy as np
import pandas as pd
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')


class RecommenderEvaluator:
    """推荐系统评估器"""
    
    def __init__(self):
        self.results = {}
        
    def precision_at_k(self, recommended, relevant, k):
        """计算Precision@K"""
        recommended_k = recommended[:k]
        relevant_set = set(relevant)
        hits = len([r for r in recommended_k if r in relevant_set])
        return hits / k if k > 0 else 0
    
    def recall_at_k(self, recommended, relevant, k):
        """计算Recall@K"""
        recommended_k = recommended[:k]
        relevant_set = set(relevant)
        hits = len([r for r in recommended_k if r in relevant_set])
        return hits / len(relevant_set) if len(relevant_set) > 0 else 0
    
    def ndcg_at_k(self, recommended, relevant, k):
        """计算NDCG@K"""
        relevant_set = set(relevant)
        recommended_k = recommended[:k]
        
        dcg = 0
        for i, item in enumerate(recommended_k):
            if item in relevant_set:
                dcg += 1 / np.log2(i + 2)
        
        ideal_length = min(len(relevant_set), k)
        idcg = sum(1 / np.log2(i + 2) for i in range(ideal_length))
        
        return dcg / idcg if idcg > 0 else 0
    
    def coverage(self, all_recommendations, all_items):
        """计算覆盖率"""
        recommended_items = set()
        for user_recs in all_recommendations.values():
            recommended_items.update(user_recs)
        return len(recommended_items) / len(all_items) if len(all_items) > 0 else 0
    
    def diversity(self, recommendations, players_df):
        """计算推荐多样性"""
        if len(recommendations) < 2:
            return 0
        
        positions = []
        for player_id in recommendations:
            player = players_df[players_df['player_id'] == player_id]
            if len(player) > 0:
                positions.append(player.iloc[0].get('position_category', 'Unknown'))
        
        unique_positions = len(set(positions))
        return unique_positions / len(positions) if len(positions) > 0 else 0
    
    def position_need_satisfaction(self, recommendations, club_id, players_df):
        """位置需求满足度评估"""
        if 'current_club_id' not in players_df.columns:
            return 0
            
        club_players = players_df[players_df['current_club_id'] == club_id]
        
        if len(club_players) == 0 or 'position_category' not in club_players.columns:
            return 0
        
        position_counts = club_players['position_category'].value_counts()
        ideal_counts = {'Goalkeeper': 3, 'Defender': 8, 'Midfielder': 7, 'Forward': 5}
        
        needs = {}
        for pos, ideal in ideal_counts.items():
            current = position_counts.get(pos, 0)
            needs[pos] = max(0, ideal - current)
        
        satisfied = 0
        total_needed = sum(needs.values())
        
        if total_needed == 0:
            return 1.0
        
        for player_id in recommendations:
            player = players_df[players_df['player_id'] == player_id]
            if len(player) > 0:
                pos = player.iloc[0].get('position_category', '')
                if needs.get(pos, 0) > 0:
                    satisfied += 1
                    needs[pos] -= 1
        
        return satisfied / min(len(recommendations), total_needed)
    
    def evaluate_model(self, model, test_clubs, players_df, k_values=[5, 10]):
        """综合评估模型"""
        print("开始评估模型...")
        
        results = {
            'ranking_metrics': {},
            'beyond_accuracy_metrics': {},
            'domain_metrics': {}
        }
        
        all_recommendations = {}
        all_items = set(players_df['player_id'].values)
        
        precisions = {k: [] for k in k_values}
        recalls = {k: [] for k in k_values}
        ndcgs = {k: [] for k in k_values}
        diversities = []
        satisfactions = []
        
        for club_id in test_clubs:
            try:
                recs = model.recommend_for_club(club_id, n_items=max(k_values))
            except Exception as e:
                continue
                
            if not recs:
                continue
            
            rec_items = [pid for pid, _ in recs]
            all_recommendations[club_id] = rec_items
            
            if 'current_club_id' in players_df.columns and 'market_value' in players_df.columns:
                club_players = players_df[players_df['current_club_id'] == club_id]
                if len(club_players) > 0:
                    relevant = club_players.nlargest(min(20, len(club_players)), 'market_value')['player_id'].tolist()
                else:
                    relevant = players_df.nlargest(50, 'market_value')['player_id'].tolist()
            else:
                relevant = players_df.head(50)['player_id'].tolist()
            
            for k in k_values:
                precisions[k].append(self.precision_at_k(rec_items, relevant, k))
                recalls[k].append(self.recall_at_k(rec_items, relevant, k))
                ndcgs[k].append(self.ndcg_at_k(rec_items, relevant, k))
            
            diversities.append(self.diversity(rec_items, players_df))
            satisfaction = self.position_need_satisfaction(rec_items, club_id, players_df)
            satisfactions.append(satisfaction)
        
        for k in k_values:
            results['ranking_metrics'][f'Precision@{k}'] = np.mean(precisions[k]) if precisions[k] else 0
            results['ranking_metrics'][f'Recall@{k}'] = np.mean(recalls[k]) if recalls[k] else 0
            results['ranking_metrics'][f'NDCG@{k}'] = np.mean(ndcgs[k]) if ndcgs[k] else 0
        
        results['beyond_accuracy_metrics']['Coverage'] = self.coverage(all_recommendations, all_items)
        results['beyond_accuracy_metrics']['Diversity'] = np.mean(diversities) if diversities else 0
        
        results['domain_metrics']['PositionNeedSatisfaction'] = np.mean(satisfactions) if satisfactions else 0
        
        print("评估完成!")
        return results
    
    def compare_models(self, models_dict, test_clubs, players_df, k_values=[5, 10]):
        """比较多个模型"""
        all_results = {}
        
        for name, model in models_dict.items():
            print(f"\n评估模型: {name}")
            results = self.evaluate_model(model, test_clubs, players_df, k_values)
            all_results[name] = results
        
        comparison_data = []
        for name, results in all_results.items():
            row = {'Model': name}
            row.update(results['ranking_metrics'])
            row.update(results['beyond_accuracy_metrics'])
            row.update(results['domain_metrics'])
            comparison_data.append(row)
        
        comparison_df = pd.DataFrame(comparison_data)
        return comparison_df, all_results
    
    def print_results(self, results, model_name="Model"):
        """打印评估结果"""
        print(f"\n{'='*50}")
        print(f"评估结果: {model_name}")
        print(f"{'='*50}")
        
        if 'ranking_metrics' in results and results['ranking_metrics']:
            print("\n排序质量指标:")
            for metric, value in results['ranking_metrics'].items():
                print(f"  {metric}: {value:.4f}")
        
        if 'beyond_accuracy_metrics' in results:
            print("\n其他指标:")
            for metric, value in results['beyond_accuracy_metrics'].items():
                metric_cn = {'Coverage': '覆盖率', 'Diversity': '多样性'}
                print(f"  {metric_cn.get(metric, metric)}: {value:.4f}")
        
        if 'domain_metrics' in results:
            print("\n领域指标:")
            for metric, value in results['domain_metrics'].items():
                metric_cn = {'PositionNeedSatisfaction': '位置需求满足度'}
                print(f"  {metric_cn.get(metric, metric)}: {value:.4f}")


if __name__ == '__main__':
    evaluator = RecommenderEvaluator()
    
    recommended = ['p1', 'p2', 'p3', 'p4', 'p5']
    relevant = ['p1', 'p3', 'p6', 'p7']
    
    print("Precision@3:", evaluator.precision_at_k(recommended, relevant, 3))
    print("Recall@3:", evaluator.recall_at_k(recommended, relevant, 3))
    print("NDCG@3:", evaluator.ndcg_at_k(recommended, relevant, 3))
