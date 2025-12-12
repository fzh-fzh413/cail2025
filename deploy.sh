#!/bin/bash
# API 服务快速部署脚本
# 使用方法: chmod +x deploy.sh && ./deploy.sh

set -e

echo "================================"
echo "法律AI API 服务部署脚本"
echo "================================"

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo "请使用 sudo 运行此脚本"
    exit 1
fi

# 配置变量（根据实际情况修改）
PROJECT_DIR="/opt/api-service"
SERVICE_NAME="api-service"
DOMAIN_NAME="api.yourdomain.com"  # 替换为您的域名
APP_PORT=8000
NGINX_CONFIG="/etc/nginx/sites-available/api-service"

echo "1. 安装必要软件..."
apt-get update
apt-get install -y python3 python3-pip python3-venv nginx git

echo "2. 创建项目目录..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 如果目录不为空，询问是否继续
if [ "$(ls -A $PROJECT_DIR)" ]; then
    read -p "目录 $PROJECT_DIR 不为空，是否继续？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "3. 创建虚拟环境..."
python3 -m venv venv
source venv/bin/activate

echo "4. 安装依赖..."
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install gunicorn
else
    echo "警告: 未找到 requirements.txt，安装基础依赖..."
    pip install flask flask-cors dashscope gunicorn requests tqdm
fi

echo "5. 设置环境变量..."
read -p "请输入 DASHSCOPE_API_KEY: " API_KEY
export DASHSCOPE_API_KEY=$API_KEY

echo "6. 创建 systemd 服务..."
cat > /etc/systemd/system/${SERVICE_NAME}.service <<EOF
[Unit]
Description=Legal AI API Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
Environment="DASHSCOPE_API_KEY=$API_KEY"
ExecStart=$PROJECT_DIR/venv/bin/gunicorn -w 4 -b 127.0.0.1:$APP_PORT app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "7. 启动服务..."
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl start ${SERVICE_NAME}

echo "8. 配置 Nginx..."
cat > $NGINX_CONFIG <<EOF
server {
    listen 80;
    server_name $DOMAIN_NAME;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
EOF

ln -sf $NGINX_CONFIG /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

echo "9. 配置防火墙..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo "================================"
echo "部署完成！"
echo "================================"
echo "请确保："
echo "1. 域名 $DOMAIN_NAME 已解析到本服务器 IP"
echo "2. 配置 SSL 证书（可选）: sudo certbot --nginx -d $DOMAIN_NAME"
echo "3. 测试 API: curl -X POST http://$DOMAIN_NAME/model -H 'Content-Type: application/json' -d '{\"id\":0,\"query\":\"test\"}'"
echo ""
echo "服务状态: sudo systemctl status $SERVICE_NAME"
echo "查看日志: sudo journalctl -u $SERVICE_NAME -f"




