# 无服务器免费部署方案

如果您没有自己的服务器，可以使用以下免费方案来部署 API 服务。

## 方案一：内网穿透工具（最简单快速）⭐推荐

### 1. ngrok（最推荐，5分钟搞定）

**优点：** 免费、简单、提供 HTTPS

**步骤：**

1. 注册 ngrok 账号：https://ngrok.com/

2. 下载 ngrok（Windows）：
   - 访问 https://ngrok.com/download
   - 下载 Windows 版本
   - 解压到任意目录

3. 获取 authtoken（登录后获取）：
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

4. 启动本地 Flask 服务：
   ```bash
   python app.py
   ```

5. 在另一个终端启动 ngrok：
   ```bash
   ngrok http 5000
   ```

6. 获取公网 URL：
   ```
   示例：https://abc123.ngrok-free.app
   ```

7. 提交的 JSON：
   ```json
   {
     "api_key": "https://abc123.ngrok-free.app/model"
   }
   ```

**注意事项：**
- 免费版每次重启 URL 会变化（可付费购买固定域名）
- 免费版有请求数限制，但测试足够用
- 本地电脑需要保持运行

---

### 2. Cloudflare Tunnel (cloudflared)

**优点：** 完全免费、稳定、可设置固定域名

1. 下载 cloudflared：https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/

2. 登录：
   ```bash
   cloudflared tunnel login
   ```

3. 创建隧道：
   ```bash
   cloudflared tunnel create my-api
   ```

4. 运行隧道：
   ```bash
   cloudflared tunnel --url http://localhost:5000
   ```

---

### 3. localtunnel

**优点：** 无需注册，直接使用

```bash
# 安装
npm install -g localtunnel

# 运行（本地先启动 Flask）
python app.py

# 在另一个终端
lt --port 5000
```

---

### 4. Serveo (SSH 隧道)

**优点：** 无需安装，只要有 SSH

```bash
ssh -R 80:localhost:5000 serveo.net
```

---

## 方案二：免费云平台部署（更稳定）⭐⭐最推荐

### 1. Render（推荐）⭐

**优点：** 完全免费、提供 HTTPS、支持 Python、自动部署

**步骤：**

1. 注册 Render：https://render.com/

2. 创建 `render.yaml` 文件：
   ```yaml
   services:
     - type: web
       name: legal-ai-api
       env: python
       buildCommand: pip install -r requirements.txt
       startCommand: gunicorn app:app
       envVars:
         - key: DASHSCOPE_API_KEY
           value: your-api-key-here
         - key: PORT
           value: 8000
   ```

3. 创建 Procfile：
   ```
   web: gunicorn app:app
   ```

4. 修改 `app.py` 的启动方式（已支持 PORT 环境变量，无需修改）

5. 在 Render 控制台：
   - 点击 "New +" → "Web Service"
   - 连接 GitHub 仓库（或手动上传）
   - 设置环境变量 `DASHSCOPE_API_KEY`
   - 点击部署

6. 获取 URL：
   ```
   示例：https://legal-ai-api.onrender.com/model
   ```

**免费额度：**
- 750 小时/月（足够使用）
- 自动休眠（15分钟无请求后休眠，首次请求会慢）

---

### 2. Railway

**优点：** 免费额度充足、部署简单

1. 注册 Railway：https://railway.app/

2. 连接 GitHub 仓库

3. 设置环境变量 `DASHSCOPE_API_KEY`

4. Railway 会自动检测 Python 并部署

**免费额度：** $5/月免费额度

---

### 3. Fly.io

**优点：** 全球边缘部署、免费额度充足

1. 注册 Fly.io：https://fly.io/

