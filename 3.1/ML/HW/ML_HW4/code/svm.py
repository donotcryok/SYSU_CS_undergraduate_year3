import argparse
import os
import random
import math
import csv
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Tuple, Dict, Any, Optional

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 常量定义
TRAINING_DATA_PATH = "train.txt"
TESTING_DATA_PATH = "test.txt"
GROUND_TRUTH_PATH = "test_ground_truth.txt"
NUM_ITERATIONS = 10
REGULARIZATION_PARAM = 1e-4
RANDOM_STATE = ""
LAMBDA_VALUES_GRID = [1e-3, 1e-2, 1e-1, 1.0]
OUTPUT_CSV_PATH = ""
PREDICTION_OUTPUT_PATH = ""

# 特征字段
FEATURE_COLUMNS = ["age", "workclass", "fnlwgt", "education", "education-num", "marital-status", 
                   "occupation", "relationship", "race", "sex", "capital-gain", "capital-loss", 
                   "hours-per-week", "native-country"]
NUMERICAL_FEATURES = {"age", "fnlwgt", "education-num", "capital-gain", "capital-loss", "hours-per-week"}
CATEGORICAL_FEATURES = {"workclass", "education", "marital-status", "occupation", 
                        "relationship", "race", "sex", "native-country"}
MISSING_VALUE_MARKER = "Unknown"
HIGH_INCOME_LABEL = ">50K"
LOW_INCOME_LABEL = "<=50K"

# 数据预处理
def standardize_token(token_str: str) -> str:
    return token_str.strip().strip(".")

def extract_features_and_target(data_line: str) -> Tuple[Dict[str, Any], Optional[str]]:
    token_list = [standardize_token(item) for item in data_line.split(",")]
    token_list = [item for item in token_list if item != ""]
    
    if not token_list:
        return {}, None
    if len(token_list) not in (len(FEATURE_COLUMNS), len(FEATURE_COLUMNS) + 1):
        raise ValueError(f"列数错误: {len(token_list)} in line: {data_line[:120]}...")
    
    # 构建特征字典
    feature_dict = {}
    for idx, col_name in enumerate(FEATURE_COLUMNS):
        value = token_list[idx]
        feature_dict[col_name] = int(value) if col_name in NUMERICAL_FEATURES else (value if value not in ("?", "") else MISSING_VALUE_MARKER)
    
    # 解析标签
    target_label = None
    if len(token_list) == len(FEATURE_COLUMNS) + 1:
        raw_label = standardize_token(token_list[-1]).rstrip(".")
        if raw_label not in (HIGH_INCOME_LABEL, LOW_INCOME_LABEL):
            raise ValueError(f"未知标签: {raw_label}")
        target_label = raw_label
    
    return feature_dict, target_label

def load_dataset_from_file(file_path: str, has_labels: bool) -> Tuple[List[Dict[str, Any]], Optional[List[str]]]:
    data_rows = []
    target_labels = [] if has_labels else None
    with open(file_path, "r", encoding="utf-8") as file_handle:
        for line_content in file_handle:
            line_content = line_content.strip()
            if not line_content:
                continue
            features, label = extract_features_and_target(line_content)
            if not features:
                continue
            data_rows.append(features)
            if has_labels and label is None:
                raise ValueError(f"行中缺少标签: {line_content[:120]}...")
            if has_labels:
                target_labels.append(label)
    return data_rows, target_labels

def extract_labels_from_file(file_path: str) -> List[str]:
    extracted_labels = []
    with open(file_path, "r", encoding="utf-8") as file_handle:
        for line_content in file_handle:
            line_content = line_content.strip()
            if not line_content:
                continue
            clean_token = standardize_token(line_content)
            if clean_token in (HIGH_INCOME_LABEL, LOW_INCOME_LABEL):
                extracted_labels.append(clean_token)
                continue
            try:
                _, label = extract_features_and_target(line_content)
                if label in (HIGH_INCOME_LABEL, LOW_INCOME_LABEL):
                    extracted_labels.append(label)
                    continue
            except Exception:
                pass
            token_parts = [standardize_token(part) for part in line_content.split(",")]
            if token_parts and token_parts[-1].rstrip(".") in (HIGH_INCOME_LABEL, LOW_INCOME_LABEL):
                extracted_labels.append(token_parts[-1].rstrip("."))
                continue
            raise ValueError(f"未知标签: {line_content[:120]}")
    return extracted_labels

