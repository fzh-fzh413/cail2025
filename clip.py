import torch
import clip
from PIL import Image
import pandas as pd
import matplotlib.pyplot as plt
from torchvision.transforms import Compose
import os
from tqdm import tqdm

# 设置设备
device = "cuda" if torch.cuda.is_available() else "cpu"

# 加载模型
model, preprocess = clip.load("ViT-B/32", device=device)

# 加载CSV文件
df = pd.read_csv(r"C:\Users\fzh\Desktop\zebra-CoT\01.csv")  # 注意：请确保路径正确

similarities = []

# 遍历每一对图像-文本
for idx, row in tqdm(df.iterrows(), total=len(df)):
    image_path, text = row['image'], row['text']

    if not os.path.exists(image_path):
        print(f"[Warning] Image not found: {image_path}")
        similarities.append(float('nan'))
        continue

    # 加载和预处理图像
    image = preprocess(Image.open(image_path).convert("RGB")).unsqueeze(0).to(device)
    text_token = clip.tokenize([text]).to(device)

    with torch.no_grad():
        image_feat = model.encode_image(image)
        text_feat = model.encode_text(text_token)

        image_feat /= image_feat.norm(dim=-1, keepdim=True)
        text_feat /= text_feat.norm(dim=-1, keepdim=True)

        similarity = (100.0 * image_feat @ text_feat.T).item()
        similarities.append(similarity)

# 添加结果到DataFrame
df['similarity'] = similarities

# 保存结果为CSV
df.to_csv("clip_similarity_results.csv", index=False)
print("结果保存到 clip_similarity_results.csv")

# 可视化相似度（柱状图）
plt.figure(figsize=(10, 6))
plt.barh(range(len(df)), df['similarity'], color='skyblue')
plt.yticks(range(len(df)), [f"{os.path.basename(p)}\n{text[:30]}..." for p, text in zip(df['image'], df['text'])])
plt.xlabel("CLIP Similarity Score")
plt.title("CLIP 图像-文本对齐性评估")
plt.tight_layout()
plt.savefig("clip_similarity_visualization.png", dpi=300)
plt.show()