2. 安装 flyctl：
   ```bash
   # Windows PowerShell
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

3. 创建 `fly.toml`：
   ```toml
   app = "legal-ai-api"
   primary_region = "iad"
   
   [build]
   
   [env]
     PORT = "8080"
   
   [[services]]
     internal_port = 8080
     protocol = "tcp"
     
     [[services.ports]]
       port = 80
       handlers = ["http"]
     
     [[services.ports]]
       port = 443
       handlers = ["tls", "http"]
   ```

4. 部署：
   ```bash
   flyctl launch
   flyctl secrets set DASHSCOPE_API_KEY=your-api-key
   flyctl deploy
   ```

**免费额度：** 3 个共享 CPU、256MB RAM、3GB 存储

---

### 4. PythonAnywhere

**优点：** 专门为 Python 设计、完全免费

1. 注册：https://www.pythonanywhere.com/

2. 上传代码文件

3. 创建 Web App，选择 Flask

4. 设置环境变量和依赖

**免费额度：** 限制较多，但基本够用

---

## 方案三：云函数 Serverless

### 1. Vercel（推荐，最简单）

1. 安装 Vercel CLI：
   ```bash
   npm install -g vercel
   ```

2. 创建 `vercel.json`：
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "app.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "app.py"
       }
     ]
   }
   ```

3. 部署：
   ```bash
   vercel
   vercel env add DASHSCOPE_API_KEY
   ```

**注意：** 可能需要稍微修改代码以适配 Vercel 的函数格式

---

### 2. 腾讯云 Serverless Cloud Function (SCF)

1. 注册腾讯云账号

2. 创建函数，选择 Python 3.9

3. 需要修改代码为函数格式（见下方代码示例）

---

## 方案四：GitHub Codespaces + ngrok（开发环境）

如果您有 GitHub 账号，可以使用免费的 Codespaces：

1. 在 GitHub 创建仓库并上传代码

2. 点击 "Code" → "Codespaces" → "Create codespace"

3. 在 Codespaces 中运行应用

4. 使用 ngrok 暴露端口

---

## 快速对比

| 方案 | 难度 | 稳定性 | 免费额度 | 推荐度 |
|------|------|--------|----------|--------|
| ngrok | ⭐ 极简 | ⭐⭐⭐ | 有限制 | ⭐⭐⭐⭐⭐ |
| Render | ⭐⭐ 简单 | ⭐⭐⭐⭐⭐ | 750小时/月 | ⭐⭐⭐⭐⭐ |
| Railway | ⭐⭐ 简单 | ⭐⭐⭐⭐ | $5/月 | ⭐⭐⭐⭐ |
| Fly.io | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐⭐ | 充足 | ⭐⭐⭐⭐ |

---

## 最快方案推荐（5分钟）

### 使用 ngrok（临时测试）

1. **下载 ngrok**：https://ngrok.com/download

2. **注册并获取 token**：https://dashboard.ngrok.com/get-started/your-authtoken

3. **配置 ngrok**：
   ```bash
   ngrok config add-authtoken YOUR_TOKEN
   ```

4. **启动本地服务**：
   ```bash
   python app.py
   ```

5. **启动 ngrok**（新终端）：
   ```bash
   ngrok http 5000
   ```

6. **复制 URL**，例如：`https://abc123.ngrok-free.app`

7. **提交 JSON**：
   ```json
   {
     "api_key": "https://abc123.ngrok-free.app/model"
   }
   ```

### 使用 Render（长期使用）

1. **注册 Render**：https://render.com/

2. **连接 GitHub** 或上传代码

3. **设置环境变量** `DASHSCOPE_API_KEY`

4. **部署完成**，获取固定 URL

---

## 需要修改代码吗？

**大多数情况下不需要修改！**

- ✅ ngrok：不需要修改，直接用
- ✅ Render：需要添加 `Procfile`，代码无需修改
- ✅ Railway：自动检测，代码无需修改
- ⚠️ Serverless：可能需要小修改（见下方适配代码）

---

## Serverless 适配代码（如果需要）

如果使用云函数，可能需要创建一个适配文件：

### Vercel 适配

创建 `api/index.py`：
```python
from app import app

# Vercel 会将请求转发到这里
handler = app
```

或修改 `app.py` 的启动部分：
```python
if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    app.run(host=host, port=port, debug=False)
```

## 常见问题

**Q: 免费版有请求限制吗？**  
A: ngrok 免费版有，但测试足够。Render/Railway 免费版限制较少。

**Q: URL 会变化吗？**  
A: ngrok 免费版会变化。Render/Railway 会提供固定 URL。

**Q: 本地电脑需要一直开着吗？**  
A: 使用内网穿透（ngrok）需要。使用云平台（Render）不需要。

**Q: 哪个最稳定？**  
A: Render 或 Railway 最稳定，有固定域名和 HTTPS。




