# encoding=utf-8
import ast
import json
import os
import dashscope
from dashscope import Generation
from http import HTTPStatus
import time
import re
import signal
from typing import Tuple, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局错误处理器，确保所有错误都返回 JSON 格式
@app.errorhandler(500)
def internal_error(error):
    """处理 500 内部服务器错误，返回 JSON 格式"""
    return jsonify({
        "id": -1,
        "reasoning_content": f"服务器内部错误: {str(error)}",
        "numerical_answer": [],
        "article_answer": []
    }), 200

@app.errorhandler(404)
def not_found(error):
    """处理 404 错误，返回 JSON 格式"""
    return jsonify({
        "id": -1,
        "reasoning_content": "接口不存在",
        "numerical_answer": [],
        "article_answer": []
    }), 200

@app.errorhandler(Exception)
def handle_exception(e):
    """处理所有未捕获的异常，返回 JSON 格式"""
    return jsonify({
        "id": -1,
        "reasoning_content": f"处理异常: {str(e)}",
        "numerical_answer": [],
        "article_answer": []
    }), 200

# 从 baseline.py 提取的核心函数
def ask_llm(prompt, model="qwen3-235b-a22b-instruct-2507", timeout=120):
    """
    调用 LLM，添加超时处理
    timeout: 超时时间（秒），默认 120 秒
    """
    if ("qwen3-235b-a22b-instruct-2507" == model):
        return ask_tyqw_general(prompt, model, timeout=timeout)


def ask_tyqw_general(prompt, model='qwen3-235b-a22b-instruct-2507', timeout=120):
    """
    调用通义千问 API，添加超时处理
    timeout: 超时时间（秒），默认 120 秒
    """
    dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "sk-653bf07ab1aa466099d80a3a275afdb4")
    
    try:
        if type(prompt) is str:
            s_time = time.time()
            # 添加超时参数（如果 dashscope 支持）
            try:
                response = Generation.call(
                    model=model,
                    prompt=prompt,
                    timeout=timeout  # 尝试传递超时参数
                )
            except TypeError:
                # 如果不支持 timeout 参数，使用默认调用
                response = Generation.call(
                    model=model,
                    prompt=prompt
                )
            
            e_time = time.time()
            elapsed = e_time - s_time

            # 检查是否超时
            if elapsed > timeout:
                app.logger.warning(f"LLM 调用耗时 {elapsed:.2f} 秒，超过超时时间 {timeout} 秒")
                return None, {"used_time": elapsed, "input_tokens": None, "output_tokens": None}

            if response.status_code == HTTPStatus.OK:
                used_time = e_time - s_time
                input_tokens = response['usage'].input_tokens
                output_tokens = response['usage'].output_tokens
                token_infomration = {"used_time": used_time, "input_tokens": input_tokens, "output_tokens": output_tokens}
                return response["output"]["text"], token_infomration
            return None, {"used_time": None, "input_tokens": None, "output_tokens": None}

        elif type(prompt) is list:
            try:
                response = Generation.call(
                    model=model,
                    messages=prompt,
                    result_format='message',  # 设置输出为'message'格式
                    timeout=timeout
                )
            except TypeError:
                response = Generation.call(
                    model=model,
                    messages=prompt,
                    result_format='message'
                )
            
            if response.status_code == HTTPStatus.OK:
                return response["output"]["choices"][0]["message"]["content"]
            else:
                return None
    except Exception as e:
        app.logger.error(f"LLM API 调用异常: {str(e)}")
        return None, {"used_time": None, "input_tokens": None, "output_tokens": None}


def extract_response(text: str) -> Tuple[bool, Optional[dict]]:
    """
    从 LLM 返回文本中提取 JSON / Python 字典。
    返回 (成功标志, dict 或 None)。
    不使用 eval；优先尝试 json.loads，再尝试 ast.literal_eval。
    如果解析失败，返回 (False, None)。
    """
    if not isinstance(text, str):
        return False, None

    # 1) 优先提取 ```json``` 或 ```python``` 代码块里的内容
    code_block_pattern = r"```(?:json|python)?\s*(\{[\s\S]*?\})\s*```"
    m = re.search(code_block_pattern, text, flags=re.IGNORECASE)
    candidate = None
    if m:
        candidate = m.group(1)
    else:
        # 2) 如果没有代码块，尝试从第一对大括号提取最外层 {...}
        m2 = re.search(r"(\{[\s\S]*\})", text)
        if m2:
            candidate = m2.group(1)
        else:
            candidate = text.strip()

    # 清理常见噪声：去掉左右两侧的非打印字符
    candidate = candidate.strip()

    # 尝试 json.loads（严格且安全）
    try:
        parsed = json.loads(candidate)
        if isinstance(parsed, dict):
            return True, parsed
        else:
            # 如果顶层不是 dict，也接受并封装
            return True, {"result": parsed}
    except Exception:
        pass

    # 尝试 ast.literal_eval（支持 Python 字面量：单引号、None、True/False）
    try:
        parsed = ast.literal_eval(candidate)
        if isinstance(parsed, dict):
            return True, parsed
        else:
            return True, {"result": parsed}
    except Exception:
        pass

    # 回退策略：尝试把单引号改为双引号再 json.loads（谨慎）
    try:
        temp = candidate
        # 仅在包含单引号且不包含双引号时尝试
        if ("'" in temp) and ('"' not in temp):
            temp2 = temp.replace("'", '"')
            parsed = json.loads(temp2)
            if isinstance(parsed, dict):
                return True, parsed
            else:
                return True, {"result": parsed}
    except Exception:
        pass

    # 无法解析：记录原始文本供后续人工检查
    return False, None


