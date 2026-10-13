# -*- coding: utf-8 -*-
"""
数据预处理模块
负责加载真实Transfermarkt数据集、清洗和特征工程
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from datetime import datetime
import os
import warnings
warnings.filterwarnings('ignore')


class DataPreprocessor:
    """足球数据预处理类"""
    
    def __init__(self, data_path='data'):
        self.data_path = data_path
        
        # 原始数据
        self.player_profiles = None
        self.player_performances = None
        self.transfer_history = None
        self.player_market_value = None
        self.player_latest_market_value = None
        self.team_details = None
        self.player_injuries = None
        
        # 处理后的数据
        self.players_df = None
        self.transfers_df = None
        self.appearances_df = None
        self.clubs_df = None
        
    def load_data(self):
        """加载真实数据集"""
        print("正在加载Transfermarkt数据集...")
        
        # 1. 加载球员个人资料（核心表）
        profiles_path = os.path.join(self.data_path, 'player_profiles', 'player_profiles.csv')
        if os.path.exists(profiles_path):
            self.player_profiles = pd.read_csv(profiles_path)
            print(f"  - 球员资料: {len(self.player_profiles)} 条")
        
        # 2. 加载球员表现数据
        perf_path = os.path.join(self.data_path, 'player_performances', 'player_performances.csv')
        if os.path.exists(perf_path):
            self.player_performances = pd.read_csv(perf_path)
            print(f"  - 球员表现: {len(self.player_performances)} 条")
        
        # 3. 加载转会历史
        transfer_path = os.path.join(self.data_path, 'transfer_history', 'transfer_history.csv')
        if os.path.exists(transfer_path):
            self.transfer_history = pd.read_csv(transfer_path)
            print(f"  - 转会历史: {len(self.transfer_history)} 条")
        
        # 4. 加载最新身价
        latest_value_path = os.path.join(self.data_path, 'player_latest_market_value', 'player_latest_market_value.csv')
        if os.path.exists(latest_value_path):
            self.player_latest_market_value = pd.read_csv(latest_value_path)
            print(f"  - 最新身价: {len(self.player_latest_market_value)} 条")
        
        # 5. 加载历史身价
        value_path = os.path.join(self.data_path, 'player_market_value', 'player_market_value.csv')
        if os.path.exists(value_path):
            self.player_market_value = pd.read_csv(value_path)
            print(f"  - 历史身价: {len(self.player_market_value)} 条")
        
        # 6. 加载球队详情
        team_path = os.path.join(self.data_path, 'team_details', 'team_details.csv')
        if os.path.exists(team_path):
            self.team_details = pd.read_csv(team_path)
            print(f"  - 球队详情: {len(self.team_details)} 条")
        
        # 7. 加载伤病数据
        injury_path = os.path.join(self.data_path, 'player_injuries', 'player_injuries.csv')
        if os.path.exists(injury_path):
            self.player_injuries = pd.read_csv(injury_path)
            print(f"  - 伤病记录: {len(self.player_injuries)} 条")
        
        return self
    
    def clean_data(self):
        """数据清洗"""
        print("\n开始数据清洗...")
        
        if self.player_profiles is not None:
            before = len(self.player_profiles)
            self.player_profiles = self.player_profiles.dropna(subset=['player_id', 'main_position'])
            self.player_profiles = self.player_profiles.drop_duplicates(subset=['player_id'])
            
            if 'date_of_birth' in self.player_profiles.columns:
                self.player_profiles['date_of_birth'] = pd.to_datetime(self.player_profiles['date_of_birth'], errors='coerce')
                current_year = datetime.now().year
                self.player_profiles['age'] = current_year - self.player_profiles['date_of_birth'].dt.year
                self.player_profiles = self.player_profiles[
                    (self.player_profiles['age'] >= 15) & (self.player_profiles['age'] <= 45)
                ]
            
            if 'height' in self.player_profiles.columns:
                self.player_profiles['height'] = pd.to_numeric(self.player_profiles['height'], errors='coerce')
                self.player_profiles = self.player_profiles[
                    (self.player_profiles['height'] >= 150) | (self.player_profiles['height'].isna())
                ]
            
            print(f"  球员资料清洗: {before} -> {len(self.player_profiles)}")
        
        if self.transfer_history is not None:
            before = len(self.transfer_history)
            self.transfer_history = self.transfer_history.dropna(subset=['player_id', 'to_team_id'])
            self.transfer_history = self.transfer_history[self.transfer_history['transfer_fee'] >= 0]
            print(f"  转会数据清洗: {before} -> {len(self.transfer_history)}")
        
        if self.player_performances is not None:
            before = len(self.player_performances)
            self.player_performances = self.player_performances.dropna(subset=['player_id'])
            print(f"  表现数据清洗: {before} -> {len(self.player_performances)}")
        
        print("数据清洗完成!")
        return self
    
    def feature_engineering(self):
        """特征工程"""
        print("\n开始特征工程...")
        
        # 1. 构建球员主表
        self.players_df = self.player_profiles[['player_id', 'player_name', 'date_of_birth', 'age', 
                                                 'height', 'citizenship', 'main_position', 'position',
                                                 'foot', 'current_club_id', 'current_club_name']].copy()
        
        # 2. 合并最新身价
        if self.player_latest_market_value is not None:
            latest_value = self.player_latest_market_value.groupby('player_id')['value'].last().reset_index()
            latest_value.columns = ['player_id', 'market_value']
            self.players_df = self.players_df.merge(latest_value, on='player_id', how='left')
        
        # 3. 计算球员表现统计
        if self.player_performances is not None:
            perf_stats = self.player_performances.groupby('player_id').agg({
                'goals': 'sum',
                'assists': 'sum',
                'yellow_cards': 'sum',
                'direct_red_cards': 'sum',
                'minutes_played': 'sum',
                'nb_on_pitch': 'sum'
            }).reset_index()
            
            perf_stats['minutes_played'] = pd.to_numeric(perf_stats['minutes_played'], errors='coerce').fillna(0)
            perf_stats['games_played'] = perf_stats['nb_on_pitch'].clip(lower=1)
            perf_stats['goals_per_game'] = perf_stats['goals'] / perf_stats['games_played']
            perf_stats['assists_per_game'] = perf_stats['assists'] / perf_stats['games_played']
            
            self.players_df = self.players_df.merge(perf_stats, on='player_id', how='left')
        
        # 4. 位置分类
        def classify_position(pos):
            if pd.isna(pos):
                return 'Unknown'
            pos = str(pos).upper()
            if 'GOALKEEPER' in pos or 'GK' in pos:
                return 'Goalkeeper'
            elif any(x in pos for x in ['CENTRE-BACK', 'LEFT-BACK', 'RIGHT-BACK', 'DEFENDER']):
                return 'Defender'
            elif any(x in pos for x in ['MIDFIELD', 'WINGER']):
                return 'Midfielder'
            elif any(x in pos for x in ['FORWARD', 'STRIKER', 'ATTACK']):
                return 'Forward'
            else:
                return 'Other'
        
        self.players_df['position_category'] = self.players_df['main_position'].apply(classify_position)
        
        # 5. 位置简写
        def get_position_short(pos):
            if pd.isna(pos):
                return 'UNK'
            pos = str(pos).upper()
            if 'GOALKEEPER' in pos:
                return 'GK'
            elif 'CENTRE-BACK' in pos:
                return 'CB'
            elif 'LEFT-BACK' in pos:
                return 'LB'
            elif 'RIGHT-BACK' in pos:
                return 'RB'
            elif 'DEFENSIVE MIDFIELD' in pos:
                return 'CDM'
            elif 'CENTRAL MIDFIELD' in pos:
                return 'CM'
            elif 'ATTACKING MIDFIELD' in pos:
                return 'CAM'
            elif 'LEFT WINGER' in pos:
                return 'LW'
            elif 'RIGHT WINGER' in pos:
                return 'RW'
            elif 'CENTRE-FORWARD' in pos or 'SECOND STRIKER' in pos:
                return 'CF'
            else:
                return 'MF'
        
        self.players_df['position_short'] = self.players_df['main_position'].apply(get_position_short)
        
        # 6. 年龄分组
        self.players_df['age_group'] = pd.cut(self.players_df['age'], 
                                               bins=[0, 21, 25, 29, 33, 100],
                                               labels=['Young', 'Prime Early', 'Prime', 'Prime Late', 'Veteran'])
        
        # 7. 构建转会数据表
        if self.transfer_history is not None:
            self.transfers_df = self.transfer_history[[
                'player_id', 'season_name', 'transfer_date', 
                'from_team_id', 'from_team_name', 'to_team_id', 'to_team_name',
                'transfer_type', 'transfer_fee', 'value_at_transfer'
            ]].copy()
            
            self.transfers_df.columns = [
                'player_id', 'season', 'transfer_date',
                'from_club_id', 'from_club_name', 'to_club_id', 'to_club_name',
                'transfer_type', 'transfer_fee', 'value_at_transfer'
            ]
        
        # 8. 构建俱乐部数据表
        if self.team_details is not None:
            self.clubs_df = self.team_details[['club_id', 'club_name', 'country_name', 'competition_name']].copy()
            self.clubs_df = self.clubs_df.drop_duplicates(subset=['club_id'])
        
        # 9. 填充缺失值
        numeric_cols = self.players_df.select_dtypes(include=[np.number]).columns
        self.players_df[numeric_cols] = self.players_df[numeric_cols].fillna(0)
        
        # 10. 为协同过滤准备出场数据
        if self.player_performances is not None:
            self.appearances_df = self.player_performances[[
                'player_id', 'team_id', 'season_name', 'goals', 'assists', 
                'yellow_cards', 'direct_red_cards', 'minutes_played', 'nb_on_pitch'
            ]].copy()
            self.appearances_df.columns = [
                'player_id', 'team_id', 'season', 'goals', 'assists',
                'yellow_cards', 'red_cards', 'minutes_played', 'appearances'
            ]
        
        print("特征工程完成!")
        return self
    
    def get_statistics(self):
        """获取数据统计信息"""
        stats = {
            'n_players': len(self.players_df) if self.players_df is not None else 0,
            'n_clubs': len(self.clubs_df) if self.clubs_df is not None else 0,
            'n_transfers': len(self.transfers_df) if self.transfers_df is not None else 0,
        }
        
        if self.players_df is not None:
            stats['avg_age'] = self.players_df['age'].mean()
            stats['position_distribution'] = self.players_df['position_category'].value_counts().to_dict()
            
            if 'market_value' in self.players_df.columns:
                stats['avg_market_value'] = self.players_df['market_value'].mean()
        
        return stats
    
    def get_top_players(self, n=20, by='market_value'):
        """获取身价最高的球员"""
        if self.players_df is None:
            return pd.DataFrame()
        
        if by in self.players_df.columns:
            return self.players_df.nlargest(n, by)[['player_id', 'player_name', 'age', 
                                                     'main_position', 'current_club_name', by]]
        return self.players_df.head(n)


if __name__ == '__main__':
    preprocessor = DataPreprocessor()
    preprocessor.load_data().clean_data().feature_engineering()
    
    stats = preprocessor.get_statistics()
    print("\n数据统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    print("\n身价最高的10位球员:")
    top_players = preprocessor.get_top_players(10)
    print(top_players.to_string(index=False))
