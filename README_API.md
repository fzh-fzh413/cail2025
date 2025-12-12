# 法律AI比赛 API 服务

基于 `baseline.py` 改造的 API 服务，符合比赛接口规范要求。

## 功能说明

- 提供 POST API 接口 `/model`
- 接收法律问题查询，返回数值计算结果和法律依据
- 符合比赛接口规范要求

## 安装依赖

```bash
pip install -r requirements.txt
```

## 环境变量配置

确保设置了 `DASHSCOPE_API_KEY` 环境变量（用于调用通义千问模型）：

```bash
# Windows PowerShell
$env:DASHSCOPE_API_KEY="your-api-key-here"

# Linux/Mac
export DASHSCOPE_API_KEY="your-api-key-here"
```

或者在代码中已经设置了默认值（不建议用于生产环境）。

## 启动服务

### 方式1：直接运行

```bash
python app.py
```

服务将在 `http://0.0.0.0:5000` 启动。

### 方式2：使用环境变量配置端口和主机

```bash
# Windows PowerShell
$env:PORT=8080
$env:HOST="0.0.0.0"
python app.py

# Linux/Mac
PORT=8080 HOST=0.0.0.0 python app.py
```

### 方式3：使用 gunicorn（推荐用于生产环境）

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## API 接口说明

### POST /model

**请求格式：**
```json
{
  "id": 0,
  "query": "某商家以收容救护为名，非法买卖了一只价值5万元的野生动物。若被查处，该商家将面临最高多少罚款？"
}
```

**响应格式：**
```json
{
  "id": 0,
  "reasoning_content": "根据《中华人民共和国野生动物保护法》第四十七条...",
  "numerical_answer": [1000000],
  "article_answer": ["《中华人民共和国野生动物保护法》第四十七条"]
}
```

**状态码：**
- 200: 成功响应

### GET /health

健康检查端点，用于检查服务是否正常运行。

**响应：**
```json
{
  "status": "healthy"
}
```

## 测试示例

```python
import requests

api_url = "http://localhost:5000/model"

input_data = {
    "id": 0,
    "query": "某商家以收容救护为名，非法买卖了一只价值5万元的野生动物。若被查处，该商家将面临最高多少罚款？"
}

response = requests.post(api_url, json=input_data)
result = response.json()

print("模型处理结果:", result)
```

## 部署说明

### 本地测试

1. 确保已安装所有依赖
2. 设置 `DASHSCOPE_API_KEY` 环境变量
3. 运行 `python app.py`
4. 访问 `http://localhost:5000/model` 进行测试

### 服务器部署

1. 将代码上传到服务器
2. 安装依赖：`pip install -r requirements.txt`
3. 使用 gunicorn 或 uwsgi 等 WSGI 服务器部署
4. 配置反向代理（如 Nginx）如果需要 HTTPS
5. 确保防火墙开放相应端口

### 云服务部署

可以部署到：
- 云服务器（阿里云、腾讯云等）
- 容器服务（Docker）
- Serverless 服务（需要适配）

## 注意事项

1. **API Key 安全**：建议使用环境变量或密钥管理服务存储 API Key，不要硬编码
2. **并发处理**：如需处理高并发请求，建议使用 gunicorn 等多进程服务器
3. **错误处理**：API 会在出错时返回格式化的响应，不会抛出未处理的异常
4. **超时设置**：LLM 调用可能需要较长时间，建议在反向代理层设置适当的超时时间

## 提交格式

比赛提交时需要创建一个 JSON 文件，格式如下：

```json
{
  "api_key": "https://your-api-domain.com/model"
}
```

确保提供的 API 地址可以正常访问并返回符合规范的响应。

