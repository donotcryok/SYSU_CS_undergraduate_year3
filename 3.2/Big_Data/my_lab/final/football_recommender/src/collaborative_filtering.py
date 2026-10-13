# -*- coding: utf-8 -*-
"""
协同过滤推荐算法模块
基于俱乐部引援历史的协同过滤
"""

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')


class ClubBasedCF:
    """基于俱乐部的协同过滤"""
    
    def __init__(self, k_neighbors=10):
        self.k_neighbors = k_neighbors
        self.club_player_matrix = None
        self.similarity_matrix = None
        self.club_ids = None
        self.player_ids = None
        
    def fit(self, transfers_df, players_df):
        """训练模型"""
        print("正在训练俱乐部协同过滤模型...")
        
        # 只使用最近的转会记录，限制俱乐部数量
        club_counts = transfers_df['to_club_id'].value_counts()
        top_clubs = club_counts.head(500).index.tolist()
        
        player_counts = transfers_df['player_id'].value_counts()
        top_players = player_counts.head(2000).index.tolist()
        
        filtered_transfers = transfers_df[
            (transfers_df['to_club_id'].isin(top_clubs)) & 
            (transfers_df['player_id'].isin(top_players))
        ]
        
        self.club_player_matrix = filtered_transfers.pivot_table(
            index='to_club_id',
            columns='player_id',
            values='transfer_fee',
            aggfunc='sum',
            fill_value=0
        )
        
        self.club_ids = self.club_player_matrix.index.tolist()
        self.player_ids = self.club_player_matrix.columns.tolist()
        
        sparse_matrix = csr_matrix(self.club_player_matrix.values)
        
        n_clubs = min(100, len(self.club_ids))
        self.similarity_matrix = cosine_similarity(sparse_matrix[:n_clubs])
        np.fill_diagonal(self.similarity_matrix, 0)
        
        self.club_ids = self.club_ids[:n_clubs]
        
        print(f"模型训练完成! 俱乐部数量: {len(self.club_ids)}")
        return self
    
    def get_similar_clubs(self, club_id, k=5):
        """获取相似俱乐部"""
        if club_id not in self.club_ids:
            return []
        
        idx = self.club_ids.index(club_id)
        if idx >= len(self.similarity_matrix):
            return []
            
        similarities = self.similarity_matrix[idx]
        top_k_idx = np.argsort(similarities)[-k:][::-1]
        
        return [(self.club_ids[i], similarities[i]) for i in top_k_idx if i < len(self.club_ids)]
    
    def recommend(self, club_id, players_df, n_items=10, exclude_current=True):
        """为俱乐部推荐球员"""
        if club_id not in self.club_ids:
            return self._recommend_by_popularity(players_df, n_items)
        
        similar_clubs = self.get_similar_clubs(club_id, self.k_neighbors)
        
        if not similar_clubs:
            return self._recommend_by_popularity(players_df, n_items)
        
        candidate_players = defaultdict(float)
        
        for sim_club_id, similarity in similar_clubs:
            if sim_club_id in self.club_ids:
                idx = self.club_ids.index(sim_club_id)
                if idx < len(self.club_player_matrix):
                    club_vector = self.club_player_matrix.values[idx]
                    
                    for i, player_id in enumerate(self.player_ids):
                        if i < len(club_vector) and club_vector[i] > 0:
                            candidate_players[player_id] += similarity * club_vector[i]
        
        if exclude_current and 'current_club_id' in players_df.columns:
            current_players = set(players_df[players_df['current_club_id'] == club_id]['player_id'].values)
            candidate_players = {pid: score for pid, score in candidate_players.items() 
                               if pid not in current_players}
        
        recommendations = sorted(candidate_players.items(), key=lambda x: x[1], reverse=True)[:n_items]
        
        if not recommendations:
            return self._recommend_by_popularity(players_df, n_items)
        
        return recommendations
    
    def _recommend_by_popularity(self, players_df, n_items):
        """基于流行度的推荐（冷启动）"""
        if 'market_value' in players_df.columns:
            popular = players_df.nlargest(n_items, 'market_value')
            return [(row['player_id'], row['market_value']) for _, row in popular.iterrows()]
        else:
            popular = players_df.head(n_items)
            return [(row['player_id'], 1.0) for _, row in popular.iterrows()]


class PlayerSimilarityCF:
    """基于球员相似度的协同过滤"""
    
    def __init__(self):
        self.similarity_matrix = None
        self.player_ids = None
        
    def fit(self, players_df, max_players=5000):
        """训练模型"""
        print("正在训练球员相似度模型...")
        
        if len(players_df) > max_players:
            if 'market_value' in players_df.columns:
                players_subset = players_df.nlargest(max_players, 'market_value')
            else:
                players_subset = players_df.head(max_players)
        else:
            players_subset = players_df
        
        feature_cols = ['age', 'goals', 'assists', 'yellow_cards', 'red_cards', 
                       'minutes_played', 'games_played', 'goals_per_game', 'assists_per_game']
        available_cols = [c for c in feature_cols if c in players_subset.columns]
        
        if not available_cols:
            available_cols = ['age']
        
        self.player_ids = players_subset['player_id'].tolist()
        
        features = players_subset[available_cols].fillna(0).values
        
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        self.similarity_matrix = cosine_similarity(features_scaled)
        np.fill_diagonal(self.similarity_matrix, 0)
        
        print(f"球员相似度模型训练完成! 球员数量: {len(self.player_ids)}")
        return self
    
    def get_similar_players(self, player_id, k=10):
        """获取相似球员"""
        if player_id not in self.player_ids:
            return []
        
        idx = self.player_ids.index(player_id)
        similarities = self.similarity_matrix[idx]
        top_k_idx = np.argsort(similarities)[-k:][::-1]
        
        return [(self.player_ids[i], similarities[i]) for i in top_k_idx]
    
    def recommend_similar(self, player_id, players_df, n_items=10):
        """推荐与指定球员相似的球员"""
        similar_players = self.get_similar_players(player_id, n_items + 1)
        similar_players = [(pid, score) for pid, score in similar_players if pid != player_id]
        return similar_players[:n_items]


if __name__ == '__main__':
    from data_preprocessing import DataPreprocessor
    
    preprocessor = DataPreprocessor()
    preprocessor.load_data().clean_data().feature_engineering()
    
    cf = ClubBasedCF()
    if preprocessor.transfers_df is not None:
        cf.fit(preprocessor.transfers_df, preprocessor.players_df)
        
        if cf.club_ids:
            test_club = cf.club_ids[0]
            similar = cf.get_similar_clubs(test_club)
            print(f"\n与俱乐部 {test_club} 相似的俱乐部:")
            for club_id, score in similar:
                print(f"  {club_id}: {score:.4f}")
