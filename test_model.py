import requests
import json
api_key="https://apperceptive-postmuscular-johnette.ngrok-free.dev/model"
data = []
with open(r"C:\Users\fzh\Desktop\pythonProject1\stage1_test.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        data.append(json.loads(line))
response = requests.post(api_key, json=data)
result = response.json()
print("模型处理结果:", result)