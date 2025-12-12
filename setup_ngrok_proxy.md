# 使用 ngrok + test_model.py 完整解决方案

## 问题
- `test_model.py` 使用 ngrok HTTPS URL
- 遇到 SSL 错误
- 不能修改 `test_model.py`

## 解决方案：使用本地代理 + hosts 文件

### 步骤 1: 修改 Flask 应用运行端口

将原始 Flask 应用运行在端口 **5001**：

```powershell
# Windows PowerShell
$env:PORT=5001
python app.py
```

### 步骤 2: 启动 ngrok 指向 Flask 应用

在新的终端运行 ngrok，指向端口 5001：

```bash
ngrok http 5001
```

获取 ngrok URL，例如：`https://apperceptive-postmuscular-johnette.ngrok-free.dev`

### 步骤 3: 配置代理服务器

确保 `proxy_server.py` 中的 `NGROK_URL` 设置正确：

```python
NGROK_URL = "https://apperceptive-postmuscular-johnette.ngrok-free.dev"
```

### 步骤 4: 启动本地代理服务器

在另一个终端运行代理服务器（监听端口 5000）：

```powershell
python proxy_server.py
```

### 步骤 5: 修改系统 hosts 文件（关键步骤）

**以管理员身份操作：**

1. 打开记事本（右键 → 以管理员身份运行）

2. 打开文件：`C:\Windows\System32\drivers\etc\hosts`

3. 在文件末尾添加：
   ```
   127.0.0.1    apperceptive-postmuscular-johnette.ngrok-free.dev
   ```

4. 保存文件

5. 刷新 DNS 缓存：
   ```powershell
   ipconfig /flushdns
   ```

### 步骤 6: 运行测试

现在运行 `test_model.py`：

```powershell
python test_model.py
```

## 工作原理

1. `test_model.py` 请求 `https://apperceptive-postmuscular-johnette.ngrok-free.dev/model`
2. 系统 hosts 文件将域名解析到 `127.0.0.1`（本地）
3. 请求到达本地代理服务器（`proxy_server.py`，监听 5000 端口）
4. 代理服务器：
   - 添加 `ngrok-skip-browser-warning` header
   - 使用 `verify=False` 禁用 SSL 验证
   - 转发请求到真实的 ngrok URL
5. ngrok 将请求转发到 Flask 应用（端口 5001）
6. 响应按原路返回

## 端口分配

- **端口 5001**: Flask 应用（原始服务）
- **端口 5000**: 本地代理服务器（转发到 ngrok）
- **ngrok**: 提供公网访问（从外部访问）

## 如果 ngrok URL 变化了

如果重新启动 ngrok 后 URL 变化：

1. 更新 `proxy_server.py` 中的 `NGROK_URL`
2. 更新 `hosts` 文件中的域名
3. 刷新 DNS：`ipconfig /flushdns`
4. 重启代理服务器

## 快速启动脚本

您可以创建一个批处理文件来简化操作：

**start_all.bat**:
```batch
@echo off
echo Starting Flask app on port 5001...
start cmd /k "set PORT=5001 && python app.py"

timeout /t 3

echo Starting proxy server on port 5000...
start cmd /k "python proxy_server.py"

echo.
echo Services started!
echo 1. Make sure ngrok is running: ngrok http 5001
echo 2. Update proxy_server.py with your ngrok URL
echo 3. Update hosts file if ngrok URL changed
echo 4. Run: python test_model.py
pause
```

## 验证步骤

1. **检查 Flask 应用**：
   ```powershell
   curl http://localhost:5001/health
   ```

2. **检查代理服务器**：
   ```powershell
   curl http://localhost:5000/health
   ```

3. **检查 ngrok**：
   在浏览器访问 ngrok 提供的 URL

4. **运行完整测试**：
   ```powershell
   python test_model.py
   ```

