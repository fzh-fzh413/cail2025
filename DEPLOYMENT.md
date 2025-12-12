# API 服务部署指南

本指南将帮助您将 API 服务部署到域名上，使其可以通过公网访问。

## 部署架构

```
域名 (example.com)
    ↓
Nginx 反向代理 (80/443端口)
    ↓
Gunicorn (Flask应用，端口8000)
    ↓
Python app.py
```

## 方案一：使用云服务器 + Nginx（推荐）

### 1. 准备云服务器

推荐使用：
- **阿里云 ECS**
- **腾讯云 CVM**
- **AWS EC2**
- **其他云服务商**

**服务器要求：**
- Ubuntu 20.04+ 或 CentOS 7+
- 至少 2GB 内存
- 公网 IP 地址
- 开放 80、443 端口（HTTP/HTTPS）

### 2. 服务器环境配置

#### 2.1 连接到服务器

```bash
ssh username@your-server-ip
```

#### 2.2 安装 Python 和必要工具

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx git -y
```

**CentOS/RHEL:**
```bash
sudo yum update -y
sudo yum install python3 python3-pip nginx git -y
```

#### 2.3 上传代码到服务器

**方式1：使用 git**
```bash
cd /opt
git clone your-repo-url
cd your-project
```

**方式2：使用 scp 上传**
```bash
# 在本地执行
scp -r /path/to/your/project username@your-server-ip:/opt/api-service
```

#### 2.4 创建虚拟环境并安装依赖

```bash
cd /opt/api-service  # 或您的项目路径
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn  # 生产环境 WSGI 服务器
```

### 3. 配置环境变量

```bash
# 创建环境变量文件
sudo nano /etc/environment
```

添加：
```
DASHSCOPE_API_KEY=your-api-key-here
```

或者创建 `.env` 文件：
```bash
cd /opt/api-service
nano .env
```

内容：
```
DASHSCOPE_API_KEY=your-api-key-here
```

### 4. 使用 Gunicorn 运行应用

#### 4.1 测试 Gunicorn

```bash
cd /opt/api-service
source venv/bin/activate
gunicorn -w 4 -b 127.0.0.1:8000 app:app
```

#### 4.2 创建 systemd 服务（推荐）

创建服务文件：
```bash
sudo nano /etc/systemd/system/api-service.service
```

内容：
```ini
[Unit]
Description=Legal AI API Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/api-service
Environment="PATH=/opt/api-service/venv/bin"
Environment="DASHSCOPE_API_KEY=your-api-key-here"
ExecStart=/opt/api-service/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable api-service
sudo systemctl start api-service
sudo systemctl status api-service
```

### 5. 配置 Nginx 反向代理

#### 5.1 安装 Nginx（如果未安装）

```bash
sudo apt install nginx -y  # Ubuntu
# 或
sudo yum install nginx -y  # CentOS
```

#### 5.2 创建 Nginx 配置

```bash
sudo nano /etc/nginx/sites-available/api-service
```

内容：
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;  # 替换为您的域名

    # 允许较大的请求体（如果需要）
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置（LLM 调用可能需要较长时间）
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

#### 5.3 启用配置

```bash
# Ubuntu/Debian
sudo ln -s /etc/nginx/sites-available/api-service /etc/nginx/sites-enabled/
sudo nginx -t  # 测试配置
sudo systemctl restart nginx

# CentOS (配置文件路径不同)
sudo cp /etc/nginx/sites-available/api-service /etc/nginx/conf.d/api-service.conf
sudo nginx -t
sudo systemctl restart nginx
```

### 6. 配置域名 DNS

在您的域名管理平台（如阿里云、腾讯云）添加 DNS 记录：

```
类型: A
主机记录: api (或 @)
记录值: 您的服务器公网 IP
TTL: 600
```

这样您就可以通过 `http://api.yourdomain.com/model` 访问 API。

### 7. 配置 SSL 证书（HTTPS，推荐）

#### 使用 Let's Encrypt 免费证书

```bash
sudo apt install certbot python3-certbot-nginx -y  # Ubuntu
# 或
sudo yum install certbot python3-certbot-nginx -y  # CentOS

# 获取证书
sudo certbot --nginx -d api.yourdomain.com

# 自动续期测试
sudo certbot renew --dry-run
```

证书安装后，Nginx 会自动配置 HTTPS。

### 8. 配置防火墙

```bash
# Ubuntu (ufw)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# CentOS (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 方案二：使用 Docker 部署（可选）

### 1. 创建 Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . .

ENV DASHSCOPE_API_KEY=""
ENV PORT=8000

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

### 2. 构建和运行

```bash
docker build -t legal-ai-api .
docker run -d -p 8000:8000 \
  -e DASHSCOPE_API_KEY="your-api-key" \
  --name legal-ai-api \
  legal-ai-api
```

## 方案三：使用云平台 Serverless（快速部署）

### 1. 阿里云函数计算

- 需要修改代码以适配函数计算格式
- 无需管理服务器
- 按调用量计费

### 2. 腾讯云 SCF

类似阿里云函数计算

### 3. Vercel / Railway / Render

这些平台支持直接部署 Flask 应用，更简单但可能有成本限制。

## 验证部署

### 1. 测试 API

```bash
curl -X POST http://api.yourdomain.com/model \
  -H "Content-Type: application/json" \
  -d '{"id": 0, "query": "测试问题"}'
```

### 2. 检查服务状态

```bash
# 检查 Gunicorn 服务
sudo systemctl status api-service

# 检查 Nginx
sudo systemctl status nginx

# 查看日志
sudo journalctl -u api-service -f
sudo tail -f /var/log/nginx/error.log
```

## 性能优化建议

1. **增加工作进程数**：根据服务器 CPU 核心数调整 `-w` 参数
2. **使用 Redis 缓存**：缓存常见查询结果
3. **CDN 加速**：如果 API 响应较大
4. **负载均衡**：多台服务器部署

## 提交的 JSON 文件格式

部署完成后，提交的 JSON 文件应为：

```json
{
  "api_key": "https://api.yourdomain.com/model"
}
```

或 HTTP（不推荐，但可用）：

```json
{
  "api_key": "http://api.yourdomain.com/model"
}
```

## 常见问题

### 1. 502 Bad Gateway

- 检查 Gunicorn 是否运行：`sudo systemctl status api-service`
- 检查端口是否正确：`sudo netstat -tlnp | grep 8000`
- 查看错误日志：`sudo journalctl -u api-service -n 50`

### 2. 超时错误

- 增加 Nginx 超时时间（已在配置中设置）
- 检查服务器资源使用情况

### 3. 连接被拒绝

- 检查防火墙设置
- 确保端口已开放
- 检查安全组规则（云服务器）

## 监控和维护

### 1. 日志查看

```bash
# 应用日志
sudo journalctl -u api-service -f

# Nginx 访问日志
sudo tail -f /var/log/nginx/access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/error.log
```

### 2. 重启服务

```bash
sudo systemctl restart api-service
sudo systemctl restart nginx
```

### 3. 更新代码

```bash
cd /opt/api-service
git pull  # 或重新上传文件
sudo systemctl restart api-service
```

## 安全建议

1. ✅ 使用 HTTPS（SSL 证书）
2. ✅ 定期更新系统和依赖
3. ✅ 使用强密码
4. ✅ 限制 SSH 访问（仅允许特定 IP）
5. ✅ 定期备份数据
6. ✅ 监控 API 使用情况，防止滥用




