import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import re

matplotlib.use('TkAgg')
# 1. 读取数据
file_path = r"C:\Users\fzh\Desktop\zebra-CoT\train-00000-of-00001.csv"
df = pd.read_csv(file_path)

# 假设 COT 在 'text' 或 'answer' 字段里（请根据实际字段名修改）
text_col = None
for col in df.columns:
    if 'cot' in col.lower() or 'text' in col.lower() or 'answer' in col.lower():
        text_col = col
        break
if not text_col:
    raise ValueError("未找到包含 COT 的列，请检查文件列名。")

# 2. 计算冗余度（用 TF-IDF + Cosine Similarity）
vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizer.fit_transform(df[text_col].astype(str))
similarity_matrix = cosine_similarity(tfidf_matrix)

# 只取上三角非对角线部分
redundancy_scores = similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)]
avg_redundancy = np.mean(redundancy_scores)

# 3. 计算逻辑一致性
def logic_consistency(text):
    steps = re.findall(r'\bStep\s*(\d+)|\b(\d+)\.', text)
    nums = [int(num) for s1, s2 in steps for num in (s1, s2) if num.isdigit()]
    if not nums:
        return 0.5
    return 1.0 if nums == sorted(nums) else 0.0

logic_scores = df[text_col].astype(str).apply(logic_consistency)
avg_logic_score = logic_scores.mean()

# 4. 可视化结果（冗余度 + 逻辑一致性）
fig, axs = plt.subplots(1, 2, figsize=(10, 4))

sns.histplot(redundancy_scores, bins=30, ax=axs[0], kde=True, color="skyblue")
axs[0].set_title(f"Redundancy distribution\nAverage redundancy: {avg_redundancy:.3f}")
axs[0].set_xlabel("Cosine Similarity")

sns.histplot(logic_scores, bins=3, ax=axs[1], color="lightgreen")
axs[1].set_title(f"Logical consistency distribution\nAverage consistency: {avg_logic_score:.3f}")
axs[1].set_xlabel("Logical consistency score")

plt.tight_layout()
plt.show()

# 5. 生成冗余样本热力图
# 取相似度最高的前 N 对（排除自己与自己的对比）
N = 10
pairs = []
for i in range(len(df)):
    for j in range(i+1, len(df)):
        pairs.append((i, j, similarity_matrix[i, j]))

pairs = sorted(pairs, key=lambda x: x[2], reverse=True)[:N]

# 提取对应的相似度矩阵
indices = sorted(set([i for i, j, s in pairs] + [j for i, j, s in pairs]))
sub_matrix = similarity_matrix[np.ix_(indices, indices)]
labels = [f"idx_{i}" for i in indices]

plt.figure(figsize=(8, 6))
sns.heatmap(sub_matrix, xticklabels=labels, yticklabels=labels,
            cmap="Reds", annot=True, fmt=".2f", cbar=True)
plt.title(f"The top {N} pairs with the highest similarity in the sample heatmap")
plt.show()

# 6. 输出冗余对样本内容
print(f"\n相似度最高的前 {N} 对样本：")
for i, j, score in pairs:
    print(f"[{i}] vs [{j}] 相似度={score:.3f}")
    print(f"样本 {i}: {df[text_col].iloc[i][:80]}...")
    print(f"样本 {j}: {df[text_col].iloc[j][:80]}...\n")
