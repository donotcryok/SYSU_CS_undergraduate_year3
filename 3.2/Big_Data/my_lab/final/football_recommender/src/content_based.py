# -*- coding: utf-8 -*-
"""
基于内容的推荐算法模块
基于球员特征的相似度推荐
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class ContentBasedRecommender:
    """基于内容的球员推荐"""
    
    def __init__(self):
        self.player_features = None
        self.player_ids = None
        self.feature_matrix = None
        self.similarity_matrix = None
        self.scaler = StandardScaler()
        
    def fit(self, players_df):
        """训练模型"""
        print("正在训练基于内容的推荐模型...")
        
        self.player_ids = players_df['player_id'].tolist()
        
        perf_cols = ['age', 'goals', 'assists', 'yellow_cards', 'red_cards', 
                    'minutes_played', 'games_played', 'goals_per_game', 'assists_per_game']
        
        if 'height' in players_df.columns:
            perf_cols.append('height')
        
        available_cols = [c for c in perf_cols if c in players_df.columns]
        
        if not available_cols:
            available_cols = ['age']
        
        features = players_df[available_cols].fillna(0).values
        self.feature_matrix = self.scaler.fit_transform(features)
        
        self.similarity_matrix = cosine_similarity(self.feature_matrix)
        np.fill_diagonal(self.similarity_matrix, 0)
        
        print(f"基于内容的推荐模型训练完成! 特征维度: {self.feature_matrix.shape[1]}")
        return self
    
    def get_similar_players(self, player_id, k=10):
        """获取相似球员"""
        if player_id not in self.player_ids:
            return []
        
        idx = self.player_ids.index(player_id)
        similarities = self.similarity_matrix[idx]
        top_k_idx = np.argsort(similarities)[-k:][::-1]
        
        return [(self.player_ids[i], similarities[i]) for i in top_k_idx]
    
    def recommend_for_player_profile(self, target_features, players_df, 
                                      position=None, exclude_ids=None, n_items=10):
        """基于目标特征推荐球员"""
        if len(target_features) < self.feature_matrix.shape[1]:
            padded = np.zeros(self.feature_matrix.shape[1])
            padded[:len(target_features)] = target_features
            target_features = padded
        elif len(target_features) > self.feature_matrix.shape[1]:
            target_features = target_features[:self.feature_matrix.shape[1]]
        
        target_scaled = self.scaler.transform(target_features.reshape(1, -1))
        similarities = cosine_similarity(target_scaled, self.feature_matrix)[0]
        
        results = pd.DataFrame({
            'player_id': self.player_ids,
            'similarity': similarities
        })
        
        if exclude_ids:
            results = results[~results['player_id'].isin(exclude_ids)]
        
        if position and 'position_category' in players_df.columns:
            position_players = players_df[players_df['position_category'] == position]['player_id'].values
            results = results[results['player_id'].isin(position_players)]
        
        results = results.nlargest(n_items, 'similarity')
        return list(zip(results['player_id'], results['similarity']))
    
    def build_team_need_profile(self, club_id, players_df):
        """构建球队需求画像，分析阵容缺口"""
        if 'current_club_id' not in players_df.columns:
            return None
            
        club_players = players_df[players_df['current_club_id'] == club_id]
        
        if len(club_players) == 0:
            return None
        
        ideal_counts = {'Goalkeeper': 3, 'Defender': 8, 'Midfielder': 7, 'Forward': 5}
        
        needs = {
            'club_id': club_id,
            'club_name': str(club_players.iloc[0].get('current_club_name', f'俱乐部 {club_id}')),
            'total_players': len(club_players),
            'position_analysis': {},
            'position_needs': {},
            'age_analysis': {},
            'player_list': []
        }
        
        # 位置需求分析
        if 'position_category' in club_players.columns:
            position_counts = club_players['position_category'].value_counts()
            
            for pos, ideal in ideal_counts.items():
                current = int(position_counts.get(pos, 0))
                gap = ideal - current
                
                needs['position_analysis'][pos] = {
                    'current': current,
                    'ideal': ideal,
                    'gap': max(0, gap),
                    'status': 'sufficient' if gap <= 0 else ('urgent' if gap >= 3 else 'needed')
                }
                
                if gap > 0:
                    needs['position_needs'][pos] = gap
        
        # 年龄结构分析
        if 'age' in club_players.columns:
            age_data = club_players['age'].dropna()
            avg_age = age_data.mean()
            young_count = len(age_data[age_data < 24])
            prime_count = len(age_data[(age_data >= 24) & (age_data <= 30)])
            veteran_count = len(age_data[age_data > 30])
            
            young_ratio = young_count / len(age_data) if len(age_data) > 0 else 0
            
            needs['age_analysis'] = {
                'average_age': round(avg_age, 1),
                'young_count': young_count,
                'prime_count': prime_count,
                'veteran_count': veteran_count,
                'young_ratio': round(young_ratio * 100, 1),
                'needs_young': young_ratio < 0.3 or avg_age > 29
            }
        
        # 当前球员列表
        for _, player in club_players.iterrows():
            player_info = {
                'player_id': int(player['player_id']),
                'name': str(player.get('player_name', f"球员 {player['player_id']}")),
                'position': str(player.get('position_category', '-')),
                'age': int(player.get('age', 0)) if pd.notna(player.get('age')) else 0,
                'market_value': float(player.get('market_value', 0)) if pd.notna(player.get('market_value')) else 0
            }
            needs['player_list'].append(player_info)
        
        position_order = {'Goalkeeper': 0, 'Defender': 1, 'Midfielder': 2, 'Forward': 3}
        needs['player_list'].sort(key=lambda x: position_order.get(x['position'], 99))
        
        return needs


class PositionBasedRecommender:
    """基于位置的专业推荐器"""
    
    def __init__(self):
        self.position_profiles = {}
        
    def fit(self, players_df):
        """构建各位置的理想特征画像"""
        print("正在构建位置特征画像...")
        
        feature_cols = ['age', 'goals_per_game', 'assists_per_game', 'minutes_played']
        available_cols = [c for c in feature_cols if c in players_df.columns]
        
        if not available_cols or 'position_category' not in players_df.columns:
            return self
        
        for position in players_df['position_category'].unique():
            if position == 'Unknown':
                continue
                
            pos_players = players_df[players_df['position_category'] == position]
            
            if 'market_value' in pos_players.columns:
                top_players = pos_players.nlargest(int(len(pos_players) * 0.25), 'market_value')
            else:
                top_players = pos_players.head(int(len(pos_players) * 0.25))
            
            if len(top_players) > 0:
                self.position_profiles[position] = {
                    'feature_means': top_players[available_cols].mean().to_dict(),
                    'count': len(pos_players)
                }
        
        return self
    
    def get_position_score(self, player, position):
        """计算球员与位置的匹配度"""
        if position not in self.position_profiles:
            return 0.5
        
        profile = self.position_profiles[position]
        score = 0
        count = 0
        
        for feature, target_mean in profile['feature_means'].items():
            if feature in player.index:
                diff = abs(player[feature] - target_mean)
                max_val = max(abs(target_mean), 1)
                feature_score = max(0, 1 - diff / max_val)
                score += feature_score
                count += 1
        
        return score / count if count > 0 else 0.5


if __name__ == '__main__':
    from data_preprocessing import DataPreprocessor
    
    preprocessor = DataPreprocessor()
    preprocessor.load_data().clean_data().feature_engineering()
    
    cb = ContentBasedRecommender()
    cb.fit(preprocessor.players_df)
    
    test_club = preprocessor.players_df['current_club_id'].iloc[0]
    needs = cb.build_team_need_profile(test_club, preprocessor.players_df)
    print(f"\n俱乐部 {test_club} 的球队需求分析:")
    print(needs)