# 特征工程
def construct_category_vocabularies(training_data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    return {
        feature_name: sorted({str(row[feature_name]) if row[feature_name] not in ("?", "", None) else MISSING_VALUE_MARKER for row in training_data} | {MISSING_VALUE_MARKER})
        for feature_name in CATEGORICAL_FEATURES
    }

def build_feature_index_mapping(vocabulary_dict: Dict[str, List[str]]) -> Tuple[Dict[str, int], Dict[str, Tuple[int, Dict[str, int]]], int]:
    # 数值特征映射
    numerical_mapping = {feature: idx for idx, feature in enumerate(col for col in FEATURE_COLUMNS if col in NUMERICAL_FEATURES)}
    current_col = len(numerical_mapping)
    
    # 类别特征one-hot编码映射
    categorical_mapping = {}
    for categorical_feature in (col for col in FEATURE_COLUMNS if col in CATEGORICAL_FEATURES):
        value_to_index = {value: (current_col + i) for i, value in enumerate(vocabulary_dict[categorical_feature])}
        categorical_mapping[categorical_feature] = (current_col, value_to_index)
        current_col += len(vocabulary_dict[categorical_feature])
    
    return numerical_mapping, categorical_mapping, current_col

def calculate_normalization_parameters(data_rows: List[Dict[str, Any]]) -> Tuple[Dict[str, float], Dict[str, float]]:
    """计算数值特征标准化参数"""
    normalization_stats = {}
    for numeric_feature in NUMERICAL_FEATURES:
        feature_values = [float(row[numeric_feature]) for row in data_rows]
        mean_value = sum(feature_values) / len(feature_values) if feature_values else 0.0
        std_value = math.sqrt(sum((val - mean_value) ** 2 for val in feature_values) / len(feature_values)) if feature_values else 1.0
        normalization_stats[numeric_feature] = (mean_value, std_value if std_value != 0 else 1.0)
    
    return {key: val[0] for key, val in normalization_stats.items()}, {key: val[1] for key, val in normalization_stats.items()}

def transform_row_to_vector(
    data_row: Dict[str, Any],
    num_indices: Dict[str, int],
    cat_indices: Dict[str, Tuple[int, Dict[str, int]]],
    vector_dimension: int,
    mean_values: Dict[str, float],
    std_values: Dict[str, float],
) -> List[float]:
    """将数据行转换特征向量"""
    feature_vector = [0.0] * vector_dimension
    
    # 处理数值特征
    for num_feature, index in num_indices.items():
        feature_vector[index] = (float(data_row[num_feature]) - mean_values[num_feature]) / std_values[num_feature]
    
    # 处理类别特征
    for cat_feature, (start_idx, index_map) in cat_indices.items():
        value = str(data_row[cat_feature])
        if value in ("?", "", None):
            value = MISSING_VALUE_MARKER
        feature_vector[index_map.get(value, index_map[MISSING_VALUE_MARKER])] = 1.0
    
    return feature_vector

def convert_labels_to_numeric(label_list: List[str]) -> List[int]:
    """标签转换为数值形式"""
    return [1 if label == HIGH_INCOME_LABEL else -1 for label in label_list]

# 预测和评估
def make_predictions(feature_matrix: List[List[float]], weight_vector: List[float], bias_term: float) -> List[int]:
    """进行预测"""
    return [1 if sum(weight_vector[j] * sample[j] for j in range(len(weight_vector))) + bias_term >= 0 else -1 for sample in feature_matrix]

def compute_accuracy_score(true_labels: List[int], predicted_labels: List[int]) -> float:
    """计算准确率"""
    return sum(1 for actual, pred in zip(true_labels, predicted_labels) if actual == pred) / len(true_labels) if true_labels else 0.0

# 随机种子处理函数
def initialize_random_seed(seed_input) -> Tuple[int, bool]:
    if not seed_input or (isinstance(seed_input, str) and seed_input.strip() == ""):
        generated_seed = random.randint(0, 2**31 - 1)
        random.seed(generated_seed)
        np.random.seed(generated_seed)
        return generated_seed, True
    specified_seed = int(seed_input)
    random.seed(specified_seed)
    np.random.seed(specified_seed)
    return specified_seed, False

# SVM训练函数
def train_linear_svm_classifier(
    training_features: List[List[float]],
    training_targets: List[int],
    regularization_lambda: float = 1e-4,
    training_epochs: int = 10,
    random_seed: int = 42,
) -> Tuple[List[float], float, Dict[str, Any]]:
    """SGD训练SVM分类器"""
    rng = random.Random(random_seed)
    np.random.seed(random_seed)
    
    num_samples, feature_dim = len(training_features), len(training_features[0])
    weight_params = [0.0] * feature_dim
    bias_param = 0.0
    step_count = update_count = total_hinge_loss = loss_count = 0
    
    # 训练过程记录
    loss_per_epoch = []
    accuracy_per_epoch = []

    for current_epoch in range(training_epochs):
        sample_indices = list(range(num_samples))
        rng.shuffle(sample_indices)
        
        epoch_loss_sum = 0.0
        epoch_loss_count = 0
        
        for sample_idx in sample_indices:
            step_count += 1
            learning_rate = 1.0 / (regularization_lambda * step_count)
            
            # 计算预测分数
            prediction_score = sum(weight_params[j] * training_features[sample_idx][j] for j in range(feature_dim)) + bias_param
            margin_value = training_targets[sample_idx] * prediction_score
            
            # 计算hinge损失
            current_hinge_loss = max(0.0, 1.0 - margin_value) if margin_value < 1.0 else 0.0
            total_hinge_loss += current_hinge_loss
            loss_count += 1
            epoch_loss_sum += current_hinge_loss
            epoch_loss_count += 1
            
            # 参数更新
            if margin_value < 1.0:
                weight_params = [(1.0 - learning_rate * regularization_lambda) * weight_params[j] + learning_rate * training_targets[sample_idx] * training_features[sample_idx][j] for j in range(feature_dim)]
                bias_param += learning_rate * training_targets[sample_idx]
                update_count += 1
            else:
                weight_params = [(1.0 - learning_rate * regularization_lambda) * weight_params[j] for j in range(feature_dim)]
        
        # 计算训练准确率
        epoch_predictions = make_predictions(training_features, weight_params, bias_param)
        epoch_accuracy = compute_accuracy_score(training_targets, epoch_predictions)
        
        # 记录统计信息
        avg_loss = epoch_loss_sum / epoch_loss_count if epoch_loss_count > 0 else 0.0
        loss_per_epoch.append(avg_loss)
        accuracy_per_epoch.append(epoch_accuracy)
        
        print(f"Epoch {current_epoch+1}/{training_epochs}: 平均损失={avg_loss:.4f}, 训练准确率={epoch_accuracy:.4f}")
    
    return weight_params, bias_param, {
        "steps": float(step_count),
        "updates": float(update_count),
        "avg_hinge": (total_hinge_loss / loss_count) if loss_count > 0 else 0.0,
        "epoch_losses": loss_per_epoch,
        "epoch_accuracies": accuracy_per_epoch,
    }

# 保存结果
def write_predictions_to_file(output_path: str, prediction_results: List[int]) -> None:
    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write("\n".join(HIGH_INCOME_LABEL if pred == 1 else LOW_INCOME_LABEL for pred in prediction_results))

def write_detailed_results(output_path: str, lambda_value: float, predictions: List[int], ground_truth: List[int]) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["index", "lambda", "pred", "truth", "correct"])
        for idx, (pred, true_val) in enumerate(zip(predictions, ground_truth)):
            csv_writer.writerow([idx, lambda_value, 
                               HIGH_INCOME_LABEL if pred == 1 else LOW_INCOME_LABEL,
                               HIGH_INCOME_LABEL if true_val == 1 else LOW_INCOME_LABEL,
                               1 if pred == true_val else 0])

