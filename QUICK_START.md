# 快速部署指南

## 最简单的方法：使用云服务器 + 自动部署脚本

### 前提条件
1. 一台有公网 IP 的云服务器（阿里云、腾讯云等）
2. 一个域名（可选，也可以直接用 IP）
3. SSH 访问权限

### 步骤 1: 连接服务器

```bash
ssh username@your-server-ip
```

### 步骤 2: 上传代码

**方式 A：使用 git**
```bash
cd /opt
git clone your-repo-url api-service
cd api-service
```

**方式 B：使用 scp（在本地执行）**
```bash
scp -r /path/to/your/project username@your-server-ip:/opt/api-service
```

### 步骤 3: 运行自动部署脚本

```bash
cd /opt/api-service
chmod +x deploy.sh
sudo ./deploy.sh
```

脚本会引导您完成：
- 安装依赖
- 配置环境变量
- 创建系统服务
- 配置 Nginx

### 步骤 4: 配置域名（如果有）

在域名管理平台添加 A 记录：
- 主机记录：`api`（或 `@`）
- 记录值：服务器公网 IP

### 步骤 5: 配置 SSL（推荐）

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d api.yourdomain.com
```

### 步骤 6: 测试

```bash
curl -X POST https://api.yourdomain.com/model \
  -H "Content-Type: application/json" \
  -d '{"id": 0, "query": "测试问题"}'
```

## 手动部署（不使用脚本）

### 1. 安装依赖

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx -y
```

### 2. 创建虚拟环境

```bash
cd /opt/api-service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

### 3. 设置环境变量

```bash
export DASHSCOPE_API_KEY="your-api-key"
# 或者添加到 /etc/environment
```

### 4. 测试运行

```bash
gunicorn -w 4 -b 127.0.0.1:8000 app:app
```

### 5. 创建系统服务

复制 `api-service.service.example` 到 `/etc/systemd/system/api-service.service`，修改路径和 API Key，然后：

```bash
sudo systemctl daemon-reload
sudo systemctl enable api-service
sudo systemctl start api-service
```

### 6. 配置 Nginx

复制 `nginx.conf.example` 到 `/etc/nginx/sites-available/api-service`，修改域名，然后：

```bash
sudo ln -s /etc/nginx/sites-available/api-service /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 没有域名怎么办？

### 方案 1: 直接使用 IP 地址

```bash
# 在 Nginx 配置中，将 server_name 改为服务器 IP 或使用 _（匹配所有）
server_name _;
```

提交的 JSON：
```json
{
  "api_key": "http://your-server-ip:80/model"
}
```

**注意：** 可能需要开放防火墙端口，并确保云服务器安全组允许 80 端口访问。

### 方案 2: 使用免费域名

- **Freenom** (免费 .tk, .ml 域名)
- **DuckDNS** (免费动态域名)
- 某些云服务商提供免费测试域名

### 方案 3: 使用内网穿透（仅用于测试）

- **ngrok**: `ngrok http 5000`
- **frp**
- **花生壳**

## 常用命令

```bash
# 查看服务状态
sudo systemctl status api-service

# 重启服务
sudo systemctl restart api-service

# 查看日志
sudo journalctl -u api-service -f

# 测试 API
curl -X POST http://your-domain/model \
  -H "Content-Type: application/json" \
  -d '{"id":0,"query":"test"}'
```

## 提交格式

部署成功后，创建 `submit.json`：

```json
{
  "api_key": "https://api.yourdomain.com/model"
}
```

或使用 IP：

```json
{
  "api_key": "http://your-server-ip/model"
}
```




