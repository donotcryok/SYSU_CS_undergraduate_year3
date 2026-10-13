# -*- coding: utf-8 -*-
"""
可视化模块
数据探索性分析和结果可视化
"""

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import os
import sys

plt.rcParams['axes.unicode_minus'] = False
sns.set_style("whitegrid")
sns.set_palette("husl")


class Visualizer:
    """可视化类"""
    
    def __init__(self, output_dir='output'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def plot_player_distribution(self, players_df, save=True):
        """绘制球员分布图"""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        if 'age' in players_df.columns:
            age_data = players_df['age'].dropna()
            axes[0, 0].hist(age_data, bins=20, color='steelblue', alpha=0.8)
            axes[0, 0].set_xlabel('Age', fontsize=12)
            axes[0, 0].set_ylabel('Count', fontsize=12)
            axes[0, 0].set_title('Player Age Distribution', fontsize=14)
            axes[0, 0].axvline(age_data.mean(), color='red', linestyle='--', label=f'Mean: {age_data.mean():.1f}')
            axes[0, 0].legend()
        
        if 'position_category' in players_df.columns:
            pos_counts = players_df['position_category'].value_counts()
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
            axes[0, 1].bar(pos_counts.index, pos_counts.values, color=colors[:len(pos_counts)])
            axes[0, 1].set_xlabel('Position', fontsize=12)
            axes[0, 1].set_ylabel('Count', fontsize=12)
            axes[0, 1].set_title('Player Position Distribution', fontsize=14)
            axes[0, 1].tick_params(axis='x', rotation=45)
        
        if 'market_value' in players_df.columns:
            market_values = players_df['market_value'].dropna() / 1000000
            market_values = market_values[market_values > 0]
            if len(market_values) > 0:
                axes[1, 0].hist(market_values[market_values < market_values.quantile(0.95)], 
                               bins=30, color='orange', alpha=0.8)
                axes[1, 0].set_xlabel('Market Value (Million)', fontsize=12)
                axes[1, 0].set_ylabel('Count', fontsize=12)
                axes[1, 0].set_title('Player Market Value Distribution', fontsize=14)
        
        if 'citizenship' in players_df.columns:
            country_counts = players_df['citizenship'].value_counts().head(10)
            axes[1, 1].barh(country_counts.index, country_counts.values, color='green', alpha=0.7)
            axes[1, 1].set_xlabel('Count', fontsize=12)
            axes[1, 1].set_title('Player Citizenship Distribution (Top 10)', fontsize=14)
        
        plt.suptitle('Football Player Data Distribution', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save:
            plt.savefig(os.path.join(self.output_dir, 'player_distribution.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
    def plot_skill_radar(self, player_data, player_name="Player", save=True):
        """绘制球员技能雷达图"""
        skills = ['goals_per_game', 'assists_per_game', 'minutes_played', 'games_played']
        available_skills = [s for s in skills if s in player_data.index and pd.notna(player_data[s])]
        
        if not available_skills:
            print("No sufficient data for radar chart")
            return
        
        values = [float(player_data.get(s, 0)) for s in available_skills]
        
        max_vals = {'goals_per_game': 1.0, 'assists_per_game': 1.0, 'minutes_played': 3000, 'games_played': 50}
        normalized_values = []
        for i, v in enumerate(values):
            max_val = max_vals.get(available_skills[i], 1)
            normalized_values.append(min(100, v / max_val * 100))
        
        angles = np.linspace(0, 2 * np.pi, len(available_skills), endpoint=False).tolist()
        normalized_values += normalized_values[:1]
        angles += angles[:1]
        
        label_map = {
            'goals_per_game': 'Goals/Game',
            'assists_per_game': 'Assists/Game',
            'minutes_played': 'Minutes',
            'games_played': 'Games'
        }
        
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        ax.fill(angles, normalized_values, color='steelblue', alpha=0.25)
        ax.plot(angles, normalized_values, color='steelblue', linewidth=2)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([label_map.get(s, s) for s in available_skills], fontsize=12)
        ax.set_ylim(0, 100)
        
        name = player_data.get('player_name', player_name) if 'player_name' in player_data.index else player_name
        ax.set_title(f'{name} Skill Radar', fontsize=14, fontweight='bold', pad=20)
        
        if save:
            plt.savefig(os.path.join(self.output_dir, f'{player_name}_radar.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
    def plot_age_vs_value(self, players_df, save=True):
        """绘制年龄与身价关系图"""
        if 'age' not in players_df.columns or 'market_value' not in players_df.columns:
            print("Missing age or market value data")
            return
        
        plot_df = players_df[['age', 'market_value']].dropna()
        plot_df = plot_df[plot_df['market_value'] > 0]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        scatter = ax.scatter(plot_df['age'], 
                           plot_df['market_value'] / 1000000,
                           alpha=0.6,
                           s=50,
                           c='steelblue')
        
        ax.set_xlabel('Age', fontsize=12)
        ax.set_ylabel('Market Value (Million)', fontsize=12)
        ax.set_title('Player Age vs Market Value', fontsize=14)
        
        if save:
            plt.savefig(os.path.join(self.output_dir, 'age_vs_value.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
    def plot_position_distribution(self, players_df, save=True):
        """绘制位置详细分布"""
        if 'main_position' not in players_df.columns:
            return
            
        fig, ax = plt.subplots(figsize=(12, 6))
        
        position_counts = players_df['main_position'].value_counts().head(15)
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(position_counts)))
        ax.barh(range(len(position_counts)), position_counts.values, color=colors)
        ax.set_yticks(range(len(position_counts)))
        ax.set_yticklabels(position_counts.index, fontsize=10)
        
        ax.set_xlabel('Count', fontsize=12)
        ax.set_title('Player Position Distribution (Top 15)', fontsize=14)
        ax.invert_yaxis()
        
        plt.tight_layout()
        if save:
            plt.savefig(os.path.join(self.output_dir, 'position_distribution.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
    def plot_evaluation_results(self, comparison_df, save=True):
        """绘制评估结果对比图"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        precision_cols = [c for c in comparison_df.columns if 'Precision' in c]
        if precision_cols:
            x = np.arange(len(comparison_df))
            width = 0.8 / len(precision_cols)
            for i, col in enumerate(precision_cols):
                axes[0].bar(x + i * width, comparison_df[col], width, label=col)
            axes[0].set_xticks(x + width * len(precision_cols) / 2)
            axes[0].set_xticklabels(comparison_df['Model'], rotation=15)
            axes[0].set_ylabel('Precision', fontsize=12)
            axes[0].set_title('Precision Comparison', fontsize=13)
            axes[0].legend()
        
        ndcg_cols = [c for c in comparison_df.columns if 'NDCG' in c]
        if ndcg_cols:
            for i, col in enumerate(ndcg_cols):
                axes[1].bar(x + i * width, comparison_df[col], width, label=col)
            axes[1].set_xticks(x + width * len(ndcg_cols) / 2)
            axes[1].set_xticklabels(comparison_df['Model'], rotation=15)
            axes[1].set_ylabel('NDCG', fontsize=12)
            axes[1].set_title('NDCG Comparison', fontsize=13)
            axes[1].legend()
        
        plt.suptitle('Recommendation Algorithm Performance Comparison', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save:
            plt.savefig(os.path.join(self.output_dir, 'evaluation_comparison.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
    def plot_recommendation_summary(self, recommendations, players_df, club_id=None, save=True):
        """绘制推荐结果摘要"""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        rec_players = []
        for player_id, score in recommendations:
            player = players_df[players_df['player_id'] == player_id]
            if len(player) > 0:
                rec_players.append(player.iloc[0])
        
        if not rec_players:
            return
            
        rec_df = pd.DataFrame(rec_players)
        
        if 'market_value' in rec_df.columns:
            market_values = rec_df['market_value'].dropna() / 1000000
            names = []
            for idx in market_values.index:
                name = rec_df.loc[idx, 'player_name'] if 'player_name' in rec_df.columns else f'P{idx}'
                name = str(name)[:20]
                names.append(name)
            
            axes[0].barh(range(len(market_values)), market_values.values, color='steelblue')
            axes[0].set_yticks(range(len(names)))
            axes[0].set_yticklabels(names, fontsize=9)
            axes[0].set_xlabel('Market Value (Million)', fontsize=12)
            axes[0].set_title('Recommended Players Market Value', fontsize=14)
        
        if 'position_category' in rec_df.columns:
            pos_counts = rec_df['position_category'].value_counts()
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
            axes[1].pie(pos_counts, labels=pos_counts.index, autopct='%1.1f%%', 
                       colors=colors[:len(pos_counts)], startangle=90)
            axes[1].set_title('Recommended Players Position Distribution', fontsize=14)
        
        title = f'Club {club_id} Recommendations' if club_id else 'Recommendation Summary'
        plt.suptitle(title, fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save:
            plt.savefig(os.path.join(self.output_dir, 'recommendation_summary.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
    def plot_top_players(self, players_df, n=20, save=True):
        """绘制身价最高的球员"""
        if 'market_value' not in players_df.columns or 'player_name' not in players_df.columns:
            return
            
        fig, ax = plt.subplots(figsize=(12, 8))
        
        top_players = players_df.nlargest(n, 'market_value')
        names = [str(name)[:20] for name in top_players['player_name']]
        values = top_players['market_value'] / 1000000
        
        colors = plt.cm.RdYlGn(np.linspace(0.3, 0.9, n))
        bars = ax.barh(range(n), values.values, color=colors)
        ax.set_yticks(range(n))
        ax.set_yticklabels(names, fontsize=10)
        ax.set_xlabel('Market Value (Million)', fontsize=12)
        ax.set_title(f'Top {n} Players by Market Value', fontsize=14)
        ax.invert_yaxis()
        
        for i, (bar, val) in enumerate(zip(bars, values.values)):
            ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                   f'{val:.1f}M', ha='left', va='center', fontsize=9)
        
        plt.tight_layout()
        if save:
            plt.savefig(os.path.join(self.output_dir, 'top_players.png'), dpi=150, bbox_inches='tight')
        plt.close()
        
    def create_eda_report(self, players_df):
        """创建完整的探索性分析报告"""
        print("正在生成数据探索性分析报告...")
        self.plot_player_distribution(players_df)
        self.plot_position_distribution(players_df)
        self.plot_top_players(players_df)
        if 'market_value' in players_df.columns:
            self.plot_age_vs_value(players_df)
        print(f"可视化结果已保存到 {self.output_dir}/")


if __name__ == '__main__':
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from data_preprocessing import DataPreprocessor
    
    preprocessor = DataPreprocessor()
    preprocessor.load_data().clean_data().feature_engineering()
    
    visualizer = Visualizer()
    visualizer.create_eda_report(preprocessor.players_df)
