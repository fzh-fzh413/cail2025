import json
import re

import requests
from dashscope import Generation  # 通义千问系列模型统一通过dashscope调用

# ------------------- 1. 核心配置（适配基线模型） -------------------
# 1.1 模型与密钥配置
BASE_MODEL_NAME = "qwen3-235b-a22b-instruct-2507"  # 基线模型名称
DASHSCOPE_API_KEY = "sk-653bf07ab1aa466099d80a3a275afdb4"  # 替换为你的阿里云dashscope密钥
# 1.2 文件路径配置
TEST_FILE_PATH = r"C:\Users\fzh\Desktop\pythonProject1\stage0_test.jsonl"  # 输入测试集
OUTPUT_FILE_PATH = "evaluation-8.jsonl"  # 输出结果文件
# 1.3 预置法条库（覆盖五类计算场景，确保法条准确性）
LEGAL_ARTICLES = {
    # 补偿类型
    "误工费": [
        "《中华人民共和国民法典》第一千一百七十九条",
        "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第七条"
    ],
    "医疗费": ["《中华人民共和国民法典》第一千一百七十九条"],
    "护理费": ["《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第八条"],
    "交通费": ["《中华人民共和国民法典》第一千一百七十九条"],
    "住宿费": ["《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第九条"],
    "住院伙食补助费": ["《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第十条"],
    "营养费": ["《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第十一条"],
    "残疾赔偿金": ["《中华人民共和国民法典》第一千一百七十九条", "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第十二条"],
    "死亡赔偿金": ["《中华人民共和国民法典》第一千一百七十九条", "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第十五条"],
    "精神损害抚慰金": ["《中华人民共和国民法典》第一千一百八十三条", "《最高人民法院关于确定民事侵权精神损害赔偿责任若干问题的解释》第五条"],

    # 交通违章扣分类型（扩展）
    "闯红灯": ["《道路交通安全违法行为记分管理办法》第八条"],
    "超速": ["《道路交通安全违法行为记分管理办法》第九条"],
    "超速20%以上": ["《道路交通安全违法行为记分管理办法》第九条"],
    "超速50%以上": ["《道路交通安全违法行为记分管理办法》第九条"],
    "酒驾": ["《道路交通安全法》第九十一条", "《道路交通安全违法行为记分管理办法》第八条"],
    "醉驾": ["《道路交通安全法》第九十一条"],
    "无证驾驶": ["《道路交通安全法》第九十九条"],
    "肇事逃逸": ["《道路交通安全法》第九十九条", "《道路交通安全违法行为记分管理办法》第八条"],
    "不系安全带": ["《道路交通安全法》第五十一条", "《道路交通安全违法行为记分管理办法》第十二条"],
    "开车打电话": ["《道路交通安全法实施条例》第六十二条", "《道路交通安全违法行为记分管理办法》第十一条"],
    "不按导向车道行驶": ["《道路交通安全违法行为记分管理办法》第十一条"],
    "违停": ["《道路交通安全法》第五十六条", "《道路交通安全违法行为记分管理办法》第十一条"],

    # 税费税率类型（扩展）
    "个人所得税": ["《中华人民共和国个人所得税法》第三条"],
    "工资薪金所得": ["《中华人民共和国个人所得税法》第三条"],
    "劳务报酬所得": ["《中华人民共和国个人所得税法》第三条"],
    "稿酬所得": ["《中华人民共和国个人所得税法》第三条"],
    "特许权使用费所得": ["《中华人民共和国个人所得税法》第三条"],
    "经营所得": ["《中华人民共和国个人所得税法》第三条"],
    "增值税": ["《中华人民共和国增值税暂行条例》第二条"],
    "企业所得税": ["《中华人民共和国企业所得税法》第四条"],
    "消费税": ["《中华人民共和国消费税暂行条例》第二条"],
    "房产税": ["《中华人民共和国房产税暂行条例》第三条"],
    "契税": ["《中华人民共和国契税法》第三条"],
    "印花税": ["《中华人民共和国印花税法》附件《印花税税目税率表》"],

    # 罚金违约金类型（扩展）
    "违约金": ["《中华人民共和国民法典》第五百八十五条"],
    "逾期付款违约金": ["《中华人民共和国民法典》第五百八十五条"],
    "合同违约金": ["《中华人民共和国民法典》第五百八十五条"],
    "行政罚款": ["《中华人民共和国行政处罚法》第九条"],
    "交通罚款": ["《中华人民共和国道路交通安全法》第九十条"],
    "滞纳金": ["《中华人民共和国行政强制法》第四十五条"],

    # 费用计算类型（扩展）
    "租赁费": ["《中华人民共和国民法典》第七百零三条"],
    "借款利息": ["《中华人民共和国民法典》第六百八十条"],
    "工程款": ["《中华人民共和国民法典》第七百九十三条"],
    "货款": ["《中华人民共和国民法典》第五百九十五条"],
    "服务费": ["《中华人民共和国民法典》第九百三十七条"],
    "咨询费": ["《中华人民共和国民法典》第九百五十一条"],

    # 劳动争议类型
    "经济补偿金": ["《中华人民共和国劳动合同法》第四十六条", "《中华人民共和国劳动合同法》第四十七条"],
    "赔偿金": ["《中华人民共和国劳动合同法》第八十七条"],
    "双倍工资": ["《中华人民共和国劳动合同法》第八十二条"],
    "加班费": ["《中华人民共和国劳动法》第四十四条"],
    "年休假工资": ["《职工带薪年休假条例》第五条"],

    # 知识产权类型
    "著作权": ["《中华人民共和国著作权法》第十条"],
    "专利权": ["《中华人民共和国专利法》第十一条"],
    "商标权": ["《中华人民共和国商标法》第五十七条"],

    # 合同纠纷类型
    "定金": ["《中华人民共和国民法典》第五百八十六条"],
    "预付款": ["《中华人民共和国民法典》第五百八十六条"],
    "质量保证金": ["《中华人民共和国民法典》第五百八十六条"],

    # 保险理赔类型
    "保险金": ["《中华人民共和国保险法》第二条"],
    "交强险": ["《机动车交通事故责任强制保险条例》第二十一条"],
    "商业险": ["《中华人民共和国保险法》第二条"],
}

