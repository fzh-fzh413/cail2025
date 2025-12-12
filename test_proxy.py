# encoding=utf-8
"""
测试代理脚本 - 用于处理 ngrok SSL 问题
这个脚本可以作为本地代理，处理 ngrok 的 SSL 问题
"""
import requests
import json
import urllib3

# 禁用 SSL 警告（仅用于测试）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 读取原始测试数据
api_key = "https://apperceptive-postmuscular-johnette.ngrok-free.dev/model"
data = []

try:
    with open(r"C:\Users\fzh\Desktop\pythonProject1\stage1_test.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            data.append(json.loads(line))
    
    print(f"读取到 {len(data)} 条测试数据")
    
    # 尝试添加 ngrok 需要的 headers
    headers = {
        'ngrok-skip-browser-warning': 'true',
        'Content-Type': 'application/json'
    }
    
    print(f"正在发送请求到: {api_key}")
    
    # 使用 verify=False 来绕过 SSL 验证（仅用于测试）
    response = requests.post(
        api_key, 
        json=data, 
        headers=headers,
        verify=False,  # 禁用 SSL 验证（仅用于测试）
        timeout=300  # 5分钟超时
    )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print("模型处理结果:", result)
    
except requests.exceptions.SSLError as e:
    print(f"SSL 错误: {e}")
    print("\n建议解决方案：")
    print("1. 重新启动 ngrok（停止并重新运行 ngrok http 5000）")
    print("2. 使用本地测试（将 api_key 改为 http://localhost:5000/model）")
    print("3. 使用其他内网穿透工具（如 localtunnel 或 cloudflared）")
except Exception as e:
    print(f"错误: {e}")


