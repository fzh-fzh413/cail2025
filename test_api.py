# encoding=utf-8
"""
测试 API 服务的脚本
"""
import requests
import json

def test_api():
    """测试 API 接口"""
    # 修改为您的 API 地址
    api_url = "http://localhost:5000/model"
    
    # 测试数据
    input_data = {
        "id": 0,
        "query": "某商家以收容救护为名，非法买卖了一只价值5万元的野生动物。若被查处，该商家将面临最高多少罚款？"
    }
    
    print("发送请求...")
    print(f"URL: {api_url}")
    print(f"请求数据: {json.dumps(input_data, ensure_ascii=False, indent=2)}")
    print("-" * 50)
    
    try:
        response = requests.post(api_url, json=input_data, timeout=60)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("模型处理结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            # 验证响应格式
            required_fields = ["id", "reasoning_content", "numerical_answer", "article_answer"]
            missing_fields = [field for field in required_fields if field not in result]
            
            if missing_fields:
                print(f"\n警告: 响应缺少必需字段: {missing_fields}")
            else:
                print("\n✓ 响应格式验证通过")
        else:
            print(f"错误: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
    except Exception as e:
        print(f"发生错误: {e}")


if __name__ == "__main__":
    test_api()