# ------------------- 2. Prompt优化（贴合基线模型指令习惯） -------------------
# 针对qwen3-235b-a22b-instruct-2507的指令特点：明确任务边界、分步骤引导、强调格式一致性
PROMPT_TEMPLATE = """
你需要处理法律数值计算问题，严格按照以下3个步骤输出结果，**仅保留最终输出内容，不添加任何多余解释**：

步骤1：输出思考过程（key: reasoning_content）
- 先明确问题类型（从“补偿类型/费用类型/罚金类型/税费税率类型/交通违章行为扣分类型”中选择1个）；
- 提取问题中的关键数值（如“年平均工资80000元”“误工5天”）；
- 说明具体计算逻辑（如“年工资÷365天×误工天数”）。

步骤2：输出数值结果（key: numerical_answer）
- 仅保留计算结果，保留2位小数（整数需补两位小数，如6→6.00）；
- 用列表包裹，格式示例：[1095.89]。

步骤3：输出法条关键词（key: legal_keyword）
- 提取1-2个能代表问题核心的关键词（用于匹配法条，如“误工费”“闯红灯”“个人所得税 综合所得”）；
- 仅输出关键词，无需额外文字。

问题内容：{query}

最终输出格式（用中文标点，严格按此结构）：
reasoning_content：[步骤1的思考过程]
numerical_answer：[步骤2的数值列表]
legal_keyword：[步骤3的关键词]
"""


