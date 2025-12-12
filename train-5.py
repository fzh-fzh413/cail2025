import json
import re
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity
from dashscope import Generation

# ------------------- 1. 核心配置 -------------------
BASE_MODEL_NAME = "qwen3-235b-a22b-instruct-2507"
DASHSCOPE_API_KEY = "sk-653bf07ab1aa466099d80a3a275afdb4"
TEST_FILE_PATH = r"C:\Users\fzh\Desktop\pythonProject1\stage0_test.jsonl"
OUTPUT_FILE_PATH = "evaluation-8.jsonl"

# 语义匹配配置 - 使用更简单的实现
SEMANTIC_MATCH_ENABLED = True
SIMILARITY_THRESHOLD = 0.6

# ------------------- 2. 扩展的法条知识库 -------------------
LEGAL_KNOWLEDGE_BASE = {
    # 侵权责任与赔偿
    "误工费": {
        "articles": [
            "《中华人民共和国民法典》第一千一百七十九条",
            "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第七条"
        ],
        "keywords": ["误工费", "误工损失", "工资损失", "收入损失", "误工时间", "工资标准", "无法工作", "收入减少"],
        "description": "因侵权行为导致受害人无法正常工作而造成的收入损失赔偿"
    },
    "医疗费": {
        "articles": [
            "《中华人民共和国民法典》第一千一百七十九条",
            "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第六条"
        ],
        "keywords": ["医疗费", "医药费", "治疗费", "住院费", "诊疗费", "康复费", "检查费", "手术费"],
        "description": "因侵权行为导致的医疗相关费用赔偿"
    },
    "护理费": {
        "articles": [
            "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第八条"
        ],
        "keywords": ["护理费", "护理人员", "护理依赖", "护理期限", "护理标准", "照顾费用", "看护费"],
        "description": "因伤残需要他人护理而产生的费用"
    },
    "交通费": {
        "articles": [
            "《中华人民共和国民法典》第一千一百七十九条",
            "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第九条"
        ],
        "keywords": ["交通费", "交通费用", "车费", "交通支出", "往返费用", "出租车费", "公交费"],
        "description": "因就医或处理纠纷实际发生的交通费用"
    },
    "残疾赔偿金": {
        "articles": [
            "《中华人民共和国民法典》第一千一百七十九条",
            "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第十二条"
        ],
        "keywords": ["残疾赔偿金", "伤残赔偿", "残疾补偿", "伤残等级", "劳动能力丧失", "残疾补助"],
        "description": "因伤残导致劳动能力丧失的赔偿"
    },
    "死亡赔偿金": {
        "articles": [
            "《中华人民共和国民法典》第一千一百七十九条",
            "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第十五条"
        ],
        "keywords": ["死亡赔偿金", "死亡补偿", "丧葬费", "死亡损失", "生命权侵害", "死亡补助"],
        "description": "因侵权行为导致死亡的赔偿"
    },
    "精神损害抚慰金": {
        "articles": [
            "《中华人民共和国民法典》第一千一百八十三条",
            "《最高人民法院关于确定民事侵权精神损害赔偿责任若干问题的解释》第五条"
        ],
        "keywords": ["精神损害抚慰金", "精神损失费", "精神赔偿", "精神痛苦", "精神损害", "精神补偿"],
        "description": "因侵权行为造成严重精神损害的赔偿"
    },

    # 交通违章
    "闯红灯": {
        "articles": ["《道路交通安全违法行为记分管理办法》第八条"],
        "keywords": ["闯红灯", "违反交通信号", "红灯", "交通信号违反", "冲红灯"],
        "description": "违反交通信号灯通行的行为"
    },
    "超速": {
        "articles": ["《道路交通安全违法行为记分管理办法》第九条"],
        "keywords": ["超速", "超速行驶", "超速驾驶", "超速20%", "超速50%", "超速行驶", "超速违章"],
        "description": "超过规定速度行驶的违法行为"
    },
    "酒驾": {
        "articles": [
            "《道路交通安全法》第九十一条",
            "《道路交通安全违法行为记分管理办法》第八条"
        ],
        "keywords": ["酒驾", "酒后驾驶", "饮酒驾驶", "酒精含量", "酒后驾车", "醉驾"],
        "description": "饮酒后驾驶机动车的违法行为"
    },

    # 税费相关
    "个人所得税": {
        "articles": ["《中华人民共和国个人所得税法》第三条"],
        "keywords": ["个人所得税", "个税", "工资薪金", "劳务报酬", "稿酬", "特许权使用费", "工资税"],
        "description": "个人所得收入应缴纳的税款"
    },
    "增值税": {
        "articles": ["《中华人民共和国增值税暂行条例》第二条"],
        "keywords": ["增值税", "增值税率", "销项税额", "进项税额", "增值税发票", "增值税缴纳"],
        "description": "商品或服务增值部分应缴纳的税款"
    },

    # 合同违约
    "违约金": {
        "articles": ["《中华人民共和国民法典》第五百八十五条"],
        "keywords": ["违约金", "违约赔偿", "合同违约", "违约责任", "违约支付", "违约罚款"],
        "description": "合同一方违约时应向另一方支付的赔偿金"
    },
    "定金": {
        "articles": ["《中华人民共和国民法典》第五百八十六条"],
        "keywords": ["定金", "定金罚则", "定金合同", "定金担保", "定金返还", "订金"],
        "description": "合同履行的担保方式"
    },

    # 劳动争议
    "经济补偿金": {
        "articles": [
            "《中华人民共和国劳动合同法》第四十六条",
            "《中华人民共和国劳动合同法》第四十七条"
        ],
        "keywords": ["经济补偿金", "解除合同补偿", "经济补偿", "离职补偿", "工作年限补偿", "裁员补偿"],
        "description": "劳动合同解除或终止时用人单位支付的经济补偿"
    },
    "加班费": {
        "articles": ["《中华人民共和国劳动法》第四十四条"],
        "keywords": ["加班费", "加班工资", "延长工作时间", "休息日加班", "法定节假日加班", "加班报酬"],
        "description": "延长工作时间应支付的额外工资"
    }
}


