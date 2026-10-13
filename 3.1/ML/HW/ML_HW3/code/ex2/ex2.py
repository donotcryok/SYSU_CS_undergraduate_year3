import numpy as np
import matplotlib.pyplot as plt
import random
import os

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class LogisticRegression:
    def __init__(self):
        self.weights = None
        self.train_errors = []
        self.test_errors = []
        self.log_likelihoods = []
        
    def load_data(self, filename):
        """加载数据文件"""
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

    def preprocess_data(self, data):
        """数据预处理：添加偏置项"""
        X = data[:, :-1]  # 特征（前6列）
        y = data[:, -1]   # 标签（最后一列）
        # 添加偏置项（常数项1）
        X_with_bias = np.column_stack([np.ones(X.shape[0]), X])
        return X_with_bias, y
    
    def sigmoid(self, z):
        """Sigmoid激活函数"""
        # 防止数值溢出
        z = np.clip(z, -500, 500)
        return 1 / (1 + np.exp(-z))
    
    def predict_proba(self, X):
        """预测概率"""
        z = X @ self.weights
        return self.sigmoid(z)
    
    def predict(self, X):
        """预测类别"""
        probabilities = self.predict_proba(X)
        return (probabilities >= 0.5).astype(int)
    
    def compute_log_likelihood(self, X, y):
        """计算对数似然函数"""
        z = X @ self.weights
        # 使用数值稳定的计算方式
        log_likelihood = np.sum(y * z - np.log(1 + np.exp(z)))
        return log_likelihood
    
    def compute_error_rate(self, X, y):
        """计算错误率"""
        predictions = self.predict(X)
        errors = np.sum(predictions != y)
        return errors, errors / len(y)
    
    def gradient_ascent(self, X_train, y_train, X_test, y_test, 
                       learning_rate=0.01, iterations=10000):
        """梯度上升法训练（批量）"""
        # 初始化参数为0
        self.weights = np.zeros(X_train.shape[1])
        self.train_errors = []
        self.test_errors = []
        self.log_likelihoods = []
        
        m = X_train.shape[0]
        
        print(f"开始梯度上升训练...")
        print(f"参数数量: {len(self.weights)} (w0: 偏置项, w1-w6: 特征系数)")
        print(f"学习率: {learning_rate}")
        print(f"迭代次数: {iterations}")
        
        for i in range(iterations):
            # 前向传播
            probabilities = self.predict_proba(X_train)
            
            # 计算梯度（对数似然的梯度）
            gradients = X_train.T @ (y_train - probabilities)
            
            # 检查梯度是否有效
            if np.any(np.isnan(gradients)) or np.any(np.isinf(gradients)):
                print(f"警告：第{i+1}步出现无效梯度，停止训练")
                break
            
            # 更新权重（梯度上升）
            self.weights += learning_rate * gradients
            
            # 检查权重是否有效
            if np.any(np.isnan(self.weights)) or np.any(np.isinf(self.weights)):
                print(f"警告：第{i+1}步权重变为无效值，停止训练")
                break
            
            # 每500次迭代记录误差和对数似然
            if (i + 1) % 500 == 0:
                log_likelihood = self.compute_log_likelihood(X_train, y_train)
                train_errors, train_error_rate = self.compute_error_rate(X_train, y_train)
                test_errors, test_error_rate = self.compute_error_rate(X_test, y_test)
                
                self.log_likelihoods.append(log_likelihood)
                self.train_errors.append(train_errors)
                self.test_errors.append(test_errors)
                
                print(f"第 {i+1:5d} 步: 对数似然 = {log_likelihood:.4f}, "
                      f"训练错误 = {train_errors}/{len(y_train)} ({train_error_rate:.3f}), "
                      f"测试错误 = {test_errors}/{len(y_test)} ({test_error_rate:.3f})")
        
        return self.weights
    
    def stochastic_gradient_ascent(self, X_train, y_train, X_test, y_test,
                                  learning_rate=0.01, iterations=50000, K=1000):
        """随机梯度上升法训练"""
        # 初始化参数为0
        self.weights = np.zeros(X_train.shape[1])
        self.train_errors = []
        self.test_errors = []
        self.log_likelihoods = []
        
        m = X_train.shape[0]
        
        print(f"开始随机梯度上升训练...")
        print(f"参数数量: {len(self.weights)}")
        print(f"学习率: {learning_rate}")
        print(f"迭代次数: {iterations}")
        print(f"记录间隔: {K}")
        
        for i in range(iterations):
            # 随机选择一个样本
            idx = random.randint(0, m-1)
            x_i = X_train[idx:idx+1]  # 保持2D形状
            y_i = y_train[idx]
            
            # 前向传播
            probability = self.predict_proba(x_i)[0]
            
            # 计算梯度（单个样本）
            gradient = x_i[0] * (y_i - probability)
            
            # 检查梯度是否有效
            if np.any(np.isnan(gradient)) or np.any(np.isinf(gradient)):
                print(f"警告：第{i+1}步出现无效梯度，停止训练")
                break
            
            # 更新权重
            self.weights += learning_rate * gradient
            
            # 检查权重是否有效
            if np.any(np.isnan(self.weights)) or np.any(np.isinf(self.weights)):
                print(f"警告：第{i+1}步权重变为无效值，停止训练")
                break
            
            # 每K次迭代记录误差和对数似然
            if (i + 1) % K == 0:
                log_likelihood = self.compute_log_likelihood(X_train, y_train)
                train_errors, train_error_rate = self.compute_error_rate(X_train, y_train)
                test_errors, test_error_rate = self.compute_error_rate(X_test, y_test)
                
                self.log_likelihoods.append(log_likelihood)
                self.train_errors.append(train_errors)
                self.test_errors.append(test_errors)
                
                print(f"第 {i+1:6d} 步: 对数似然 = {log_likelihood:.4f}, "
                      f"训练错误 = {train_errors}/{len(y_train)} ({train_error_rate:.3f}), "
                      f"测试错误 = {test_errors}/{len(y_test)} ({test_error_rate:.3f})")
        
        return self.weights
    
    def train_with_subset(self, X_train, y_train, X_test, y_test, subset_size, 
                         learning_rate=0.01, iterations=5000):
        """使用训练集子集训练模型"""
        # 随机选择子集
        indices = np.random.choice(len(X_train), subset_size, replace=False)
        X_subset = X_train[indices]
        y_subset = y_train[indices]
        
        # 初始化参数
        weights = np.zeros(X_subset.shape[1])
        
        # 训练
        for i in range(iterations):
            probabilities = self.sigmoid(X_subset @ weights)
            gradients = X_subset.T @ (y_subset - probabilities)
            weights += learning_rate * gradients
        
        # 计算误差
        train_pred = (self.sigmoid(X_subset @ weights) >= 0.5).astype(int)
        test_pred = (self.sigmoid(X_test @ weights) >= 0.5).astype(int)
        
        train_errors = np.sum(train_pred != y_subset)
        test_errors = np.sum(test_pred != y_test)
        
        return train_errors, test_errors, weights
    
    def plot_log_likelihood(self, save_filename=None):
        """绘制对数似然变化图"""
        plt.figure(figsize=(10, 6))
        iterations = range(len(self.log_likelihoods))
        plt.plot(iterations, self.log_likelihoods, 'g-', linewidth=2, marker='o')
        plt.xlabel('迭代次数 (×1000)')
        plt.ylabel('对数似然值')
        plt.title('随机梯度上升法 - 对数似然变化')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_filename:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            result_dir = os.path.join(current_dir, './result')
            os.makedirs(result_dir, exist_ok=True)
            save_path = os.path.join(result_dir, save_filename)
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"图片已保存为: {save_path}")
        plt.show()
    
    def plot_error_curves(self, train_sizes, train_errors_list, test_errors_list, save_filename=None):
        """绘制训练集规模与误错误率关系图"""
        plt.figure(figsize=(12, 8))
        plt.plot(train_sizes, train_errors_list, 'b-', label='训练误差', linewidth=2, marker='o')
        plt.plot(train_sizes, test_errors_list, 'r-', label='测试误差', linewidth=2, marker='s')
        plt.xlabel('训练集规模')
        plt.ylabel('误分类样本数')
        plt.title('训练集规模对误差的影响')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if save_filename:
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
    for i in range(1, len(weights)):
        print(f"  w{i} (特征{i}系数): {weights[i]:.6f}")
    
    print(f"最终训练误分类数: {train_errors[-1]}")
    print(f"最终测试误分类数: {test_errors[-1]}")

