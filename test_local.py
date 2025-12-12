# encoding=utf-8
"""
本地测试脚本 - 使用 localhost 而不是 ngrok
这样可以避免 SSL 问题
使用方法：python test_local.py
"""
import requests
import json

# 使用本地地址，避免 ngrok SSL 问题
api_key = "http://localhost:5000/model"  # 使用 HTTP，不通过 ngrok
data = []

try:
    with open(r"C:\Users\fzh\Desktop\pythonProject1\stage1_test.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    
    print(f"读取到 {len(data)} 条测试数据")
    print(f"正在发送请求到: {api_key}")
    
    response = requests.post(api_key, json=data, timeout=300)
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print("模型处理结果:", result)
    
except Exception as e:
    print(f"错误: {e}")
    print("\n请确保：")
    print("1. Flask 服务正在运行 (python app.py)")
    print("2. 服务运行在 localhost:5000")