# ------------------- 3. 简化的语义匹配器 -------------------
class SimpleSemanticMatcher:
    def __init__(self):
        self.legal_texts = []
        self.legal_types = []
        self.build_legal_index()

    def build_legal_index(self):
        """构建法条文本索引"""
        print("正在构建法条文本索引...")

        for legal_type, info in LEGAL_KNOWLEDGE_BASE.items():
            # 法条类型名称
            self.legal_texts.append(legal_type)
            self.legal_types.append(legal_type)

            # 关键词
            for keyword in info["keywords"]:
                self.legal_texts.append(keyword)
                self.legal_types.append(legal_type)

            # 描述
            self.legal_texts.append(info["description"])
            self.legal_types.append(legal_type)

        print(f"法条索引构建完成，共{len(self.legal_texts)}个文本")

    def calculate_similarity(self, text1, text2):
        """计算两个文本的相似度（基于字符重叠）"""
        # 简单的基于字符重叠的相似度计算
        words1 = set(text1)
        words2 = set(text2)

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def find_similar_legal_types(self, query, top_k=3):
        """查找与查询最相似的法条类型"""
        if not self.legal_texts:
            return []

        # 计算相似度
        similarities = []
        for i, legal_text in enumerate(self.legal_texts):
            similarity = self.calculate_similarity(query, legal_text)
            legal_type = self.legal_types[i]
            similarities.append((legal_type, similarity, legal_text))

        # 按相似度排序并去重
        similarities.sort(key=lambda x: x[1], reverse=True)

        seen_types = set()
        results = []
        for legal_type, similarity, matched_text in similarities:
            if legal_type not in seen_types and similarity >= SIMILARITY_THRESHOLD:
                results.append({
                    "legal_type": legal_type,
                    "similarity": similarity,
                    "matched_text": matched_text,
                    "articles": LEGAL_KNOWLEDGE_BASE[legal_type]["articles"]
                })
                seen_types.add(legal_type)
                if len(results) >= top_k:
                    break

        return results


