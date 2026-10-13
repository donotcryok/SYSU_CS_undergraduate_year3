# -*- coding: utf-8 -*-
"""
数据加载与预处理模块
负责加载MovieLens数据集并进行预处理
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split


class DataLoader:
    """MovieLens数据加载器"""
    
    def __init__(self, data_dir='../data/'):
        """
        初始化数据加载器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = data_dir
        self.movies = None
        self.ratings = None
        self.tags = None
        self.train_data = None
        self.test_data = None
        
    def load_data(self):
        """
        加载所有数据文件
        
        Returns:
            bool: 加载是否成功
        """
        try:
            print("正在加载数据...")
            
            # 加载电影数据
            self.movies = pd.read_csv(f'{self.data_dir}movies.csv')
            print(f"电影数据: {len(self.movies)} 条记录")
            
            # 加载评分数据
            self.ratings = pd.read_csv(f'{self.data_dir}ratings.csv')
            print(f"评分数据: {len(self.ratings)} 条记录")
            
            # 加载标签数据
            self.tags = pd.read_csv(f'{self.data_dir}tags.csv')
            print(f"标签数据: {len(self.tags)} 条记录")
            
            # 数据预处理
            self._preprocess()
            
            print("数据加载完成!")
            return True
            
        except FileNotFoundError as e:
            print(f"错误: 找不到数据文件 - {e}")
            return False
        except Exception as e:
            print(f"错误: 数据加载失败 - {e}")
            return False
    
    def _preprocess(self):
        """数据预处理"""
        # 提取电影年份
        self.movies['year'] = self.movies['title'].str.extract(r'\((\d{4})\)', expand=False)
        
        # 将genres转换为列表
        self.movies['genres_list'] = self.movies['genres'].str.split('|')
        
        # 创建电影ID到标题的映射
        self.movie_id_to_title = dict(zip(self.movies['movieId'], self.movies['title']))
        self.movie_id_to_genres = dict(zip(self.movies['movieId'], self.movies['genres_list']))
        
    def split_data(self, test_size=0.2, random_state=42):
        """
        划分训练集和测试集
        
        Args:
            test_size: 测试集比例
            random_state: 随机种子
        """
        print(f"划分数据集 (测试集比例: {test_size})...")
        
        # 按用户划分，确保每个用户都有训练和测试数据
        self.train_data = []
        self.test_data = []
        
        for user_id in self.ratings['userId'].unique():
            user_ratings = self.ratings[self.ratings['userId'] == user_id]
            
            # 如果用户评分太少，全部放入训练集
            if len(user_ratings) < 5:
                self.train_data.append(user_ratings)
            else:
                user_train, user_test = train_test_split(
                    user_ratings, 
                    test_size=test_size, 
                    random_state=random_state
                )
                self.train_data.append(user_train)
                self.test_data.append(user_test)
        
        self.train_data = pd.concat(self.train_data, ignore_index=True)
        self.test_data = pd.concat(self.test_data, ignore_index=True)
        
        print(f"训练集: {len(self.train_data)} 条记录")
        print(f"测试集: {len(self.test_data)} 条记录")
        
    def get_user_movie_matrix(self, data=None):
        """
        构建用户-电影评分矩阵
        
        Args:
            data: 使用的数据，默认为训练集
            
        Returns:
            DataFrame: 用户-电影评分矩阵
        """
        if data is None:
            data = self.train_data
            
        # 创建透视表
        matrix = data.pivot_table(
            index='userId', 
            columns='movieId', 
            values='rating'
        )
        
        return matrix
    
    def get_movie_features(self):
        """
        获取电影特征（用于基于内容的推荐）
        
        Returns:
            dict: 电影ID到特征字典的映射
        """
        # 聚合每部电影的标签
        movie_tags = self.tags.groupby('movieId')['tag'].apply(
            lambda x: ' '.join(x.astype(str))
        ).reset_index()
        
        # 合并类型和标签
        movie_features = {}
        
        for _, row in self.movies.iterrows():
            movie_id = row['movieId']
            genres = ' '.join(row['genres_list']) if row['genres_list'] else ''
            
            # 查找该电影的标签
            tag_row = movie_tags[movie_tags['movieId'] == movie_id]
            tags = tag_row['tag'].values[0] if len(tag_row) > 0 else ''
            
            movie_features[movie_id] = {
                'genres': genres,
                'tags': tags,
                'combined': f"{genres} {tags}".strip()
            }
            
        return movie_features


if __name__ == '__main__':
    # 测试数据加载
    loader = DataLoader()
    if loader.load_data():
        loader.split_data()
        print("\n电影示例:")
        print(loader.movies.head())
        print("\n评分矩阵形状:", loader.get_user_movie_matrix().shape)