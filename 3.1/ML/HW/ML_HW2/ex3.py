import matplotlib.pyplot as plt
import numpy as np

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 根据练习2的数据计算精度和召回率
# 排名: doc1(1), doc2(1), doc3(1), doc4(0), doc5(1), doc8(0), doc7(1), doc6(1), doc9(0), doc10(1)
# 总相关文档数: 7

# 计算各个位置的累计精度和召回率
positions = []
precisions = []
recalls = []
cumulative_relevant = 0
total_relevant = 7

# 文档相关性 (1表示相关，0表示不相关)
relevance = [1, 1, 1, 0, 1, 0, 1, 1, 0, 1]
doc_names = ['doc1', 'doc2', 'doc3', 'doc4', 'doc5', 'doc8', 'doc7', 'doc6', 'doc9', 'doc10']

for i, rel in enumerate(relevance):
    cumulative_relevant += rel
    precision = cumulative_relevant / (i + 1)
    recall = cumulative_relevant / total_relevant
    
    positions.append(i + 1)
    precisions.append(precision)
    recalls.append(recall)
    
    print(f"位置 {i+1}: {doc_names[i]}({rel}), 累计相关: {cumulative_relevant}, "
          f"精度: {precision:.3f}, 召回率: {recall:.3f}")

# 绘制精度-召回率曲线
plt.figure(figsize=(10, 8))

# 绘制PR曲线
plt.plot(recalls, precisions, 'b-o', linewidth=2, markersize=8, label='PR曲线')

# 添加数据点标注
for i, (r, p) in enumerate(zip(recalls, precisions)):
    plt.annotate(f'pos{i+1}\n({r:.3f},{p:.3f})', 
                xy=(r, p), xytext=(5, 5), 
                textcoords='offset points',
                fontsize=9, alpha=0.7)

# 设置图表属性
plt.xlabel('召回率 (Recall)', fontsize=12)
plt.ylabel('精度 (Precision)', fontsize=12)
plt.title('练习2排名结果的精度-召回率曲线', fontsize=14, fontweight='bold')
plt.grid(True, alpha=0.3)
plt.legend()

# 设置坐标轴范围
plt.xlim(0, 1.1)
plt.ylim(0, 1.1)

# 添加理想曲线对比（水平线在精度=1.0处，直到召回率=1.0）
ideal_recalls = [0, 1.0]
ideal_precisions = [1.0, 7/10]  # 最后精度受限于相关文档比例
plt.plot(ideal_recalls, ideal_precisions, 'r--', alpha=0.5, label='理想曲线')

plt.legend()
plt.tight_layout()
plt.show()

# 打印详细的计算结果表格
print("\n详细计算结果表格:")
print("=" * 80)
print(f"{'排名位置':<8} {'文档':<8} {'相关性':<6} {'累计相关':<8} {'精度':<10} {'召回率':<10}")
print("-" * 80)

cumulative_relevant = 0
for i, (doc, rel) in enumerate(zip(doc_names, relevance)):
    cumulative_relevant += rel
    precision = cumulative_relevant / (i + 1)
    recall = cumulative_relevant / total_relevant
    print(f"{i+1:<8} {doc:<8} {rel:<6} {cumulative_relevant:<8} {precision:<10.3f} {recall:<10.3f}")

# 计算曲线下面积 (AUC-PR)
auc_pr = 0
for i in range(1, len(recalls)):
    auc_pr += (recalls[i] - recalls[i-1]) * precisions[i]
print(f"\nPR曲线下面积 (AUC-PR): {auc_pr:.3f}")