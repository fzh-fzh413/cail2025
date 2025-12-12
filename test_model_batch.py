"""
分批处理测试脚本
由于 Render 有超时限制，将大量数据分成小批处理
"""
import requests
import json
import time

api_url = "https://cail2025.onrender.com/model"
data = []

# 读取数据
print("正在读取数据...")
with open(r"C:\Users\fzh\Desktop\pythonProject1\stage1_test.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        data.append(json.loads(line))

print(f"总共 {len(data)} 条数据")

# 分批处理（每批 50 条，避免超时）
batch_size = 50
all_results = []

for i in range(0, len(data), batch_size):
    batch = data[i:i+batch_size]
    batch_num = i // batch_size + 1
    total_batches = (len(data) + batch_size - 1) // batch_size
    
    print(f"\n处理第 {batch_num}/{total_batches} 批，共 {len(batch)} 条...")
    
    try:
        # 发送请求，设置较长的超时时间
        response = requests.post(api_url, json=batch, timeout=600)
        
        if response.status_code == 200:
            batch_results = response.json()
            if isinstance(batch_results, list):
                all_results.extend(batch_results)
                print(f"✓ 成功处理 {len(batch_results)} 条")
            else:
                print(f"✗ 响应格式错误: {type(batch_results)}")
                print(f"响应内容: {str(batch_results)[:200]}")
        else:
            print(f"✗ 错误状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            # 即使出错，也添加错误结果以保持数据完整性
            for item in batch:
                error_result = {
                    "id": item.get("id", -1),
                    "reasoning_content": f"服务器错误: HTTP {response.status_code}",
                    "numerical_answer": [],
                    "article_answer": []
                }
                all_results.append(error_result)
                
    except requests.exceptions.Timeout:
        print(f"✗ 请求超时")
        # 添加超时错误结果
        for item in batch:
            error_result = {
                "id": item.get("id", -1),
                "reasoning_content": "请求超时",
                "numerical_answer": [],
                "article_answer": []
            }
            all_results.append(error_result)
            
    except requests.exceptions.JSONDecodeError as e:
        print(f"✗ JSON 解析错误: {str(e)}")
        print(f"响应内容: {response.text[:500] if 'response' in locals() else 'N/A'}")
        # 添加解析错误结果
        for item in batch:
            error_result = {
                "id": item.get("id", -1),
                "reasoning_content": f"响应解析错误: {str(e)}",
                "numerical_answer": [],
                "article_answer": []
            }
            all_results.append(error_result)
            
    except Exception as e:
        print(f"✗ 处理失败: {str(e)}")
        # 添加异常错误结果
        for item in batch:
            error_result = {
                "id": item.get("id", -1),
                "reasoning_content": f"处理异常: {str(e)}",
                "numerical_answer": [],
                "article_answer": []
            }
            all_results.append(error_result)
    
    # 避免请求过快，给服务器一些休息时间
    if i + batch_size < len(data):
        time.sleep(2)

print(f"\n{'='*50}")
print(f"处理完成！")
print(f"总共处理: {len(all_results)} 条结果")
print(f"预期结果: {len(data)} 条")
print(f"{'='*50}")

# 保存结果到文件
output_file = "prediction_batch.jsonl"
print(f"\n正在保存结果到 {output_file}...")
with open(output_file, "w", encoding="utf-8") as f:
    for result in all_results:
        f.write(json.dumps(result, ensure_ascii=False) + "\n")

print(f"结果已保存到 {output_file}")

# 显示前几条结果作为示例
if all_results:
    print("\n前 3 条结果示例:")
    for i, result in enumerate(all_results[:3]):
        print(f"\n结果 {i+1}:")
        print(f"  ID: {result.get('id', 'N/A')}")
        print(f"  数值答案: {result.get('numerical_answer', [])}")
        print(f"  法条答案: {result.get('article_answer', [])}")
        print(f"  推理内容: {result.get('reasoning_content', '')[:100]}...")