# 初始化语义匹配器
semantic_matcher = None
if SEMANTIC_MATCH_ENABLED:
    try:
        semantic_matcher = SimpleSemanticMatcher()
        print("语义匹配模型初始化成功")
    except Exception as e:
        print(f"语义匹配模型初始化失败: {e}")
        SEMANTIC_MATCH_ENABLED = False

# ------------------- 4. Prompt优化 -------------------
PROMPT_TEMPLATE = """
你需要处理法律数值计算问题，严格按照以下3个步骤输出结果，**仅保留最终输出内容，不添加任何多余解释**：

步骤1：输出思考过程（key: reasoning_content）
- 先明确问题类型（从"补偿类型/费用类型/罚金类型/税费税率类型/交通违章行为扣分类型"中选择1个）；
- 提取问题中的关键数值（如"年平均工资80000元""误工5天"）；
- 说明具体计算逻辑（如"年工资÷365天×误工天数"）。

步骤2：输出数值结果（key: numerical_answer）
- 仅保留计算结果，保留2位小数（整数需补两位小数，如6→6.00）；
- 用列表包裹，格式示例：[1095.89]。

步骤3：输出法条关键词（key: legal_keyword）
- 提取1-2个能代表问题核心的关键词（用于匹配法条，如"误工费""闯红灯""个人所得税"）；
- 仅输出关键词，无需额外文字。

问题内容：{query}

最终输出格式（用中文标点，严格按此结构）：
reasoning_content：[步骤1的思考过程]
numerical_answer：[步骤2的数值列表]
legal_keyword：[步骤3的关键词]
"""


# ------------------- 5. 工具函数 -------------------
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


def enhanced_match_legal_articles(legal_keyword, query=""):
    """增强的法条匹配：语义匹配 + 关键词匹配"""
    results = []

    # 1. 语义匹配（优先）
    if SEMANTIC_MATCH_ENABLED and semantic_matcher:
        # 使用关键词和完整查询进行语义匹配
        search_text = f"{legal_keyword} {query}" if query else legal_keyword
        semantic_results = semantic_matcher.find_similar_legal_types(search_text)

        for result in semantic_results:
            if result["similarity"] >= SIMILARITY_THRESHOLD:
                results.extend(result["articles"])
                print(f"语义匹配: {legal_keyword} -> {result['legal_type']} (相似度: {result['similarity']:.3f})")

        if results:
            return list(set(results))  # 去重

    # 2. 精确关键词匹配
    if legal_keyword in LEGAL_KNOWLEDGE_BASE:
        print(f"精确匹配: {legal_keyword}")
        return LEGAL_KNOWLEDGE_BASE[legal_keyword]["articles"]

    # 3. 同义词映射
    synonym_map = {
        "医疗费赔偿": "医疗费", "护理费赔偿": "护理费", "交通费赔偿": "交通费",
        "个人所得税综合所得": "个人所得税", "增值税一般纳税人": "增值税",
        "行政罚款交通违法": "交通罚款", "误工费赔偿": "误工费",
        "闯红灯扣分": "闯红灯", "超速扣分": "超速", "违约金支付": "违约金",
        "工资薪金": "个人所得税", "劳务报酬": "个人所得税", "稿酬所得": "个人所得税",
        "死亡赔偿": "死亡赔偿金", "残疾赔偿": "残疾赔偿金", "精神赔偿": "精神损害抚慰金",
        "住院伙食补助": "住院伙食补助费", "营养补助": "营养费", "住宿补助": "住宿费",
        "经济补偿": "经济补偿金", "加班工资": "加班费", "双倍工资赔偿": "双倍工资"
    }

    if legal_keyword in synonym_map:
        mapped_keyword = synonym_map[legal_keyword]
        if mapped_keyword in LEGAL_KNOWLEDGE_BASE:
            print(f"同义词匹配: {legal_keyword} -> {mapped_keyword}")
            return LEGAL_KNOWLEDGE_BASE[mapped_keyword]["articles"]

    # 4. 关键词包含匹配
    for legal_type, info in LEGAL_KNOWLEDGE_BASE.items():
        if legal_keyword in legal_type or any(legal_keyword in kw for kw in info["keywords"]):
            print(f"关键词包含匹配: {legal_keyword} -> {legal_type}")
            return info["articles"]

    # 5. 分类匹配
    category_match = category_based_matching(legal_keyword)
    if category_match:
        return category_match

    # 6. 返回通用法条
    return get_general_legal_articles(legal_keyword)


