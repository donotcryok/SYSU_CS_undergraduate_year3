# -*- coding: utf-8 -*-
"""
混合推荐算法模块
结合协同过滤、基于内容推荐和位置需求感知
"""

import numpy as np
import pandas as pd
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

try:
    from .collaborative_filtering import ClubBasedCF, PlayerSimilarityCF
    from .content_based import ContentBasedRecommender, PositionBasedRecommender
except ImportError:
    from collaborative_filtering import ClubBasedCF, PlayerSimilarityCF
    from content_based import ContentBasedRecommender, PositionBasedRecommender


class HybridRecommender:
    """混合推荐算法"""
    
    def __init__(self, content_weight=0.4, cf_weight=0.3, position_weight=0.3):
        self.content_weight = content_weight
        self.cf_weight = cf_weight
        self.position_weight = position_weight
        
        # 子模型
        self.content_recommender = ContentBasedRecommender()
        self.club_cf = ClubBasedCF(k_neighbors=10)
        self.position_recommender = PositionBasedRecommender()
        
        # 数据
        self.players_df = None
        self.transfers_df = None
        self.is_fitted = False
        
    def fit(self, players_df, transfers_df=None):
        """训练混合推荐模型"""
        print("=" * 50)
        print("开始训练混合推荐模型")
        print("=" * 50)
        
        self.players_df = players_df
        self.transfers_df = transfers_df
        
        print("\n[1/3] 训练基于内容的推荐...")
        self.content_recommender.fit(players_df)
        
        print("\n[2/3] 构建位置特征画像...")
        self.position_recommender.fit(players_df)
        
        if transfers_df is not None and len(transfers_df) > 0:
            print("\n[3/3] 训练俱乐部协同过滤...")
            self.club_cf.fit(transfers_df, players_df)
        
        self.is_fitted = True
        print("\n" + "=" * 50)
        print("混合推荐模型训练完成!")
        print("=" * 50)
        
        return self
    
    def get_adaptive_weights(self, club_id=None):
        """根据球队需求自适应调整权重"""
        weights = {
            'content': self.content_weight,
            'cf': self.cf_weight,
            'position': self.position_weight
        }
        
        if club_id is not None and 'current_club_id' in self.players_df.columns:
            club_players = self.players_df[self.players_df['current_club_id'] == club_id]
            
            if len(club_players) > 0 and 'position_category' in club_players.columns:
                position_counts = club_players['position_category'].value_counts()
                total = len(club_players)
                
                for pos, ideal_ratio in [('Goalkeeper', 0.12), ('Defender', 0.35), 
                                          ('Midfielder', 0.30), ('Forward', 0.23)]:
                    current_ratio = position_counts.get(pos, 0) / total
                    if current_ratio < ideal_ratio * 0.7:
                        weights['position'] *= 1.3
                        weights['content'] *= 0.9
                        break
                
                total_weight = sum(weights.values())
                weights = {k: v / total_weight for k, v in weights.items()}
        
        return weights
    
    def recommend_for_club(self, club_id, n_items=10, position_filter=None, 
                           budget_range=None, age_range=None):
        """为俱乐部推荐球员"""
        if not self.is_fitted:
            raise ValueError("模型尚未训练")
        
        weights = self.get_adaptive_weights(club_id)
        
        content_recs = []
        cf_recs = []
        position_recs = []
        
        if 'current_club_id' in self.players_df.columns:
            club_players = self.players_df[self.players_df['current_club_id'] == club_id]
        else:
            club_players = pd.DataFrame()
        
        if len(club_players) > 0:
            feature_cols = ['age', 'goals', 'assists', 'minutes_played']
            available_cols = [c for c in feature_cols if c in club_players.columns]
            
            if available_cols:
                avg_features = club_players[available_cols].fillna(0).mean().values
                content_recs = self.content_recommender.recommend_for_player_profile(
                    avg_features, self.players_df, exclude_ids=club_players['player_id'].tolist(), n_items=n_items*2
                )
        
        if self.transfers_df is not None and len(self.transfers_df) > 0:
            cf_recs = self.club_cf.recommend(club_id, self.players_df, n_items=n_items*2)
        
        needs = self.content_recommender.build_team_need_profile(club_id, self.players_df)
        
        if needs and needs['position_needs']:
            most_needed_pos = max(needs['position_needs'], key=needs['position_needs'].get)
            if needs['position_needs'][most_needed_pos] > 0 and 'position_category' in self.players_df.columns:
                pos_players = self.players_df[self.players_df['position_category'] == most_needed_pos]
                exclude_ids = club_players['player_id'].tolist() if len(club_players) > 0 else []
                pos_players = pos_players[~pos_players['player_id'].isin(exclude_ids)]
                
                if 'market_value' in pos_players.columns:
                    position_recs = [(row['player_id'], row['market_value']) 
                                    for _, row in pos_players.nlargest(n_items*2, 'market_value').iterrows()]
                else:
                    position_recs = [(row['player_id'], 1.0) 
                                    for _, row in pos_players.head(n_items*2).iterrows()]
        
        # 融合推荐结果
        final_scores = defaultdict(float)
        
        if content_recs:
            max_content = max(s for _, s in content_recs) if content_recs else 1
            for player_id, score in content_recs:
                final_scores[player_id] += weights['content'] * (score / max_content)
        
        if cf_recs:
            max_cf = max(s for _, s in cf_recs) if cf_recs else 1
            for player_id, score in cf_recs:
                final_scores[player_id] += weights['cf'] * (score / max_cf)
        
        if position_recs:
            max_pos = max(s for _, s in position_recs) if position_recs else 1
            for player_id, score in position_recs:
                final_scores[player_id] += weights['position'] * (score / max_pos)
        
        recommendations = [(pid, score) for pid, score in final_scores.items()]
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = self._apply_filters(recommendations, position_filter, budget_range, age_range)
        
        return recommendations[:n_items]
    
    def recommend_similar_player(self, player_id, n_items=10, same_position=True):
        """推荐与指定球员相似的球员"""
        if not self.is_fitted:
            raise ValueError("模型尚未训练")
        
        player = self.players_df[self.players_df['player_id'] == player_id]
        if len(player) == 0:
            return []
        
        player = player.iloc[0]
        content_similar = self.content_recommender.get_similar_players(player_id, n_items * 2)
        
        if same_position and 'position_category' in self.players_df.columns:
            player_pos = player.get('position_category', '')
            same_pos_players = set(self.players_df[
                self.players_df['position_category'] == player_pos
            ]['player_id'].values)
            content_similar = [(pid, score) for pid, score in content_similar 
                             if pid in same_pos_players]
        
        return content_similar[:n_items]
    
    def _apply_filters(self, recommendations, position_filter=None, budget_range=None, age_range=None):
        """应用过滤条件"""
        filtered = []
        
        for player_id, score in recommendations:
            player = self.players_df[self.players_df['player_id'] == player_id]
            if len(player) == 0:
                continue
            player = player.iloc[0]
            
            if position_filter and 'position_category' in player.index:
                if player['position_category'] != position_filter:
                    continue
            
            if budget_range and 'market_value' in player.index:
                min_budget, max_budget = budget_range
                if pd.notna(player['market_value']):
                    if player['market_value'] < min_budget or player['market_value'] > max_budget:
                        continue
            
            if age_range and 'age' in player.index:
                min_age, max_age = age_range
                if pd.notna(player['age']):
                    if player['age'] < min_age or player['age'] > max_age:
                        continue
            
            filtered.append((player_id, score))
        
        return filtered
    
    def get_recommendation_explanation(self, player_id, club_id=None):
        """生成推荐解释"""
        player = self.players_df[self.players_df['player_id'] == player_id]
        if len(player) == 0:
            return "无法生成解释"
        player = player.iloc[0]
        
        explanations = []
        
        # 位置
        if 'position_category' in player.index:
            pos_map = {'Goalkeeper': '门将', 'Defender': '后卫', 'Midfielder': '中场', 'Forward': '前锋'}
            explanations.append(f"{pos_map.get(player['position_category'], player['position_category'])}位置")
        
        # 年龄
        if 'age' in player.index and pd.notna(player['age']):
            if player['age'] < 23:
                explanations.append("潜力新星")
            elif player['age'] < 28:
                explanations.append("当打之年")
            elif player['age'] > 32:
                explanations.append("经验丰富的老将")
        
        # 身价
        if 'market_value' in player.index and pd.notna(player['market_value']):
            if player['market_value'] > 50000000:
                explanations.append("顶级球星")
            elif player['market_value'] > 10000000:
                explanations.append("高价值球员")
        
        # 进球效率
        if 'goals_per_game' in player.index and pd.notna(player['goals_per_game']):
            if player['goals_per_game'] > 0.5:
                explanations.append("高进球效率")
        
        # 满足球队需求
        if club_id is not None:
            needs = self.content_recommender.build_team_need_profile(club_id, self.players_df)
            if needs and 'position_category' in player.index:
                pos = player['position_category']
                pos_cn = {'Goalkeeper': '门将', 'Defender': '后卫', 'Midfielder': '中场', 'Forward': '前锋'}
                if needs['position_needs'].get(pos, 0) > 0:
                    explanations.append(f"满足球队{pos_cn.get(pos, pos)}位置缺口")
        
        return "，".join(explanations) if explanations else "综合推荐"


if __name__ == '__main__':
    from data_preprocessing import DataPreprocessor
    
    preprocessor = DataPreprocessor()
    preprocessor.load_data().clean_data().feature_engineering()
    
    hybrid = HybridRecommender()
    hybrid.fit(preprocessor.players_df, preprocessor.transfers_df)
    
    if preprocessor.transfers_df is not None:
        test_club = preprocessor.transfers_df['to_club_id'].iloc[0]
        recs = hybrid.recommend_for_club(test_club, n_items=5)
        
        print(f"\n为俱乐部 {test_club} 推荐:")
        for pid, score in recs:
            player = preprocessor.players_df[preprocessor.players_df['player_id'] == pid].iloc[0]
            explanation = hybrid.get_recommendation_explanation(pid, test_club)
            print(f"  {player.get('player_name', pid)}: {score:.3f} - {explanation}")