prompt_template = """针对查询中涉及到的问题回答数值计算结果并给出依据的法律条款：
{query}

要求：
1. 一步一步思考，最后给出答案（思路可写在 reasoning 字段）
2. 最后返回一个**严格的 JSON**，只返回 JSON，不要多余自然语言，也不要包含占位符（例如 xx,..）
格式示例：
```json
{{
  "article_answer": ["《民法典》第123条", "《某法》第45条"],
  "numerical_answer": [1234.56],
  "reasoning": "这里写推理过程的简短摘要"
}}
```"""


def process_query(query: str, model_name='qwen3-235b-a22b-instruct-2507', timeout=120):
    """
    处理单个查询，返回 LLM 的原始响应
    timeout: 超时时间（秒），默认 120 秒
    """
    prompt = prompt_template.replace("{query}", query)
    response, usage = ask_llm(prompt, model=model_name, timeout=timeout)
    return response


def process_single_query(query_data):
    """
    处理单个查询请求
    返回处理结果字典
    所有错误都会被捕获并返回标准格式的响应
    """
    try:
        if not isinstance(query_data, dict):
            return {
                "id": -1,
                "reasoning_content": "请求格式错误：单个请求必须是 JSON 对象",
                "numerical_answer": [],
                "article_answer": []
            }
        
        # 验证必需字段
        if "id" not in query_data or "query" not in query_data:
            query_id = query_data.get("id", -1)
            return {
                "id": query_id,
                "reasoning_content": "请求必须包含 'id' 和 'query' 字段",
                "numerical_answer": [],
                "article_answer": []
            }
        
        query_id = query_data["id"]
        query = query_data["query"]
        
        # 验证 query 不为空
        if not query or not isinstance(query, str) or len(query.strip()) == 0:
            return {
                "id": query_id,
                "reasoning_content": "查询内容不能为空",
                "numerical_answer": [],
                "article_answer": []
            }
        
        # 处理查询，添加异常捕获和超时处理
        try:
            # 设置单个查询的超时时间（秒）
            # 对于批量请求，每个查询的超时时间会相应缩短
            query_timeout = 120  # 默认 120 秒
            raw_response = process_query(query, timeout=query_timeout)
        except TimeoutError as e:
            return {
                "id": query_id,
                "reasoning_content": f"模型调用超时: {str(e)}",
                "numerical_answer": [],
                "article_answer": []
            }
        except Exception as e:
            return {
                "id": query_id,
                "reasoning_content": f"模型调用异常: {str(e)}",
                "numerical_answer": [],
                "article_answer": []
            }
        
        if raw_response is None:
            # LLM 调用失败，返回错误响应
            return {
                "id": query_id,
                "reasoning_content": "模型调用失败，返回为空",
                "numerical_answer": [],
                "article_answer": []
            }
        
        # 提取结构化响应
        try:
            success, extracted = extract_response(raw_response)
        except Exception as e:
            # 提取失败，返回原始响应
            return {
                "id": query_id,
                "reasoning_content": raw_response if raw_response else f"响应提取失败: {str(e)}",
                "numerical_answer": [],
                "article_answer": []
            }
        
        if success and extracted is not None:
            # 确保必要的字段存在
            result = {
                "id": query_id,
                "reasoning_content": raw_response,  # 完整的推理内容
                "numerical_answer": extracted.get("numerical_answer", []),
                "article_answer": extracted.get("article_answer", [])
            }
        else:
            # 解析失败，使用兜底结构
            result = {
                "id": query_id,
                "reasoning_content": raw_response if raw_response else "无法解析模型响应",
                "numerical_answer": [],
                "article_answer": []
            }
        
        return result
        
    except Exception as e:
        # 捕获所有异常，返回错误信息
        import traceback
        app.logger.error(f"process_single_query 异常: {str(e)}\n{traceback.format_exc()}")
        query_id = query_data.get("id", -1) if isinstance(query_data, dict) else -1
        return {
            "id": query_id,
            "reasoning_content": f"处理错误: {str(e)}",
            "numerical_answer": [],
            "article_answer": []
        }


