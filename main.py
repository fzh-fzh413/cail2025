# 这是一个示例 Python 脚本。

# 按 Shift+F10 执行或将其替换为您的代码。
# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。


# import pandas as pd
#  import pyarrow.parquet as pq
# import pyarrow.csv as pc

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('TkAgg')
# 加载 CSV 文件
df = pd.read_csv(r"C:\Users\fzh\Desktop\zebra-CoT\train-00000-of-00001.csv")

# 添加推理长度和步骤数量
df['reasoning_length'] = df['Text Reasoning Trace'].apply(len)
df['reasoning_steps'] = df['Text Reasoning Trace'].str.count("THOUGHT")

# 可视化推理长度分布
plt.figure(figsize=(8, 5))
plt.hist(df['reasoning_length'], bins=30, color='skyblue', edgecolor='black')
plt.title("Text Reasoning Trace Length Distribution")
plt.xlabel("Length (characters)")
plt.ylabel("Number of Samples")
plt.grid(True)
plt.tight_layout()
plt.show()



# 访问 https://www.jetbrains.com/help/pycharm/ 获取 PyCharm 帮助
