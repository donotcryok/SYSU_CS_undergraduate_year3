"""
股票价格预测脚本：使用 ARIMA 和 LSTM 模型预测股票未来7天的价格
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_DIR, 'data')
IMG_DIR = os.path.join(PROJECT_DIR, 'img')

# 中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# ==================== ARIMA 模型相关导入 ====================
HAS_PMDARIMA = False
try:
    from pmdarima import auto_arima
    HAS_PMDARIMA = True
except (ImportError, ValueError) as e:
    print(f"注意: pmdarima 不可用 ({e})，将使用 statsmodels ARIMA")
    from statsmodels.tsa.arima.model import ARIMA

# ==================== LSTM 模型相关导入 (PyTorch) ====================
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# 随机种子
np.random.seed(42)
torch.manual_seed(42)


#LSTM 网络定义
class LSTMModel(nn.Module):
    """
    LSTM 网络结构定义
    结构说明：
    - 输入层：接收滑动窗口构造的时序特征
    - LSTM 层：捕捉时间序列的长期依赖关系
    - 全连接层：输出预测值
    """
    def __init__(self, input_size=1, hidden_size=64, num_layers=2, output_size=1, dropout=0.2):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # LSTM 层
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout
        )
        
        # 全连接层
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        # 初始化隐藏状态
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        
        # LSTM 前向传播
        out, _ = self.lstm(x, (h0, c0))
        
        # 取最后一个时间步的输出
        out = self.fc(out[:, -1, :])
        return out


#数据处理函数 
def load_data(file_path):
    """加载股票数据"""
    print(f"正在加载数据：{file_path}")
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df.sort_values('Date', inplace=True)
    df.reset_index(drop=True, inplace=True)
    print(f"数据加载成功，共 {len(df)} 条记录")
    return df


def create_sequences(data, window_size):
    """
    使用滑动窗口构造时序特征
    
    Parameters:
    -----------
    data : np.array
        归一化后的数据
    window_size : int
        滑动窗口大小
    
    Returns:
    --------
    X, y : np.array
        特征和标签
    """
    X, y = [], []
    for i in range(len(data) - window_size):
        X.append(data[i:i+window_size])
        y.append(data[i+window_size])
    return np.array(X), np.array(y)


#ARIMA 模型 
def train_arima(train_data, test_data):
    """
    训练 ARIMA 模型
    
    Parameters:
    -----------
    train_data : np.array
        训练数据
    test_data : np.array
        测试数据
    
    Returns:
    --------
    model : 训练好的模型
    test_pred : 测试集预测
    future_pred : 未来7天预测
    order : ARIMA 参数 (p, d, q)
    """
    print("\n" + "="*50)
    print("训练 ARIMA 模型...")
    print("="*50)
    
    if HAS_PMDARIMA:
        #使用 auto_arima 自动寻找最优参数
        print("使用 auto_arima 自动寻找最优参数...")
        model = auto_arima(
            train_data,
            start_p=0, start_q=0,
            max_p=5, max_q=5,
            d=None,  # 自动确定差分阶数
            seasonal=False,
            stepwise=True,
            suppress_warnings=True,
            trace=True
        )
        order = model.order
        print(f"最优参数: ARIMA{order}")
    else:
        #手动设置参数
        order = (5, 1, 0)
        print(f"使用预设参数: ARIMA{order}")
        model = ARIMA(train_data, order=order)
        model = model.fit()
    
    #测试集预测
    test_pred = model.predict(n_periods=len(test_data)) if HAS_PMDARIMA else model.forecast(steps=len(test_data))
    
    #未来7天预测
    future_pred = model.predict(n_periods=len(test_data) + 7) if HAS_PMDARIMA else model.forecast(steps=len(test_data) + 7)
    future_pred = future_pred[-7:] if HAS_PMDARIMA else future_pred[-7:]
    
    print("ARIMA 模型训练完成！")
    
    return model, test_pred, future_pred, order


#LSTM 模型
def train_lstm(train_data, test_data, window_size=30, epochs=100, batch_size=32, learning_rate=0.001):
    """
    训练 LSTM 模型
    
    Parameters:
    -----------
    train_data : np.array
        训练数据（原始值）
    test_data : np.array
        测试数据（原始值）
    window_size : int
        滑动窗口大小
    epochs : int
        训练轮数
    batch_size : int
        批次大小
    learning_rate : float
        学习率
    
    Returns:
    --------
    model : 训练好的模型
    scaler : 归一化器
    test_pred : 测试集预测（原始尺度）
    future_pred : 未来7天预测（原始尺度）
    """
    print("\n" + "="*50)
    print("训练 LSTM 模型...")
    print("="*50)
    
    #数据归一化
    scaler = MinMaxScaler(feature_range=(0, 1))
    train_scaled = scaler.fit_transform(train_data.reshape(-1, 1)).flatten()
    test_scaled = scaler.transform(test_data.reshape(-1, 1)).flatten()
    
    #合并数据用于滑动窗口
    full_data = np.concatenate([train_scaled, test_scaled])
    
    #构建训练序列
    X_train, y_train = create_sequences(train_scaled, window_size)
    
    #转换为 PyTorch 张量
    X_train = torch.FloatTensor(X_train).unsqueeze(-1)  # (samples, window_size, 1)
    y_train = torch.FloatTensor(y_train).unsqueeze(-1)  # (samples, 1)
    
    #创建数据加载器
    train_dataset = TensorDataset(X_train, y_train)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    
    #初始化模型
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")
    
    model = LSTMModel(input_size=1, hidden_size=64, num_layers=2, output_size=1, dropout=0.2)
    model = model.to(device)
    
    #定义损失函数和优化器
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    #训练模型
    print(f"开始训练，共 {epochs} 轮...")
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        if (epoch + 1) % 20 == 0:
            avg_loss = total_loss / len(train_loader)
            print(f"Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.6f}")
    
    print("LSTM 模型训练完成！")
    
    #测试集预测
    model.eval()
    with torch.no_grad():
        #使用训练数据的最后 window_size 个点开始预测
        test_input = train_scaled[-window_size:]
        test_pred_scaled = []
        
        for i in range(len(test_data)):
            x = torch.FloatTensor(test_input[-window_size:]).unsqueeze(0).unsqueeze(-1).to(device)
            pred = model(x).cpu().numpy()[0, 0]
            test_pred_scaled.append(pred)
            test_input = np.append(test_input, test_scaled[i])
        
        test_pred = scaler.inverse_transform(np.array(test_pred_scaled).reshape(-1, 1)).flatten()
    
    #未来7天预测
    with torch.no_grad():
        #使用全部数据进行预测
        future_input = full_data[-window_size:]
        future_pred_scaled = []
        
        for i in range(7):
            x = torch.FloatTensor(future_input[-window_size:]).unsqueeze(0).unsqueeze(-1).to(device)
            pred = model(x).cpu().numpy()[0, 0]
            future_pred_scaled.append(pred)
            future_input = np.append(future_input, pred)
        
        future_pred = scaler.inverse_transform(np.array(future_pred_scaled).reshape(-1, 1)).flatten()
    
    return model, scaler, test_pred, future_pred


#评估函数
def evaluate_model(y_true, y_pred, model_name):
    """
    计算模型的评估指标
    
    Parameters:
    -----------
    y_true : np.array
        真实值
    y_pred : np.array
        预测值
    model_name : str
        模型名称
    
    Returns:
    --------
    mae, rmse : float
        平均绝对误差和均方根误差
    """
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    
    print(f"\n{model_name} 模型评估结果:")
    print(f"  MAE:  {mae:.4f}")
    print(f"  RMSE: {rmse:.4f}")
    
    return mae, rmse


#可视化函数
def plot_results(df, train_size, test_data, arima_test_pred, arima_future_pred, 
                 lstm_test_pred, lstm_future_pred, save_path):
    """
    绘制预测对比图
    
    Parameters:
    -----------
    df : pd.DataFrame
        完整数据
    train_size : int
        训练集大小
    test_data : np.array
        测试集真实数据
    arima_test_pred : np.array
        ARIMA 测试集预测
    arima_future_pred : np.array
        ARIMA 未来7天预测
    lstm_test_pred : np.array
        LSTM 测试集预测
    lstm_future_pred : np.array
        LSTM 未来7天预测
    save_path : str
        图片保存路径
    """
    print("\n正在生成预测对比图...")
    
    #创建图形
    fig, ax = plt.subplots(figsize=(14, 8))

    dates = df['Date'].values
    train_dates = dates[:train_size]
    test_dates = dates[train_size:]

    last_date = pd.to_datetime(dates[-1])
    future_dates = [last_date + pd.Timedelta(days=i+1) for i in range(7)]
    
    #绘制历史数据
    show_history = 100
    history_start = max(0, train_size - show_history)
    history_dates = dates[history_start:train_size]
    history_data = df['Close'].values[history_start:train_size]
    
    #绘制历史数据
    ax.plot(history_dates, history_data, 'b-', label='历史数据', linewidth=1.5, alpha=0.7)
    
    #绘制测试数据
    ax.plot(test_dates, test_data, 'g-', label='真实测试数据', linewidth=2)
    
    #绘制ARIMA预测
    ax.plot(test_dates, arima_test_pred, 'r--', label='ARIMA 测试预测', linewidth=1.5)
    ax.plot(future_dates, arima_future_pred, 'r:', label='ARIMA 未来7天预测', linewidth=2, marker='o', markersize=4)
    
    #绘制LSTM预测
    ax.plot(test_dates, lstm_test_pred, 'm--', label='LSTM 测试预测', linewidth=1.5)
    ax.plot(future_dates, lstm_future_pred, 'm:', label='LSTM 未来7天预测', linewidth=2, marker='s', markersize=4)
    
    #设置图表属性
    ax.set_xlabel('日期', fontsize=12)
    ax.set_ylabel('收盘价 ($)', fontsize=12)
    ax.set_title('股票价格预测对比：ARIMA vs LSTM', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)

    ax.axvline(x=test_dates[0], color='gray', linestyle='--', alpha=0.5, label='测试集起点')
    ax.axvline(x=test_dates[-1], color='gray', linestyle=':', alpha=0.5)

    plt.xticks(rotation=45)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"预测对比图已保存至：{save_path}")
    
    plt.close()

def main():
    """主函数"""
    print("="*60)
    print("股票价格预测 - ARIMA vs LSTM")
    print("="*60)
    
    # 1. 加载数据
    data_path = os.path.join(DATA_DIR, 'stock_data.csv')
    df = load_data(data_path)
    
    # 2. 数据预处理
    close_prices = df['Close'].values
    
    # 划分训练集和测试集（80% 训练，20% 测试）
    train_size = int(len(close_prices) * 0.8)
    train_data = close_prices[:train_size]
    test_data = close_prices[train_size:]
    
    print(f"\n数据集划分:")
    print(f"  训练集: {len(train_data)} 条 ({df['Date'].iloc[0].strftime('%Y-%m-%d')} ~ {df['Date'].iloc[train_size-1].strftime('%Y-%m-%d')})")
    print(f"  测试集: {len(test_data)} 条 ({df['Date'].iloc[train_size].strftime('%Y-%m-%d')} ~ {df['Date'].iloc[-1].strftime('%Y-%m-%d')})")
    
    # 3. 训练 ARIMA 模型
    arima_model, arima_test_pred, arima_future_pred, arima_order = train_arima(train_data, test_data)
    
    # 4. 训练 LSTM 模型
    lstm_model, scaler, lstm_test_pred, lstm_future_pred = train_lstm(
        train_data, test_data, 
        window_size=30, 
        epochs=100, 
        batch_size=32
    )
    
    # 5. 模型评估
    arima_mae, arima_rmse = evaluate_model(test_data, arima_test_pred, "ARIMA")
    lstm_mae, lstm_rmse = evaluate_model(test_data, lstm_test_pred, "LSTM")
    
    # 6. 打印未来7天预测结果
    print("\n" + "="*60)
    print("未来7天价格预测")
    print("="*60)
    last_date = df['Date'].iloc[-1]
    print(f"\n基准日期: {last_date.strftime('%Y-%m-%d')}")
    print(f"\n{'日期':<15} {'ARIMA预测':<15} {'LSTM预测':<15}")
    print("-" * 45)
    for i in range(7):
        future_date = last_date + pd.Timedelta(days=i+1)
        print(f"{future_date.strftime('%Y-%m-%d'):<15} ${arima_future_pred[i]:.2f}{'':<8} ${lstm_future_pred[i]:.2f}")
    
    # 7. 可视化
    plot_results(
        df, train_size, test_data,
        arima_test_pred, arima_future_pred,
        lstm_test_pred, lstm_future_pred,
        save_path=os.path.join(IMG_DIR, 'prediction_comparison.png')
    )
    
    # 8. 保存评估结果
    results = {
        'Model': ['ARIMA', 'LSTM'],
        'MAE': [arima_mae, lstm_mae],
        'RMSE': [arima_rmse, lstm_rmse]
    }
    results_df = pd.DataFrame(results)
    results_df.to_csv(os.path.join(IMG_DIR, 'evaluation_metrics.csv'), index=False)
    print(f"\n评估指标已保存至：{os.path.join(IMG_DIR, 'evaluation_metrics.csv')}")
    
    print("\n" + "="*60)
    print("预测任务完成！")
    print("="*60)


if __name__ == "__main__":
    main()