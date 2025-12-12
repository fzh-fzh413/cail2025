# encoding=utf-8
import ast

import requests
import json
import os
import dashscope
from dashscope import Generation
from http import HTTPStatus
import time
import re
from tqdm import tqdm
from typing import Tuple, Optional

def ask_llm(prompt, model="qwen3-235b-a22b-instruct-2507"):
    if ("qwen3-235b-a22b-instruct-2507" == model):
        return ask_tyqw_general(prompt, model)


def ask_tyqw_general(prompt, model='qwen3-235b-a22b-instruct-2507'):
    dashscope.api_key = os.getenv("DASHSCOPE_API_KEY", "sk-653bf07ab1aa466099d80a3a275afdb4")
    if type(prompt) is str:
        s_time = time.time()
        response = Generation.call(model,
                                   prompt=prompt,
                                   )
        e_time = time.time()

        # print(response)
        if response.status_code == HTTPStatus.OK:
            used_time = e_time - s_time
            input_tokens = response['usage'].input_tokens
            output_tokens = response['usage'].output_tokens
            token_infomration = {"used_time": used_time, "input_tokens": input_tokens, "output_tokens": output_tokens}
            return response["output"]["text"], token_infomration
        return None, {"used_time": None, "input_tokens": None, "output_tokens": None}

    elif type(prompt) is list:
        response = Generation.call(model,
                                   messages=prompt,
                                   result_format='message'  # 设置输出为'message'格式
                                   )
        if response.status_code == HTTPStatus.OK:
            return response["output"]["choices"][0]["message"]["content"]
        else:
            return None


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

prompt = """针对查询中涉及到的问题回答数值计算结果并给出依据的法律条款：
{query}

要求：
1. 一步一步思考，最后给出答案（思路可写在 reasoning 字段）
2. 最后返回一个**严格的 JSON**，只返回 JSON，不要多余自然语言，也不要包含占位符（例如 xx,..）
格式示例：
```json
{
  "article_answer": ["《民法典》第123条", "《某法》第45条"],
  "numerical_answer": [1234.56],
  "reasoning": "这里写推理过程的简短摘要"
}
"""


def process_res(num, model_name='qwen3-235b-a22b-instruct-2507'):
    query = data_test[num]['query']
    response, usage = ask_llm(prompt.replace("{query}", query)
                              , model=model_name)

    return response


with open(f"./stage1_test.jsonl") as f:
    data_test = f.readlines()
data_test = [json.loads(i) for i in data_test]

pred_res = []

for i in tqdm(range(len(data_test))):
    res = process_res(i)
    pred_res.append(res)

final_res = []

for i in range(len(data_test)):
    success, item = extract_response(pred_res[i])

    if success and item is not None:
        # 正常解析成功
        item["reasoning_content"] = pred_res[i]
        item["id"] = i
        final_res.append(item)
    else:
        # 解析失败，构造一个兜底结构
        fallback = {
            "id": i,
            "article_answer": [],
            "numerical_answer": [],
            "reasoning_content": pred_res[i],
            "parse_error": True
        }
        final_res.append(fallback)

# 写出文件
with open("prediction1.jsonl", "w", encoding="utf-8") as f:
    for item in final_res:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")
