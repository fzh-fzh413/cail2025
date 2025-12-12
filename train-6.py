# -*- coding: utf-8 -*-
import json
import re
from dashscope import Generation

# ------------------- 1. 核心配置 -------------------
BASE_MODEL_NAME = "qwen3-235b-a22b-instruct-2507"
DASHSCOPE_API_KEY = "sk-653bf07ab1aa466099d80a3a275afdb4"
TEST_FILE_PATH = r"C:\Users\fzh\Desktop\pythonProject1\stage1_test.jsonl"
OUTPUT_FILE_PATH = "prediction-6.jsonl"

# ------------------- 2. 完整的法条知识库 -------------------
COMPLETE_LEGAL_ARTICLES = {
    # 侵权责任与赔偿
    "误工费": [
        "《中华人民共和国民法典》第一千一百七十九条",
        "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第七条"
    ],
    "医疗费": [
        "《中华人民共和国民法典》第一千一百七十九条",
        "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第六条"
    ],
    "护理费": [
        "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第八条"
    ],
    "交通费": [
        "《中华人民共和国民法典》第一千一百七十九条",
        "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第九条"
    ],
    "残疾赔偿金": [
        "《中华人民共和国民法典》第一千一百七十九条",
        "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第十二条"
    ],
    "死亡赔偿金": [
        "《中华人民共和国民法典》第一千一百七十九条",
        "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第十五条"
    ],
    "精神损害抚慰金": [
        "《中华人民共和国民法典》第一千一百八十三条",
        "《最高人民法院关于确定民事侵权精神损害赔偿责任若干问题的解释》第五条"
    ],

    # 交通违章
    "闯红灯": [
        "《道路交通安全违法行为记分管理办法》第八条",
        "《中华人民共和国道路交通安全法》第九十条"
    ],
    "超速": [
        "《道路交通安全违法行为记分管理办法》第九条",
        "《中华人民共和国道路交通安全法》第九十九条"
    ],
    "酒驾": [
        "《道路交通安全法》第九十一条",
        "《道路交通安全违法行为记分管理办法》第八条"
    ],
    "醉驾": [
        "《道路交通安全法》第九十一条"
    ],

    # 税费相关
    "个人所得税": [
        "《中华人民共和国个人所得税法》第三条"
    ],
    "增值税": [
        "《中华人民共和国增值税暂行条例》第二条"
    ],

    # 合同违约
    "违约金": [
        "《中华人民共和国民法典》第五百八十五条"
    ],
    "定金": [
        "《中华人民共和国民法典》第五百八十六条"
    ],

    # 劳动争议
    "经济补偿金": [
        "《中华人民共和国劳动合同法》第四十六条",
        "《中华人民共和国劳动合同法》第四十七条"
    ],
    "加班费": [
        "《中华人民共和国劳动法》第四十四条"
    ],
    "双倍工资": [
        "《中华人民共和国劳动合同法》第八十二条"
    ],

    # 通用法条（保底）
    "通用侵权": [
        "《中华人民共和国民法典》第一千一百七十九条",
        "《中华人民共和国民法典》第一千一百八十四条"
    ],
    "通用合同": [
        "《中华人民共和国民法典》第四百六十四条",
        "《中华人民共和国民法典》第五百七十七条"
    ],
    "通用劳动": [
        "《中华人民共和国劳动法》第三条",
        "《中华人民共和国劳动合同法》第三条"
    ]
}

# ------------------- 3. 优化的Prompt模板 -------------------
PROMPT_TEMPLATE = """
你需要处理法律数值计算问题，严格按照以下3个步骤输出结果：

步骤1：分析计算逻辑
- 提取问题中的关键数值
- 说明具体计算过程
- 得出最终计算结果

步骤2：确定法律领域
- 分析问题涉及的法律领域
- 提取核心法律关键词

步骤3：输出结构化结果

问题内容：{query}

最终输出格式（严格按此结构）：
reasoning_content：[步骤1的思考过程，包含完整计算逻辑]
numerical_answer：[步骤1的数值结果列表，保留2位小数]
legal_keyword：[步骤2的核心法律关键词，仅1-2个词]

示例：
reasoning_content：张某无固定收入且无法提供最近三年的平均收入证明，按照相同或相近行业上一年度职工的平均工资计算。所以张某应得的误工费为80,000元/365天 x 5天 = 1,095.89元。
numerical_answer：[1095.89]
legal_keyword：误工费
"""