def main():
    """主函数"""
    print("="*80)
    print("逻辑回归二分类实验")
    print("="*80)
    
    # 创建逻辑回归模型
    model = LogisticRegression()
    
    # 加载数据
    print("\n" + "="*80)
    print("加载数据")
    print("="*80)
    try:
        train_data = model.load_data('dataForTrainingLogistic.txt')
        test_data = model.load_data('dataForTestingLogistic.txt')
    except FileNotFoundError as e:
        print(f"错误: {e}")
        print("请确保数据文件存在在当前目录中")
        return
    
    # 预处理数据
    X_train, y_train = model.preprocess_data(train_data)
    X_test, y_test = model.preprocess_data(test_data)
    
    print(f"训练集大小: {X_train.shape[0]} 个样本, {X_train.shape[1]-1} 个特征 + 1个偏置项")
    print(f"测试集大小: {X_test.shape[0]} 个样本")
    print(f"特征数量: 6个")
    print(f"类别分布 - 训练集: 类别1={np.sum(y_train)}, 类别0={len(y_train)-np.sum(y_train)}")
    print(f"类别分布 - 测试集: 类别1={np.sum(y_test)}, 类别0={len(y_test)-np.sum(y_test)}")
    
    # ==================== Query(c) - 训练分类器 Query(a)(b)不再赘述====================
    print("\n" + "="*80)
    print("Query(c) - 训练逻辑回归分类器")
    print("="*80)
    
    # 使用随机梯度上升训练
    model_c = LogisticRegression()
    weights_c = model_c.stochastic_gradient_ascent(X_train, y_train, X_test, y_test,
                                                  learning_rate=0.1, iterations=100000, K=2000)
    
    analyze_results(weights_c, model_c.train_errors, model_c.test_errors, "随机梯度上升法")
    
    # 预测测试集
    test_predictions = model_c.predict(X_test)
    print(f"\n测试集预测结果:")
    print(f"预测的类别标签: {test_predictions}")
    print(f"真实的类别标签: {y_test.astype(int)}")
    
    # ==================== Query(d) - 报告误分类样本数 ====================
    print("\n" + "="*80)
    print("Query(d) - 测试集误分类分析")
    print("="*80)
    
    test_errors, test_error_rate = model_c.compute_error_rate(X_test, y_test)
    print(f"测试集总样本数: {len(y_test)}")
    print(f"误分类样本数: {test_errors}")
    print(f"误分类率: {test_error_rate:.4f} ({test_error_rate*100:.2f}%)")
    print(f"准确率: {1-test_error_rate:.4f} ({(1-test_error_rate)*100:.2f}%)")
    
    # 详细分析误分类样本
    misclassified_indices = np.where(test_predictions != y_test)[0]
    print(f"\n误分类样本详情:")
    print(f"误分类样本索引: {misclassified_indices}")
    for idx in misclassified_indices[:10]:  # 显示前10个误分类样本
        prob = model_c.predict_proba(X_test[idx:idx+1])[0]
        print(f"样本{idx}: 真实={int(y_test[idx])}, 预测={test_predictions[idx]}, 概率={prob:.4f}")
    
    # ==================== Query(e) - 绘制对数似然曲线 ====================
    print("\n" + "="*80)
    print("Query(e) - 对数似然收敛分析")
    print("="*80)
    
    # 分析收敛性
    log_likelihoods = model_c.log_likelihoods
    print(f"对数似然变化:")
    print(f"初始值: {log_likelihoods[0]:.4f}")
    print(f"最终值: {log_likelihoods[-1]:.4f}")
    print(f"总变化: {log_likelihoods[-1] - log_likelihoods[0]:.4f}")
    
    # 判断收敛
    convergence_threshold = 0.001
    convergence_window = 5
    converged = False
    convergence_iteration = len(log_likelihoods)
    
    for i in range(convergence_window, len(log_likelihoods)):
        recent_change = abs(log_likelihoods[i] - log_likelihoods[i-convergence_window])
        if recent_change < convergence_threshold:
            converged = True
            convergence_iteration = i * 1000  # 转换为实际迭代次数
            break
    
    if converged:
        print(f"算法在第 {convergence_iteration} 次迭代时收敛")
    else:
        print(f"算法在 {len(log_likelihoods)*1000} 次迭代内未完全收敛")
    
    model_c.plot_log_likelihood(save_filename="log_likelihood_curve.png")
    
    # ==================== Query(f) - 训练集规模影响分析 ====================
    print("\n" + "="*80)
    print("Query(f) - 训练集规模对误差的影响")
    print("="*80)
    
    # 设置随机种子确保可重现性
    np.random.seed(42)
    
    train_sizes = list(range(10, 401, 10))  # 10, 20, 30, ..., 400
    train_errors_list = []
    test_errors_list = []
    
    print("训练集规模分析进行中...")
    for k in train_sizes:
        train_errors, test_errors, _ = model_c.train_with_subset(
            X_train, y_train, X_test, y_test, k, learning_rate=0.01, iterations=3000)
        train_errors_list.append(train_errors)
        test_errors_list.append(test_errors)
        
        if k % 50 == 0:  # 每50个样本打印一次
            print(f"训练集规模 {k}: 训练误差 = {train_errors}, 测试误差 = {test_errors}")
    
    # 绘制学习曲线
    model_c.plot_error_curves(train_sizes, train_errors_list, test_errors_list, 
                             save_filename="learning_curves.png")
    
    # 分析趋势
    print(f"\n学习曲线分析:")
    print(f"最小训练集规模 (k=10): 训练误差 = {train_errors_list[0]}, 测试误差 = {test_errors_list[0]}")
    print(f"最大训练集规模 (k=400): 训练误差 = {train_errors_list[-1]}, 测试误差 = {test_errors_list[-1]}")
    print(f"测试误差改善: {test_errors_list[0] - test_errors_list[-1]} 个样本")
    
    # 找到测试误差最低点
    min_test_error_idx = np.argmin(test_errors_list)
    optimal_size = train_sizes[min_test_error_idx]
    min_test_error = test_errors_list[min_test_error_idx]
    print(f"最优训练集规模: {optimal_size} (测试误差 = {min_test_error})")


if __name__ == "__main__":
    # 设置随机种子以确保结果可重现
    random.seed(42)
    np.random.seed(42)
    main()