# 可视化函数
def visualize_training_process(statistics_list: List[Dict[str, Any]], lambda_list: List[float], output_file: str = "training_progress.png"):
    figure, (subplot1, subplot2) = plt.subplots(1, 2, figsize=(15, 5))
    
    # 损失曲线
    for idx, (stats, lambda_val) in enumerate(zip(statistics_list, lambda_list)):
        epoch_range = range(1, len(stats['epoch_losses']) + 1)
        subplot1.plot(epoch_range, stats['epoch_losses'], label=f'λ={lambda_val:.0e}', marker='o')
    
    subplot1.set_xlabel('训练轮数')
    subplot1.set_ylabel('平均Hinge损失')
    subplot1.set_title('训练损失变化')
    subplot1.legend()
    subplot1.grid(True, alpha=0.3)
    
    # 准确率曲线
    for idx, (stats, lambda_val) in enumerate(zip(statistics_list, lambda_list)):
        epoch_range = range(1, len(stats['epoch_accuracies']) + 1)
        subplot2.plot(epoch_range, stats['epoch_accuracies'], label=f'λ={lambda_val:.0e}', marker='s')
    
    subplot2.set_xlabel('训练轮数')
    subplot2.set_ylabel('训练准确率')
    subplot2.set_title('训练准确率变化')
    subplot2.legend()
    subplot2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"训练过程图已保存至: {output_file}")

