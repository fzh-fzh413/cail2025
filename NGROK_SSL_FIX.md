# ngrok SSL 错误解决方案

## 问题描述

在使用 ngrok 免费版时，可能会遇到 SSL 错误：
```
SSLError: [SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC] decryption failed or bad record mac
```

## 解决方案

### 方案 1：重新启动 ngrok（最简单）⭐

1. **停止当前的 ngrok**：
   - 在 ngrok 运行的终端按 `Ctrl+C`

2. **重新启动 ngrok**：
   ```bash
   ngrok http 5000
   ```

3. **获取新的 URL**（如果 URL 变化了，更新 test_model.py 中的 api_key）

### 方案 2：使用本地测试（推荐用于开发测试）

如果您的 Flask 服务运行在本地，可以直接使用 localhost：

1. **修改 test_model.py 中的 api_key**：
   ```python
   api_key = "http://localhost:5000/model"  # 使用 HTTP 而不是 HTTPS
   ```

2. **运行测试**：
   ```bash
   python test_model.py
   ```

### 方案 3：使用代理脚本

如果无法修改 test_model.py，可以使用 `test_proxy.py` 作为代理：

```bash
python test_proxy.py
```

这个脚本会：
- 添加 ngrok 需要的 headers
- 处理 SSL 验证问题
- 提供更好的错误提示

### 方案 4：升级 ngrok 配置

如果经常使用 ngrok，可以考虑：

1. **使用固定域名**（需要付费账号）
2. **使用其他内网穿透工具**：
   - **localtunnel**: `npm install -g localtunnel && lt --port 5000`
   - **cloudflared**: `cloudflared tunnel --url http://localhost:5000`
   - **serveo**: `ssh -R 80:localhost:5000 serveo.net`

### 方案 5：使用云平台部署（最稳定）⭐⭐

使用 Render 或 Railway 等免费云平台部署，避免 ngrok 的问题：

- 查看 `FREE_DEPLOYMENT.md` 了解详细步骤
- 使用 `render.yaml` 快速部署到 Render

## 快速测试

### 测试 Flask 服务是否正常运行

```bash
# 在浏览器访问
http://localhost:5000/health

# 或使用 curl
curl http://localhost:5000/health
```

### 测试 API 端点

```bash
curl -X POST http://localhost:5000/model \
  -H "Content-Type: application/json" \
  -d '{"id": 0, "query": "测试问题"}'
```

## 常见问题

**Q: ngrok URL 经常变化怎么办？**  
A: 考虑使用云平台（如 Render）部署，获得固定 URL。

**Q: SSL 错误一直存在？**  
A: 
1. 检查 ngrok 版本：`ngrok version`
2. 更新 ngrok：访问 https://ngrok.com/download 下载最新版
3. 重新配置 token：`ngrok config add-authtoken YOUR_TOKEN`

**Q: 想要更稳定的方案？**  
A: 使用 Render 或 Railway 等云平台部署，完全避免 ngrok 的问题。


