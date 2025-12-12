# encoding=utf-8
"""
启动脚本：同时启动 Flask 服务和代理服务器
用于将 localhost 请求转发到 ngrok
"""
import subprocess
import sys
import os
import time
import threading

def start_flask_app():
    """在后台启动 Flask 应用"""
    # 使用环境变量指定 Flask 运行在不同的端口（如 5001）
    env = os.environ.copy()
    env['PORT'] = '5001'
    env['HOST'] = '127.0.0.1'
    
    print("启动 Flask 应用在端口 5001...")
    subprocess.run([sys.executable, 'app.py'], env=env)

def start_proxy_server():
    """启动代理服务器"""
    env = os.environ.copy()
    env['NGROK_URL'] = 'https://apperceptive-postmuscular-johnette.ngrok-free.dev'
    env['PROXY_PORT'] = '5000'
    
    print("启动代理服务器在端口 5000...")
    subprocess.run([sys.executable, 'proxy_server.py'], env=env)

if __name__ == '__main__':
    print("=" * 50)
    print("启动服务和代理服务器")
    print("=" * 50)
    
    # 由于需要在两个端口运行，建议手动操作：
    print("\n请按以下步骤操作：")
    print("\n步骤 1: 启动 Flask 应用（在一个终端）")
    print("  设置环境变量: $env:PORT=5001")
    print("  运行: python app.py")
    print("\n步骤 2: 启动代理服务器（在另一个终端）")
    print("  设置环境变量: $env:NGROK_URL='您的ngrok地址'")
    print("  运行: python proxy_server.py")
    print("\n步骤 3: 运行测试")
    print("  运行: python test_local.py")