def category_based_matching(keyword):
    """基于问题类型的分类匹配"""
    category_patterns = {
        "赔偿": ["误工费", "医疗费", "护理费", "交通费", "残疾赔偿金", "死亡赔偿金", "精神损害抚慰金"],
        "交通": ["闯红灯", "超速", "酒驾", "违停", "不系安全带"],
        "税务": ["个人所得税", "增值税", "企业所得税", "消费税"],
        "合同": ["违约金", "定金", "预付款"],
        "劳动": ["经济补偿金", "加班费", "双倍工资"],
    }

    for category, legal_types in category_patterns.items():
        if category in keyword:
            for legal_type in legal_types:
                if legal_type in LEGAL_KNOWLEDGE_BASE:
                    return LEGAL_KNOWLEDGE_BASE[legal_type]["articles"]

    return None


def get_general_legal_articles(keyword):
    """根据关键词类型返回通用法条"""
    if any(word in keyword for word in ["费", "赔偿", "补偿"]):
        return ["《中华人民共和国民法典》第一千一百七十九条"]
    elif any(word in keyword for word in ["税", "税率"]):
        return ["《中华人民共和国税收征收管理法》相关条款"]
    elif any(word in keyword for word in ["违章", "违规", "处罚", "罚款"]):
        return ["《中华人民共和国行政处罚法》第九条"]
    elif any(word in keyword for word in ["合同", "协议", "约定"]):
        return ["《中华人民共和国民法典》第四百六十四条"]
    elif any(word in keyword for word in ["劳动", "工资", "加班"]):
        return ["《中华人民共和国劳动法》相关条款"]
    else:
        return ["《中华人民共和国民法典》相关条款"]


# ------------------- 6. 结果生成函数 -------------------
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
                # 使用增强的法条匹配
                article_answer = enhanced_match_legal_articles(legal_keyword, query)
                # 组装输出数据
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
                error_data = {
                    "id": data_id,
                    "reasoning_content": f"处理异常：{error_msg}",
                    "numerical_answer": [0.00],
                    "article_answer": ["数据处理异常，需人工核查"]
                }
                f.write(json.dumps(error_data, ensure_ascii=False) + '\n')

    print(f"\n所有数据处理结束，结果文件已保存至：{OUTPUT_FILE_PATH}")


# ------------------- 7. 主函数 -------------------
if __name__ == "__main__":
    print(f"===== 开始运行qwen3-235b-a22b-instruct-2507基线模型处理流程 =====")
    print(f"语义匹配功能: {'已启用' if SEMANTIC_MATCH_ENABLED else '未启用'}")

    # 加载测试数据
    test_data = load_test_data()
    print(f"成功加载 {len(test_data)} 条有效测试数据")
    if not test_data:
        print("无有效测试数据，程序退出")
        exit()

    # 生成结果文件
    generate_evaluation_file(test_data)
    print("===== 流程结束 =====")