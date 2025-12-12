# encoding=utf-8
"""
本地代理服务器 - 用于解决 ngrok SSL 问题
监听 localhost，将请求转发到 ngrok URL，并处理 SSL 问题
配合 hosts 文件使用，可以拦截 test_model.py 对 ngrok 的请求
"""
from flask import Flask, request, jsonify
import requests
import os
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# 配置：您的 ngrok URL（从这里读取环境变量或直接修改）
NGROK_URL = os.getenv("NGROK_URL", "https://apperceptive-postmuscular-johnette.ngrok-free.dev")

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def proxy(path):
    """
    代理所有请求到 ngrok URL
    """
    try:
        # 构建目标 URL
        target_url = f"{NGROK_URL}/{path}" if path else NGROK_URL
        
        # 获取原始请求的 headers
        headers = dict(request.headers)
        
        # 添加 ngrok 需要的 headers
        headers['ngrok-skip-browser-warning'] = 'true'
        
        # 移除可能导致问题的 headers
        headers.pop('Host', None)
        headers.pop('Content-Length', None)
        
        # 获取请求体
        if request.is_json:
            json_data = request.get_json()
        else:
            json_data = None
        
        if request.data:
            data = request.data
        else:
            data = None
        
        # 转发请求到 ngrok
        try:
            response = requests.request(
                method=request.method,
                url=target_url,
                headers=headers,
                json=json_data,
                data=data,
                params=request.args,
                verify=False,  # 禁用 SSL 验证（仅用于测试）
                timeout=300  # 5分钟超时
            )
            
            # 返回响应
            return (
                response.content,
                response.status_code,
                [(k, v) for k, v in response.headers.items() 
                 if k.lower() not in ['content-encoding', 'transfer-encoding', 'content-length']]
            )
        except requests.exceptions.SSLError as e:
            # SSL 错误处理
            return jsonify({
                "error": "SSL 错误",
                "message": str(e),
                "suggestion": "请重新启动 ngrok 或检查 ngrok URL 是否正确"
            }), 500
        except Exception as e:
            return jsonify({
                "error": "代理请求失败",
                "message": str(e)
            }), 500
            
    except Exception as e:
        return jsonify({
            "error": "代理错误",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("本地代理服务器")
    print("=" * 60)
    print(f"监听地址: http://127.0.0.1:5000")
    print(f"转发目标: {NGROK_URL}")
    print("=" * 60)
    print("重要说明：")
    print("1. 请确保 Flask 应用运行在端口 5001")
    print("2. 请确保 ngrok 指向端口 5001: ngrok http 5001")
    print("3. 修改 hosts 文件，将 ngrok 域名指向 127.0.0.1")
    print("4. 刷新 DNS: ipconfig /flushdns")
    print("5. 然后运行: python test_model.py")
    print("=" * 60)
    
    port = int(os.getenv("PROXY_PORT", 5000))
    app.run(host='127.0.0.1', port=port, debug=False)