# ------------------- 3. 工具函数（适配基线模型调用与解析） -------------------
def load_test_data():
    """加载test.jsonl测试数据，处理空行和格式异常"""
    test_data = []
    with open(TEST_FILE_PATH, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                print(f"跳过第{line_num}行空行")
                continue
            try:
                data = json.loads(line)
                # 校验必要字段
                if "id" not in data or "query" not in data:
                    print(f"第{line_num}行数据缺少id或query字段，跳过")
                    continue
                test_data.append(data)
            except json.JSONDecodeError as e:
                print(f"第{line_num}行数据格式错误：{str(e)}，跳过")
    return test_data


def call_baseline_model(query):
    """调用qwen3-235b-a22b-instruct-2507基线模型，获取结构化结果"""
    # 组装适配模型的Prompt
    prompt = PROMPT_TEMPLATE.format(query=query)

    # 基线模型调用参数：根据官方建议设置（低温确保结果稳定，长上下文适配）
    response = Generation.call(
        model=BASE_MODEL_NAME,
        prompt=prompt,
        api_key=DASHSCOPE_API_KEY,
        parameters={
            "temperature": 0.05,  # 基线模型低温度更易输出结构化结果
            "max_tokens": 1024,  # 足够覆盖计算逻辑与关键词输出
            "top_p": 0.9,  # 控制输出多样性，优先高概率结果
            "response_format": {"type": "text"}  # 基线模型默认文本输出格式
        }
    )

    # 模型响应校验与解析
    if response.status_code != 200:
        raise Exception(f"基线模型调用失败：状态码{response.status_code}，消息{response.message}")

    model_output = response.output.text.strip()
    return parse_model_output(model_output)


def parse_model_output(model_output):
    """解析基线模型输出，提取思考过程、数值结果、法条关键词"""
    # 1. 提取思考过程（reasoning_content）
    reasoning_match = re.search(r'reasoning_content：(.*?)(?=numerical_answer：|legal_keyword：|$)', model_output,
                                re.DOTALL)
    reasoning = reasoning_match.group(1).strip() if reasoning_match else "未解析出思考过程"

    # 2. 提取数值结果（numerical_answer）
    num_match = re.search(r'numerical_answer：(\[.*?\])', model_output)
    if num_match:
        try:
            num_list = json.loads(num_match.group(1))
            # 校验数值格式，确保保留两位小数
            if isinstance(num_list, list) and len(num_list) > 0 and isinstance(num_list[0], (int, float)):
                numerical = round(float(num_list[0]), 2)
                numerical_answer = [numerical]
            else:
                numerical_answer = [0.00]
        except (json.JSONDecodeError, TypeError):
            numerical_answer = [0.00]
    else:
        numerical_answer = [0.00]

    # 3. 提取法条关键词（legal_keyword）
    keyword_match = re.search(r'legal_keyword：(.*)', model_output, re.DOTALL)
    legal_keyword = keyword_match.group(1).strip() if keyword_match else "未提取到关键词"

    return reasoning, numerical_answer, legal_keyword


def match_legal_articles(legal_keyword):
    """根据关键词智能匹配法条，支持同义词和层级匹配"""
    # 1. 精确匹配
    if legal_keyword in LEGAL_ARTICLES:
        return LEGAL_ARTICLES[legal_keyword]

    # 2. 同义词映射
    synonym_map = {
        "医疗费赔偿": "医疗费",
        "护理费赔偿": "护理费",
        "交通费赔偿": "交通费",
        "个人所得税综合所得": "个人所得税",
        "增值税一般纳税人": "增值税",
        "行政罚款交通违法": "交通罚款",
        "护理费人身损害": "护理费",
        "误工费赔偿": "误工费",
        "闯红灯扣分": "闯红灯",
        "超速扣分": "超速",
        "违约金支付": "违约金",
    }

    if legal_keyword in synonym_map:
        return LEGAL_ARTICLES[synonym_map[legal_keyword]]

    # 3. 关键词拆分匹配
    for kw_part in legal_keyword.split():
        for article_key in LEGAL_ARTICLES:
            if kw_part in article_key:
                return LEGAL_ARTICLES[article_key]

    # 4. 包含关系匹配
    for article_key in LEGAL_ARTICLES:
        if legal_keyword in article_key or article_key in legal_keyword:
            return LEGAL_ARTICLES[article_key]

    # 5. 分类匹配（基于问题类型）
    category_keywords = {
        "补偿": ["误工费", "医疗费", "护理费", "交通费", "残疾赔偿金", "死亡赔偿金"],
        "交通": ["闯红灯", "超速", "酒驾", "违停", "不系安全带"],
        "税务": ["个人所得税", "增值税", "企业所得税", "消费税"],
        "合同": ["违约金", "定金", "预付款"],
        "劳动": ["经济补偿金", "加班费", "双倍工资"],
        "费用": ["租赁费", "服务费", "咨询费"]
    }

    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in legal_keyword:
                return LEGAL_ARTICLES[keyword]

    # 6. 返回通用法条
    return get_general_legal_articles(legal_keyword)


def get_general_legal_articles(keyword):
    """根据关键词类型返回通用法条"""
    if any(word in keyword for word in ["费", "赔偿", "补偿"]):
        return ["《中华人民共和国民法典》第一千一百七十九条"]
    elif any(word in keyword for word in ["税", "税率"]):
        return ["建议参考《中华人民共和国税收征收管理法》及相关税种法律"]
    elif any(word in keyword for word in ["违章", "违规", "处罚", "罚款"]):
        return ["《中华人民共和国行政处罚法》第九条"]
    elif any(word in keyword for word in ["合同", "协议", "约定"]):
        return ["《中华人民共和国民法典》第四百六十四条"]
    elif any(word in keyword for word in ["劳动", "工资", "加班"]):
        return ["《中华人民共和国劳动法》相关条款"]
    else:
        return ["《中华人民共和国民法典》相关条款", "建议咨询专业法律人士"]



# ------------------- 4. 结果生成函数（符合evaluation.jsonl格式） -------------------
def generate_evaluation_file(test_data):
    """生成最终输出文件，处理单条数据异常不中断整体流程"""
    with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as f:
        for data in test_data:
            data_id = data["id"]
            query = data["query"]
            print(f"开始处理ID：{data_id}，问题：{query[:60]}...")

            try:
                # 1. 调用基线模型获取核心信息
                reasoning, numerical_answer, legal_keyword = call_baseline_model(query)
                # 2. 匹配法条
                article_answer = match_legal_articles(legal_keyword)
                # 3. 组装输出数据（严格符合提交格式）
                output_data = {
                    "id": data_id,
                    "reasoning_content": reasoning,
                    "numerical_answer": numerical_answer,
                    "article_answer": article_answer
                }
                # 4. 写入JSON行（确保无ASCII转义，格式正确）
                f.write(json.dumps(output_data, ensure_ascii=False) + '\n')
                print(f"ID：{data_id} 处理完成")

            except Exception as e:
                # 单条数据异常处理，不中断后续任务
                error_msg = f"ID：{data_id} 处理失败：{str(e)}"
                print(error_msg)
                # 写入错误标记数据，便于后续排查
                error_data = {
                    "id": data_id,
                    "reasoning_content": f"处理异常：{error_msg}",
                    "numerical_answer": [0.00],
                    "article_answer": ["数据处理异常，需人工核查"]
                }
                f.write(json.dumps(error_data, ensure_ascii=False) + '\n')

    print(f"\n所有数据处理结束，结果文件已保存至：{OUTPUT_FILE_PATH}")


# ------------------- 5. 主函数（流程入口） -------------------
if __name__ == "__main__":
    print(f"===== 开始运行qwen3-235b-a22b-instruct-2507基线模型处理流程 =====")
    # 1. 加载测试数据
    test_data = load_test_data()
    print(f"成功加载 {len(test_data)} 条有效测试数据")
    if not test_data:
        print("无有效测试数据，程序退出")
        exit()
    # 2. 生成结果文件
    generate_evaluation_file(test_data)
    print("===== 流程结束 =====")