@app.route('/model', methods=['POST'])
def model_inference():
    """
    API 端点：处理法律问题查询
    请求格式: 
    - 单个对象: {"id": 0, "query": "问题"}
    - 批量请求: [{"id": 0, "query": "问题1"}, {"id": 1, "query": "问题2"}]
    响应格式: 
    - 单个响应: {"id": 0, "reasoning_content": "...", "numerical_answer": [...], "article_answer": [...]}
    - 批量响应: [{...}, {...}]
    """
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                "id": -1,
                "reasoning_content": "请求体不能为空",
                "numerical_answer": [],
                "article_answer": []
            }), 200
        
        # 记录请求信息（用于调试）
        if isinstance(data, list):
            app.logger.info(f"收到批量请求，共 {len(data)} 条")
        else:
            app.logger.info(f"收到单个请求，ID: {data.get('id', 'unknown')}")
        
        # 如果是列表，批量处理
        if isinstance(data, list):
            if len(data) == 0:
                return jsonify([]), 200
            
            # 限制批量请求大小，避免超时
            MAX_BATCH_SIZE = 100  # 最大批量大小
            if len(data) > MAX_BATCH_SIZE:
                return jsonify({
                    "id": -1,
                    "reasoning_content": f"批量请求过大（{len(data)} 条），最多支持 {MAX_BATCH_SIZE} 条。请分批发送请求。",
                    "numerical_answer": [],
                    "article_answer": []
                }), 200
            
            results = []
            # 批量处理，每个请求单独处理，避免一个失败影响全部
            for idx, item in enumerate(data):
                try:
                    # 记录处理进度
                    if (idx + 1) % 10 == 0:
                        app.logger.info(f"批量处理进度: {idx + 1}/{len(data)}")
                    
                    result = process_single_query(item)
                    results.append(result)
                except Exception as e:
                    # 单个请求失败，返回错误响应但继续处理其他请求
                    app.logger.error(f"处理第 {idx + 1} 条请求时出错: {str(e)}")
                    query_id = item.get("id", idx) if isinstance(item, dict) else idx
                    error_result = {
                        "id": query_id,
                        "reasoning_content": f"处理错误: {str(e)}",
                        "numerical_answer": [],
                        "article_answer": []
                    }
                    results.append(error_result)
            
            app.logger.info(f"批量处理完成，共处理 {len(results)} 条")
            return jsonify(results), 200
        
        # 单个对象处理
        result = process_single_query(data)
        return jsonify(result), 200
        
    except Exception as e:
        # 捕获所有异常，返回错误信息
        import traceback
        error_msg = str(e)
        # 记录详细错误信息（用于调试，生产环境可以去掉）
        app.logger.error(f"处理请求时发生错误: {error_msg}\n{traceback.format_exc()}")
        
        try:
            if 'data' in locals():
                if isinstance(data, list) and len(data) > 0:
                    # 如果是列表，返回错误列表
                    error_results = []
                    for idx, item in enumerate(data):
                        query_id = item.get("id", idx) if isinstance(item, dict) else idx
                        error_results.append({
                            "id": query_id,
                            "reasoning_content": f"批量处理错误: {error_msg}",
                            "numerical_answer": [],
                            "article_answer": []
                        })
                    return jsonify(error_results), 200
                elif isinstance(data, dict):
                    query_id = data.get("id", -1)
                else:
                    query_id = -1
            else:
                query_id = -1
        except:
            query_id = -1
            
        error_response = {
            "id": query_id,
            "reasoning_content": f"处理错误: {error_msg}",
            "numerical_answer": [],
            "article_answer": []
        }
        return jsonify(error_response), 200


@app.route('/', methods=['GET'])
def index():
    """根路径，返回 API 使用说明"""
    return jsonify({
        "message": "法律AI比赛 API 服务",
        "endpoints": {
            "POST /model": "处理法律问题查询",
            "GET /health": "健康检查"
        },
        "usage": {
            "url": "/model",
            "method": "POST",
            "request_format": {
                "id": 0,
                "query": "问题内容"
            },
            "response_format": {
                "id": 0,
                "reasoning_content": "推理过程",
                "numerical_answer": [123456],
                "article_answer": ["法律条文"]
            }
        }
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({"status": "healthy"}), 200


if __name__ == '__main__':
    # 可以在环境变量中设置端口，默认 5000
    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    # 设置日志级别
    import logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    app.run(host=host, port=port, debug=False)

