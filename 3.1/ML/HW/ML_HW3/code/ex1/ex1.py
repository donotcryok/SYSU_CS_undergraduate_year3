import numpy as np
import matplotlib.pyplot as plt
import random
import os

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class LinearRegression:
    def __init__(self):
        self.weights = None
        self.train_errors = []
        self.test_errors = []
        self.scaler_X = None
        self.scaler_y = None
        
    def load_data(self, filename):
        """加载数据文件"""
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, filename)
        
        data = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:  # 跳过空行
                        values = list(map(float, line.split()))
                        data.append(values)
            print(f"成功加载数据文件 {file_path}，包含 {len(data)} 行数据")
            return np.array(data)
        except Exception as e:
            print(f"加载文件 {file_path} 时出错: {e}")
            raise

    def normalize_features(self, X_train, X_test):
        """特征标准化"""
        # 对特征进行Z-score标准化（不包括偏置项）
        X_train_features = X_train[:, 1:]  # 去掉偏置项
        X_test_features = X_test[:, 1:]    # 去掉偏置项
        
        # 计算训练集的均值和标准差
        mean = np.mean(X_train_features, axis=0)
        std = np.std(X_train_features, axis=0)
        
        # 标准化
        X_train_normalized = (X_train_features - mean) / std
        X_test_normalized = (X_test_features - mean) / std
        
        # 重新添加偏置项
        X_train_final = np.column_stack([np.ones(X_train.shape[0]), X_train_normalized])
        X_test_final = np.column_stack([np.ones(X_test.shape[0]), X_test_normalized])
        
        self.scaler_X = {'mean': mean, 'std': std}
        return X_train_final, X_test_final

    def normalize_targets(self, y_train, y_test):
        """目标值标准化"""
        mean = np.mean(y_train)
        std = np.std(y_train)
        
        y_train_normalized = (y_train - mean) / std
        y_test_normalized = (y_test - mean) / std
        
        self.scaler_y = {'mean': mean, 'std': std}
        return y_train_normalized, y_test_normalized

    def preprocess_data(self, data):
        """数据预处理：添加偏置项"""
        X = data[:, :-1]  # 特征（面积、距离）
        y = data[:, -1]   # 标签（房价）
        # 添加偏置项（常数项1）
        X_with_bias = np.column_stack([np.ones(X.shape[0]), X])
        return X_with_bias, y
    
    def predict(self, X):
        """预测函数"""
        return X @ self.weights
    
    def compute_cost(self, X, y):
        """计算均方误差损失函数"""
        predictions = self.predict(X)
        cost = np.mean((predictions - y) ** 2)
        return cost
    
    def gradient_descent(self, X_train, y_train, X_test, y_test, 
                        learning_rate=0.01, iterations=1500000, normalize=True):
        """梯度下降法训练"""
        # 数据标准化
        if normalize:
            X_train_norm, X_test_norm = self.normalize_features(X_train, X_test)
            y_train_norm, y_test_norm = self.normalize_targets(y_train, y_test)
        else:
            X_train_norm, X_test_norm = X_train, X_test
            y_train_norm, y_test_norm = y_train, y_test
        
        # 初始化参数为0
        self.weights = np.zeros(X_train_norm.shape[1])
        self.train_errors = []
        self.test_errors = []
        
        m = X_train_norm.shape[0]  # 训练样本数量
        
        print(f"开始梯度下降训练...")
        print(f"参数数量: {len(self.weights)} (w0: 偏置项, w1: 面积系数, w2: 距离系数)")
        print(f"学习率: {learning_rate}")
        print(f"迭代次数: {iterations}")

        
        for i in range(iterations):
            # 前向传播
            predictions = self.predict(X_train_norm)
            
            # 计算梯度
            gradients = (2/m) * X_train_norm.T @ (predictions - y_train_norm)
            
            # 检查梯度是否有效
            if np.any(np.isnan(gradients)) or np.any(np.isinf(gradients)):
                print(f"警告：第{i+1}步出现无效梯度，停止训练")
                break
            
            # 更新权重
            self.weights -= learning_rate * gradients
            
            # 检查权重是否有效
            if np.any(np.isnan(self.weights)) or np.any(np.isinf(self.weights)):
                print(f"警告：第{i+1}步权重变为无效值，停止训练")
                break
            
            # 每100000次迭代记录误差
            if (i + 1) % 100000 == 0:
                if normalize:
                    # 反标准化计算真实误差
                    train_pred_denorm = predictions * self.scaler_y['std'] + self.scaler_y['mean']
                    test_pred = self.predict(X_test_norm)
                    test_pred_denorm = test_pred * self.scaler_y['std'] + self.scaler_y['mean']
                    
                    train_error = np.mean((train_pred_denorm - y_train) ** 2)
                    test_error = np.mean((test_pred_denorm - y_test) ** 2)
                else:
                    train_error = self.compute_cost(X_train_norm, y_train_norm)
                    test_error = self.compute_cost(X_test_norm, y_test_norm)
                
                self.train_errors.append(train_error)
                self.test_errors.append(test_error)
                print(f"第 {i+1:7d} 步: 训练误差 = {train_error:.4f}, 测试误差 = {test_error:.4f}")
        
        return self.weights
    
    def stochastic_gradient_descent(self, X_train, y_train, X_test, y_test,
                                   learning_rate=0.001, iterations=15000, K=1000, normalize=True):
        """随机梯度下降法训练"""
        # 数据标准化
        if normalize:
            X_train_norm, X_test_norm = self.normalize_features(X_train, X_test)
            y_train_norm, y_test_norm = self.normalize_targets(y_train, y_test)
        else:
            X_train_norm, X_test_norm = X_train, X_test
            y_train_norm, y_test_norm = y_train, y_test
        
        # 初始化参数为0
        self.weights = np.zeros(X_train_norm.shape[1])
        self.train_errors = []
        self.test_errors = []
        
        m = X_train_norm.shape[0]
        
        print(f"开始随机梯度下降训练...")
        print(f"参数数量: {len(self.weights)}")
        print(f"学习率: {learning_rate}")
        print(f"迭代次数: {iterations}")
        print(f"记录间隔: {K}")
        
        for i in range(iterations):
            # 随机选择一个样本
            idx = random.randint(0, m-1)
            x_i = X_train_norm[idx:idx+1]  # 保持2D形状
            y_i = y_train_norm[idx]
            
            # 前向传播
            prediction = self.predict(x_i)[0]
            
            # 计算梯度（单个样本）
            gradient = 2 * x_i[0] * (prediction - y_i)
            
            # 检查梯度是否有效
            if np.any(np.isnan(gradient)) or np.any(np.isinf(gradient)):
                print(f"警告：第{i+1}步出现无效梯度，停止训练")
                break
            
            # 更新权重
            self.weights -= learning_rate * gradient
            
            # 检查权重是否有效
            if np.any(np.isnan(self.weights)) or np.any(np.isinf(self.weights)):
                print(f"警告：第{i+1}步权重变为无效值，停止训练")
                break
            
            # 每K次迭代记录误差
            if (i + 1) % K == 0:
                if normalize:
                    # 反标准化计算真实误差
                    train_pred = self.predict(X_train_norm)
                    train_pred_denorm = train_pred * self.scaler_y['std'] + self.scaler_y['mean']
                    test_pred = self.predict(X_test_norm)
                    test_pred_denorm = test_pred * self.scaler_y['std'] + self.scaler_y['mean']
                    
                    train_error = np.mean((train_pred_denorm - y_train) ** 2)
                    test_error = np.mean((test_pred_denorm - y_test) ** 2)
                else:
                    train_error = self.compute_cost(X_train_norm, y_train_norm)
                    test_error = self.compute_cost(X_test_norm, y_test_norm)
                
                self.train_errors.append(train_error)
                self.test_errors.append(test_error)
                print(f"第 {i+1:6d} 步: 训练误差 = {train_error:.4f}, 测试误差 = {test_error:.4f}")
        
        return self.weights
    
    def plot_errors(self, title, x_label="迭代次数 (×100k)", save_filename=None):
        """绘制误差变化图"""
        plt.figure(figsize=(10, 6))
        iterations = range(1, len(self.train_errors) + 1)
        plt.plot(iterations, self.train_errors, 'b-', label='训练误差', linewidth=2, marker='o')
        plt.plot(iterations, self.test_errors, 'r-', label='测试误差', linewidth=2, marker='s')
        plt.xlabel(x_label)
        plt.ylabel('均方误差 (MSE)')
        plt.title(title)
        plt.legend()
        plt.grid(True, alpha=0.3)
        # 添加数值标注
        for i, (train_err, test_err) in enumerate(zip(self.train_errors, self.test_errors)):
            plt.annotate(f'{train_err:.3f}', (i+1, train_err), textcoords="offset points", 
                        xytext=(0,10), ha='center', fontsize=8)
            plt.annotate(f'{test_err:.3f}', (i+1, test_err), textcoords="offset points", 
                        xytext=(0,-15), ha='center', fontsize=8)
        plt.tight_layout()
        if save_filename:
            # 保存到 code/result 文件夹
            current_dir = os.path.dirname(os.path.abspath(__file__))
            result_dir = os.path.join(current_dir, './result')
            os.makedirs(result_dir, exist_ok=True)
            save_path = os.path.join(result_dir, save_filename)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图片已保存为: {save_path}")
        plt.show()