def visualize_lambda_performance(lambda_values: List[float], accuracy_scores: List[float], output_file: str = "lambda_comparison.png"):
    """可视化不同λ值的性能对比"""
    plt.figure(figsize=(10, 6))
    
    bar_chart = plt.bar(range(len(lambda_values)), accuracy_scores, alpha=0.7, color='skyblue', edgecolor='navy')
    
    for idx, (bar, score) in enumerate(zip(bar_chart, accuracy_scores)):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.001, 
                f'{score:.4f}', ha='center', va='bottom', fontweight='bold')
    
    plt.xlabel('正则化参数 λ')
    plt.ylabel('测试准确率')
    plt.title('不同λ值的SVM测试准确率对比')
    plt.xticks(range(len(lambda_values)), [f'{val:.0e}' for val in lambda_values])
    plt.grid(True, alpha=0.3, axis='y')
    plt.ylim(0, max(accuracy_scores) * 1.1)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"λ值对比图已保存至: {output_file}")

def visualize_confusion_matrix(actual_labels: List[int], predicted_labels: List[int], lambda_parameter: float, output_file: str = "confusion_matrix.png"):
    # 计算混淆矩阵元素
    true_positive = sum(1 for actual, pred in zip(actual_labels, predicted_labels) if actual == 1 and pred == 1)
    true_negative = sum(1 for actual, pred in zip(actual_labels, predicted_labels) if actual == -1 and pred == -1)
    false_positive = sum(1 for actual, pred in zip(actual_labels, predicted_labels) if actual == -1 and pred == 1)
    false_negative = sum(1 for actual, pred in zip(actual_labels, predicted_labels) if actual == 1 and pred == -1)
    
    confusion_matrix = np.array([[true_negative, false_positive], [false_negative, true_positive]])
    
    plt.figure(figsize=(8, 6))
    plt.imshow(confusion_matrix, interpolation='nearest', cmap='Blues')
    plt.title(f'混淆矩阵 (λ={lambda_parameter:.0e})')
    plt.colorbar()
    
    class_labels = ['<=50K', '>50K']
    tick_positions = np.arange(len(class_labels))
    plt.xticks(tick_positions, class_labels)
    plt.yticks(tick_positions, class_labels)
    plt.xlabel('预测标签')
    plt.ylabel('真实标签')
    
    # 添加数值标注
    for row_idx in range(2):
        for col_idx in range(2):
            plt.text(col_idx, row_idx, f'{confusion_matrix[row_idx, col_idx]}', ha='center', va='center', 
                    color='white' if confusion_matrix[row_idx, col_idx] > confusion_matrix.max()/2 else 'black', 
                    fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    print(f"混淆矩阵已保存至: {output_file}")

def main():
    argument_parser = argparse.ArgumentParser(description="使用SGD实现线性SVM")
    argument_parser.add_argument("--train", default="", help="训练集路径")
    argument_parser.add_argument("--test", default="", help="测试集路径")
    argument_parser.add_argument("--test-labels", default="", help="测试标签路径")
    argument_parser.add_argument("--epochs", type=int, default=NUM_ITERATIONS, help="训练轮数")
    argument_parser.add_argument("--lambda", dest="lambda_reg", type=float, default=REGULARIZATION_PARAM, help="正则化系数")
    argument_parser.add_argument("--seed", default=RANDOM_STATE, help="随机种子(空表示随机生成)")
    argument_parser.add_argument("--save-preds", default=PREDICTION_OUTPUT_PATH, help="预测结果保存路径")
    argument_parser.add_argument("--grid-lambdas", default=",".join(str(val) for val in LAMBDA_VALUES_GRID),
                                help="λ网格搜索值(逗号分隔)")
    argument_parser.add_argument("--results-csv", default=OUTPUT_CSV_PATH, help="结果CSV保存路径")
    argument_parser.add_argument("--no-grid", action="store_true", help="禁用λ网格搜索")
    argument_parser.add_argument("--vary-seed-per-lambda", action="store_true", help="为每个λ使用不同随机种子")
    argument_parser.add_argument("--no-plot", action="store_true", help="禁用可视化")

    parsed_args = argument_parser.parse_args()

    # 配置参数
    training_file = parsed_args.train or TRAINING_DATA_PATH
    testing_file = parsed_args.test or TESTING_DATA_PATH
    labels_file = parsed_args.test_labels or GROUND_TRUTH_PATH
    num_epochs = parsed_args.epochs
    lambda_param = parsed_args.lambda_reg
    seed_value, was_random_seed = initialize_random_seed(parsed_args.seed)
    prediction_save_path = parsed_args.save_preds or PREDICTION_OUTPUT_PATH
    lambda_grid = [float(token) for token in parsed_args.grid_lambdas.split(",") if token.strip()]
    results_file = parsed_args.results_csv or os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_results.csv")

    print(f"配置: train={training_file}, test={testing_file}, epochs={num_epochs}, lambda={lambda_param}, seed={seed_value}")
    if not parsed_args.no_grid:
        print(f"λ搜索值: {lambda_grid}")

    # 数据加载 
    train_data, train_labels = load_dataset_from_file(training_file, has_labels=True)
    test_data, _ = load_dataset_from_file(testing_file, has_labels=False)
    test_labels = extract_labels_from_file(labels_file)
    
    if len(test_data) != len(test_labels):
        raise ValueError(f"测试集样本数({len(test_data)})与标签数({len(test_labels)})不匹配")

    # 特征工程
    category_vocabs = construct_category_vocabularies(train_data)
    num_mapping, cat_mapping, total_dims = build_feature_index_mapping(category_vocabs)
    feature_means, feature_stds = calculate_normalization_parameters(train_data)

    # 数据转换
    train_features = [transform_row_to_vector(row, num_mapping, cat_mapping, total_dims, feature_means, feature_stds) for row in train_data]
    train_targets = convert_labels_to_numeric(train_labels)
    test_features = [transform_row_to_vector(row, num_mapping, cat_mapping, total_dims, feature_means, feature_stds) for row in test_data]
    test_targets = convert_labels_to_numeric(test_labels)

    # 模型训练和评估
    if parsed_args.no_grid:
        print(f"\n开始训练 (lambda={lambda_param}, seed={seed_value})")
        trained_weights, trained_bias, training_stats = train_linear_svm_classifier(train_features, train_targets, lambda_param, num_epochs, seed_value)
        print(f"训练统计: 总步数={int(training_stats['steps'])}, 更新次数={int(training_stats['updates'])}, 平均hinge损失={training_stats['avg_hinge']:.4f}")
        
        test_predictions = make_predictions(test_features, trained_weights, trained_bias)
        test_accuracy = compute_accuracy_score(test_targets, test_predictions)
        print(f"测试准确率 (lambda={lambda_param}): {test_accuracy:.4f} ({test_accuracy*100:.2f}%)")
        
        if prediction_save_path:
            write_predictions_to_file(prediction_save_path, test_predictions)
            print(f"预测结果已保存至: {prediction_save_path}")
        
        write_detailed_results(results_file, lambda_param, test_predictions, test_targets)
        print(f"详细结果已保存至: {results_file}")
        
        # 可视化
        if not parsed_args.no_plot:
            visualize_training_process([training_stats], [lambda_param], "single_training_progress.png")
            visualize_confusion_matrix(test_targets, test_predictions, lambda_param, f"confusion_matrix_lambda_{lambda_param:.0e}.png")
    else:
        collected_stats = []
        collected_accuracies = []
        optimal_lambda = None
        optimal_accuracy = 0.0
        optimal_predictions = None
        
        for iteration, current_lambda in enumerate(lambda_grid):
            current_seed = (seed_value + iteration * 9973) if parsed_args.vary_seed_per_lambda else seed_value
            print(f"\n=== 使用 lambda={current_lambda}, seed={current_seed} 进行训练 ===")
            
            weights, bias, stats = train_linear_svm_classifier(train_features, train_targets, current_lambda, num_epochs, current_seed)
            print(f"训练统计: 总步数={int(stats['steps'])}, 更新次数={int(stats['updates'])}, 平均hinge损失={stats['avg_hinge']:.4f}")
            
            predictions = make_predictions(test_features, weights, bias)
            accuracy = compute_accuracy_score(test_targets, predictions)
            print(f"测试准确率: {accuracy:.4f} ({accuracy*100:.2f}%)")
            
            collected_stats.append(stats)
            collected_accuracies.append(accuracy)
            
            if accuracy > optimal_accuracy:
                optimal_accuracy = accuracy
                optimal_lambda = current_lambda
                optimal_predictions = predictions
        
        print(f"\n=== 网格搜索结果总结 ===")
        for lam_val, acc_val in zip(lambda_grid, collected_accuracies):
            print(f"λ={lam_val:.0e}: 测试准确率={acc_val:.4f}")
        print(f"最佳λ={optimal_lambda:.0e}, 最佳准确率={optimal_accuracy:.4f}")
        
        if prediction_save_path and optimal_predictions is not None:
            write_predictions_to_file(prediction_save_path, optimal_predictions)
            print(f"最佳模型预测结果已保存至: {prediction_save_path}")
        
        # 保存最终结果
        if optimal_predictions is not None:
            write_detailed_results(results_file, optimal_lambda, optimal_predictions, test_targets)
            print(f"最佳模型详细结果已保存至: {results_file}")
        
        # 可视化
        if not parsed_args.no_plot:
            visualize_training_process(collected_stats, lambda_grid, "grid_training_progress.png")
            visualize_lambda_performance(lambda_grid, collected_accuracies, "lambda_comparison.png")
            if optimal_predictions is not None:
                visualize_confusion_matrix(test_targets, optimal_predictions, optimal_lambda, f"best_confusion_matrix.png")

if __name__ == "__main__":
    main()