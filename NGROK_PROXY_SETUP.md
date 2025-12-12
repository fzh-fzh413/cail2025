# ngrok + test_model.py 解决方案

## 问题分析

`test_model.py` 直接请求 ngrok URL，SSL 错误发生在客户端到 ngrok 之间。由于不能修改 `test_model.py`，我们需要在服务器端或系统层面解决。

## 解决方案：使用本地代理转发到 ngrok

### 方案一：修改 Flask 应用端口 + 本地代理（推荐）

#### 步骤 1: 修改 Flask 应用运行端口

将 Flask 应用运行在端口 5001，然后使用代理服务器监听 5000，转发到 ngrok：

**在启动 Flask 前设置环境变量：**
```powershell
# Windows PowerShell
$env:PORT=5001
python app.py
```

#### 步骤 2: 配置代理服务器

修改 `proxy_server.py` 中的 NGROK_URL 为您的 ngrok 地址，然后运行：

```powershell
python proxy_server.py
```

代理服务器会监听 `localhost:5000`，将请求转发到 ngrok URL。

#### 步骤 3: 修改系统 hosts 文件（将 ngrok 域名指向本地）

这样可以拦截对 ngrok 域名的请求：

1. **以管理员身份打开记事本**

2. **打开 hosts 文件**：
   - 路径：`C:\Windows\System32\drivers\etc\hosts`
   - 文件类型改为"所有文件"

3. **添加以下行**：
   ```
   127.0.0.1    apperceptive-postmuscular-johnette.ngrok-free.dev
   ```

4. **保存文件**

5. **刷新 DNS 缓存**：
   ```powershell
   ipconfig /flushdns
   ```

#### 步骤 4: 运行测试

现在 `test_model.py` 中的 ngrok URL 会被解析到本地代理服务器（localhost:5000），代理会转发到实际的 ngrok。

---

## 方案二：直接解决 ngrok SSL 问题（更简单）

### 重新启动 ngrok 并添加配置

1. **停止当前 ngrok**

2. **使用 ngrok 配置文件**：
   
   创建或编辑 `ngrok.yml`（在用户目录下）：
   ```yaml
   version: "2"
   authtoken: YOUR_AUTH_TOKEN
   tunnel_defaults:
     inspect: false
   ```

3. **启动 ngrok**：
   ```bash
   ngrok http 5000
   ```

4. **如果还有问题，尝试使用 HTTP 而不是 HTTPS**：
   
   ngrok 会同时提供 HTTP 和 HTTPS URL。如果有 SSL 问题，可以：
   - 使用 HTTP URL（`http://xxxxx.ngrok-free.app`）
   - 但这需要修改 `test_model.py`（不可行）

---

## 方案三：使用 ngrok 的静态域名（如果有）

如果您有 ngrok 账号，可以配置静态域名，通常更稳定：

```bash
ngrok http 5000 --domain=your-static-domain.ngrok-free.app
```

---

## 快速解决步骤（推荐）

### 最简单的方法：

1. **修改 Flask 端口**（在一个终端）：
   ```powershell
   $env:PORT=5001
   python app.py
   ```

2. **修改代理服务器配置**：
   
   编辑 `proxy_server.py`，确保：
   ```python
   NGROK_URL = "https://apperceptive-postmuscular-johnette.ngrok-free.dev"
   ```

3. **启动代理服务器**（在另一个终端）：
   ```powershell
   python proxy_server.py
   ```

4. **修改 hosts 文件**（以管理员身份）：
   ```
   127.0.0.1    apperceptive-postmuscular-johnette.ngrok-free.dev
   ```
   
   然后刷新 DNS：
   ```powershell
   ipconfig /flushdns
   ```

5. **重新启动 ngrok**（确保 Flask 在 5001 运行）：
   ```bash
   ngrok http 5001
   ```

6. **运行测试**：
   ```powershell
   python test_model.py
   ```

现在 `test_model.py` 请求 ngrok URL 时：
- 被 hosts 文件拦截，指向 `127.0.0.1`
- 请求到达本地代理服务器（端口 5000）
- 代理服务器转发到实际的 ngrok URL
- 代理服务器处理 SSL 问题并添加必要的 headers

---

## 注意事项

1. **端口冲突**：确保端口 5000 和 5001 没有被其他程序占用

2. **管理员权限**：修改 hosts 文件需要管理员权限

3. **DNS 缓存**：修改 hosts 后记得刷新 DNS 缓存

4. **ngrok URL 变化**：如果 ngrok URL 变化，需要：
   - 更新 `proxy_server.py` 中的 NGROK_URL
   - 更新 hosts 文件中的域名
   - 刷新 DNS 缓存