def analyze_results(weights, train_errors, test_errors, method_name):
    """分析实验结果"""
    print(f"\n{method_name} 结果分析:")
    print(f"最终参数值:")
    print(f"  w0 (偏置项): {weights[0]:.6f}")
    print(f"  w1 (面积系数): {weights[1]:.6f}")
    print(f"  w2 (距离系数): {weights[2]:.6f}")
    print(f"最终训练误差: {train_errors[-1]:.6f}")
    print(f"最终测试误差: {test_errors[-1]:.6f}")
    
    # 分析参数的实际意义
    print(f"参数解释:")
    if weights[1] > 0:
        print(f"  面积系数为正({weights[1]:.6f})，表明面积越大房价越高")
    else:
        print(f"  面积系数为负({weights[1]:.6f})，表明面积越大房价越低")
        
    if weights[2] > 0:
        print(f"  距离系数为正({weights[2]:.6f})，表明距离越远房价越高")
    else:
        print(f"  距离系数为负({weights[2]:.6f})，表明距离越远房价越低")

def main():
    """主函数"""
    print("="*60)
    print("线性回归房价预测实验")
    print("="*60)
    
    # 创建线性回归模型
    model = LinearRegression()
    
    # 加载数据
    print("正在加载数据...")
    try:
        train_data = model.load_data('dataForTrainingLinear.txt')
        test_data = model.load_data('dataForTestingLinear.txt')
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请确保数据文件存在在当前目录中")
        return
    
    # 预处理数据
    X_train, y_train = model.preprocess_data(train_data)
    X_test, y_test = model.preprocess_data(test_data)
    
    print(f"训练集大小: {X_train.shape[0]} 个样本, {X_train.shape[1]-1} 个特征 + 1个偏置项")
    print(f"测试集大小: {X_test.shape[0]} 个样本")
    print(f"特征: 房屋面积、到双鸭山职业技术学院的距离")
    print(f"标签: 房价 (亿元)")
    
    # ==================== (a) 梯度下降法 - 学习率 0.00015 ====================
    print("\n" + "="*60)
    print("(a) 梯度下降法训练 - 学习率 0.00015")
    print("="*60)
    
    model_a = LinearRegression()
    weights_a = model_a.gradient_descent(X_train, y_train, X_test, y_test, 
                                       learning_rate=0.00015, iterations=1500000, normalize=True)
    
    analyze_results(weights_a, model_a.train_errors, model_a.test_errors, "梯度下降法(lr=0.00015)")
    model_a.plot_errors("梯度下降法 - 学习率 0.00015", save_filename="gd_lr_00015.png")
    
    # ==================== (b) 梯度下降法 - 学习率 0.0002 ====================
    print("\n" + "="*60)
    print("(b) 梯度下降法训练 - 学习率 0.0002")
    print("="*60)
    
    model_b = LinearRegression()
    weights_b = model_b.gradient_descent(X_train, y_train, X_test, y_test, 
                                       learning_rate=0.0002, iterations=1500000, normalize=True)
    
    analyze_results(weights_b, model_b.train_errors, model_b.test_errors, "梯度下降法(lr=0.0002)")
    model_b.plot_errors("梯度下降法 - 学习率 0.0002", save_filename="gd_lr_0002.png")
    
    # ==================== (c) 随机梯度下降法 ====================
    print("\n" + "="*60)
    print("(c) 随机梯度下降法训练")
    print("="*60)
    
    model_c = LinearRegression()
    weights_c = model_c.stochastic_gradient_descent(X_train, y_train, X_test, y_test,
                                                  learning_rate=0.001, iterations=10000, K=1000, normalize=True)
    
    analyze_results(weights_c, model_c.train_errors, model_c.test_errors, "随机梯度下降法")
    model_c.plot_errors("随机梯度下降法", x_label="迭代次数 (×1k)", save_filename="sgd.png")

    # ==================== 综合分析比较 ====================
    print("\n" + "="*60)
    print("实验结果综合分析")
    print("="*60)
    
    print("方法比较:")
    methods = [
        ("梯度下降法(lr=0.00015)", weights_a, model_a.train_errors[-1], model_a.test_errors[-1]),
        ("梯度下降法(lr=0.0002)", weights_b, model_b.train_errors[-1], model_b.test_errors[-1]),
        ("随机梯度下降法", weights_c, model_c.train_errors[-1], model_c.test_errors[-1])
    ]
    
    print(f"{'方法':<20} {'w0 (偏置)':<12} {'w1 (面积)':<12} {'w2 (距离)':<12} {'训练误差':<10} {'测试误差':<10}")
    print("-" * 80)
    for name, weights, train_err, test_err in methods:
        print(f"{name:<20} {weights[0]:<12.4f} {weights[1]:<12.4f} {weights[2]:<12.4f} {train_err:<10.4f} {test_err:<10.4f}")
    
    # 预测示例
    print("\n预测示例:")
    sample_area = 100  # 100平方米
    sample_distance = 5  # 5千米
    sample_input = np.array([[1, sample_area, sample_distance]])  # 添加偏置项
    
    pred_a = model_a.predict(sample_input)[0]
    pred_b = model_b.predict(sample_input)[0]
    pred_c = model_c.predict(sample_input)[0]
    
    print(f"对于 {sample_area}平方米、距离{sample_distance}千米的房屋:")
    print(f"  梯度下降法(lr=0.00015)预测房价: {pred_a:.4f} 亿元")
    print(f"  梯度下降法(lr=0.0002)预测房价: {pred_b:.4f} 亿元")
    print(f"  随机梯度下降法预测房价: {pred_c:.4f} 亿元")

if __name__ == "__main__":
    # 设置随机种子以确保结果可重现
    random.seed(42)
    np.random.seed(42)
    main()