# ------------------- 4. 工具函数 -------------------
def load_test_data():
    """加载test.jsonl测试数据"""
    test_data = []
    with open(TEST_FILE_PATH, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if "id" not in data or "query" not in data:
                    continue
                test_data.append(data)
            except json.JSONDecodeError:
                continue
    return test_data


def call_baseline_model(query):
    """调用基线模型"""
    prompt = PROMPT_TEMPLATE.format(query=query)

    response = Generation.call(
        model=BASE_MODEL_NAME,
        prompt=prompt,
        api_key=DASHSCOPE_API_KEY,
        parameters={
            "temperature": 0.05,
            "max_tokens": 1024,
            "top_p": 0.9,
            "response_format": {"type": "text"}
        }
    )

    if response.status_code != 200:
        raise Exception(f"基线模型调用失败：状态码{response.status_code}")

    model_output = response.output.text.strip()
    return parse_model_output(model_output)


def parse_model_output(model_output):
    """解析模型输出"""
    # 提取思考过程
    reasoning_match = re.search(r'reasoning_content：(.*?)(?=numerical_answer：|legal_keyword：|$)', model_output,
                                re.DOTALL)
    reasoning = reasoning_match.group(1).strip() if reasoning_match else "未解析出思考过程"

    # 提取数值结果
    num_match = re.search(r'numerical_answer：(\[.*?\])', model_output)
    if num_match:
        try:
            num_list = json.loads(num_match.group(1))
            if isinstance(num_list, list) and len(num_list) > 0 and isinstance(num_list[0], (int, float)):
                numerical = round(float(num_list[0]), 2)
                numerical_answer = [numerical]
            else:
                numerical_answer = [0.00]
        except (json.JSONDecodeError, TypeError):
            numerical_answer = [0.00]
    else:
        numerical_answer = [0.00]

    # 提取法条关键词
    keyword_match = re.search(r'legal_keyword：(.*)', model_output, re.DOTALL)
    legal_keyword = keyword_match.group(1).strip() if keyword_match else "未提取到关键词"

    return reasoning, numerical_answer, legal_keyword


def smart_match_legal_articles(legal_keyword, reasoning_content):
    """智能匹配法条，确保总有明确的法条输出"""
    # 1. 精确匹配
    if legal_keyword in COMPLETE_LEGAL_ARTICLES:
        print(f"精确匹配: {legal_keyword}")
        return COMPLETE_LEGAL_ARTICLES[legal_keyword]

    # 2. 同义词映射
    synonym_map = {
        "医疗费赔偿": "医疗费", "护理费赔偿": "护理费", "交通费赔偿": "交通费",
        "误工费赔偿": "误工费", "闯红灯扣分": "闯红灯", "超速扣分": "超速",
        "违约金支付": "违约金", "工资薪金": "个人所得税", "劳务报酬": "个人所得税",
        "死亡赔偿": "死亡赔偿金", "残疾赔偿": "残疾赔偿金", "精神赔偿": "精神损害抚慰金",
        "经济补偿": "经济补偿金", "加班工资": "加班费", "双倍工资赔偿": "双倍工资",
        "住院伙食补助": "住院伙食补助费", "营养补助": "营养费", "住宿补助": "住宿费"
    }

    if legal_keyword in synonym_map:
        mapped_keyword = synonym_map[legal_keyword]
        if mapped_keyword in COMPLETE_LEGAL_ARTICLES:
            print(f"同义词匹配: {legal_keyword} -> {mapped_keyword}")
            return COMPLETE_LEGAL_ARTICLES[mapped_keyword]

    # 3. 关键词包含匹配
    for legal_type in COMPLETE_LEGAL_ARTICLES:
        if legal_keyword in legal_type:
            print(f"关键词包含匹配: {legal_keyword} -> {legal_type}")
            return COMPLETE_LEGAL_ARTICLES[legal_type]

    # 4. 基于推理内容分析匹配
    reasoning_lower = reasoning_content.lower()
    if any(word in reasoning_lower for word in ["工资", "收入", "误工", "赔偿", "损害"]):
        print(f"推理分析匹配侵权类: {legal_keyword}")
        return COMPLETE_LEGAL_ARTICLES["误工费"]
    elif any(word in reasoning_lower for word in ["税", "税率", "缴纳", "个税"]):
        print(f"推理分析匹配税务类: {legal_keyword}")
        return COMPLETE_LEGAL_ARTICLES["个人所得税"]
    elif any(word in reasoning_lower for word in ["合同", "违约", "定金", "协议"]):
        print(f"推理分析匹配合同类: {legal_keyword}")
        return COMPLETE_LEGAL_ARTICLES["违约金"]
    elif any(word in reasoning_lower for word in ["劳动", "加班", "补偿", "工资", "离职"]):
        print(f"推理分析匹配劳动类: {legal_keyword}")
        return COMPLETE_LEGAL_ARTICLES["经济补偿金"]
    elif any(word in reasoning_lower for word in ["交通", "违章", "罚款", "驾驶", "扣分"]):
        print(f"推理分析匹配交通类: {legal_keyword}")
        return COMPLETE_LEGAL_ARTICLES["闯红灯"]

    # 5. 基于关键词类型返回通用法条
    if any(word in legal_keyword for word in ["费", "赔偿", "补偿", "损害"]):
        print(f"通用侵权匹配: {legal_keyword}")
        return COMPLETE_LEGAL_ARTICLES["通用侵权"]
    elif any(word in legal_keyword for word in ["税", "税率"]):
        print(f"通用税务匹配: {legal_keyword}")
        return COMPLETE_LEGAL_ARTICLES["个人所得税"]
    elif any(word in legal_keyword for word in ["合同", "协议", "违约"]):
        print(f"通用合同匹配: {legal_keyword}")
        return COMPLETE_LEGAL_ARTICLES["通用合同"]
    elif any(word in legal_keyword for word in ["劳动", "工资", "加班"]):
        print(f"通用劳动匹配: {legal_keyword}")
        return COMPLETE_LEGAL_ARTICLES["通用劳动"]
    else:
        print(f"默认通用侵权匹配: {legal_keyword}")
        return COMPLETE_LEGAL_ARTICLES["通用侵权"]


# ------------------- 5. 结果生成函数 -------------------
def generate_evaluation_file(test_data):
    """生成最终输出文件"""
    with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as f:
        for data in test_data:
            data_id = data["id"]
            query = data["query"]
            print(f"开始处理ID：{data_id}，问题：{query[:60]}...")

            try:
                # 调用基线模型获取核心信息
                reasoning, numerical_answer, legal_keyword = call_baseline_model(query)

                # 智能匹配法条（确保总有明确的法条输出）
                article_answer = smart_match_legal_articles(legal_keyword, reasoning)

                # 组装输出数据（严格符合指定格式）
                output_data = {
                    "id": data_id,
                    "reasoning_content": reasoning,
                    "numerical_answer": numerical_answer,
                    "article_answer": article_answer
                }
                f.write(json.dumps(output_data, ensure_ascii=False) + '\n')
                print(f"ID：{data_id} 处理完成 - 关键词: {legal_keyword}, 法条数: {len(article_answer)}")

            except Exception as e:
                error_msg = f"ID：{data_id} 处理失败：{str(e)}"
                print(error_msg)
                # 即使出错也确保输出明确的法条
                error_data = {
                    "id": data_id,
                    "reasoning_content": f"处理异常：{error_msg}",
                    "numerical_answer": [0.00],
                    "article_answer": COMPLETE_LEGAL_ARTICLES["通用侵权"]
                }
                f.write(json.dumps(error_data, ensure_ascii=False) + '\n')

    print(f"\n所有数据处理结束，结果文件已保存至：{OUTPUT_FILE_PATH}")


# ------------------- 6. 主函数 -------------------
if __name__ == "__main__":
    print(f"===== 开始运行qwen3-235b-a22b-instruct-2507基线模型处理流程 =====")

    # 加载测试数据
    test_data = load_test_data()
    print(f"成功加载 {len(test_data)} 条有效测试数据")
    if not test_data:
        print("无有效测试数据，程序退出")
        exit()

    # 生成结果文件
    generate_evaluation_file(test_data)
    print("===== 流程结束 =====")