"""
股票数据下载脚本
"""
import yfinance as yf
import pandas as pd
import os
import time
import numpy as np
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
IMG_DIR = os.path.join(PROJECT_DIR, 'img')

def download_stock_data(stock_code="AAPL", period="5y", save_path=None, max_retries=3):
    """
    下载股票历史数据并保存为CSV文件
    Parameters:
    -----------
    stock_code : str
        股票代码，默认为 AAPL（苹果公司）
    period : str
        下载的时间周期，默认为 5y（5年）
    save_path : str
        数据保存路径，默认为 data/stock_data.csv
    max_retries : int
        最大重试次数
    Returns:
    --------
    pd.DataFrame
        清洗后的股票数据，包含 Date 和 Close 列
    """
    # 设置默认保存路径
    if save_path is None:
        save_path = os.path.join(DATA_DIR, 'stock_data.csv')
    
    print(f"正在下载 {stock_code} 过去 {period} 的历史数据...")
    
    # 尝试下载数据，带重试机制
    data = None
    for attempt in range(max_retries):
        try:
            print(f"尝试下载 (第 {attempt + 1}/{max_retries} 次)...")
            data = yf.download(stock_code, period=period, progress=True)
            
            # 检查是否成功获取数据
            if data is not None and len(data) > 0:
                print(f"下载成功！获取 {len(data)} 条数据记录")
                break
            else:
                print("下载的数据为空，等待后重试...")
                time.sleep(5)
                
        except Exception as e:
            print(f"下载出错: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print("达到最大重试次数，将使用模拟数据...")
    
    # 如果下载失败，生成模拟数据
    if data is None or len(data) == 0:
        print("\n" + "="*50)
        print("将生成模拟股票数据用于实验演示...")
        print("="*50 + "\n")
        data = generate_simulated_stock_data(period_years=5)
        print(f"已生成 {len(data)} 条模拟数据记录")
    
    # 处理 MultiIndex 问题（yfinance 有时会返回 MultiIndex 列）
    if isinstance(data.columns, pd.MultiIndex):
        # 如果是 MultiIndex，取第一层索引
        data.columns = data.columns.get_level_values(0)
    
    # 重置索引，将 Date 从索引变为普通列
    data.reset_index(inplace=True)
    
    # 确保只保留需要的列：Date 和 Close
    if 'Date' in data.columns and 'Close' in data.columns:
        data = data[['Date', 'Close']]
    elif 'index' in data.columns and 'Close' in data.columns:
        data = data.rename(columns={'index': 'Date'})
        data = data[['Date', 'Close']]
    
    data['Date'] = pd.to_datetime(data['Date'])
    
    data['Close'] = pd.to_numeric(data['Close'], errors='coerce')
    
    # 删除可能的缺失值
    data.dropna(subset=['Date', 'Close'], inplace=True)
    
    # 确保数据按日期升序排列
    data.sort_values('Date', inplace=True)
    data.reset_index(drop=True, inplace=True)
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    # 保存为 CSV 文件
    data.to_csv(save_path, index=False)
    
    print(f"\n数据已保存至：{save_path}")
    print(f"\n数据预览：")
    print(data.head())
    print(f"\n数据统计信息：")
    print(data.describe())
    
    return data


def generate_simulated_stock_data(period_years=5, start_price=150.0):
    """
    生成模拟的股票数据（用于 yfinance 无法下载时的备选方案）
    Parameters:
    -----------
    period_years : int
        生成的年数
    start_price : float
        起始价格
    
    Returns:
    --------
    pd.DataFrame
        模拟的股票数据，包含 Date 和 Close 列
    """
    print("正在生成模拟股票数据...")
    
    # 生成日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=period_years * 365)
    
    # 生成所有日期
    all_dates = pd.date_range(start=start_date, end=end_date, freq='B')  # 'B' 表示工作日
    
    # 设置随机种子以保证可复现
    np.random.seed(42)
    
    # 使用几何布朗运动模拟股票价格
    n_days = len(all_dates)
    
    # 参数设置
    mu = 0.0003  # 日收益率均值（年化约 7.5%）
    sigma = 0.02  # 日波动率（年化约 32%）
    
    # 生成随机收益率
    returns = np.random.normal(mu, sigma, n_days)
    
    # 计算价格序列
    prices = np.zeros(n_days)
    prices[0] = start_price
    
    for i in range(1, n_days):
        prices[i] = prices[i-1] * (1 + returns[i])
    
    data = pd.DataFrame({
        'Date': all_dates,
        'Close': np.round(prices, 2)
    })
    
    print(f"模拟数据生成完成，共 {n_days} 个交易日")
    print(f"日期范围：{all_dates[0].strftime('%Y-%m-%d')} ~ {all_dates[-1].strftime('%Y-%m-%d')}")
    print(f"价格范围：${prices.min():.2f} ~ ${prices.max():.2f}")
    
    return data


if __name__ == "__main__":
    # 执行数据下载
    download_stock_data()