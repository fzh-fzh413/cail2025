# -*- coding: utf-8 -*-
import json
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dashscope import Generation

# ------------------- 1. 核心配置 -------------------
BASE_MODEL_NAME = "qwen3-235b-a22b-instruct-2507"
DASHSCOPE_API_KEY = "sk-653bf07ab1aa466099d80a3a275afdb4"
TEST_FILE_PATH = r"C:\Users\fzh\Desktop\pythonProject1\stage0_test.jsonl"
OUTPUT_FILE_PATH = "evaluation-8.jsonl"

# ------------------- 2. 扩展的法条知识库（包含详细描述） -------------------
LEGAL_KNOWLEDGE_BASE = {
    "误工费": {
        "articles": [
            "《中华人民共和国民法典》第一千一百七十九条",
            "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第七条"
        ],
        "description": "误工费是指受害人因侵权行为导致无法正常工作而损失的收入。计算依据是受害人的误工时间和收入状况。有固定收入的按实际减少收入计算，无固定收入的按最近三年平均收入或相同行业平均工资计算。",
        "keywords": ["误工费", "工资损失", "收入减少", "误工时间", "平均工资", "无法工作"]
    },
    "医疗费": {
        "articles": [
            "《中华人民共和国民法典》第一千一百七十九条",
            "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第六条"
        ],
        "description": "医疗费包括医药费、住院费、检查费、治疗费等实际发生的医疗费用。需要医疗机构出具的收款凭证和病历诊断证明。",
        "keywords": ["医疗费", "医药费", "治疗费", "住院费", "检查费", "康复费"]
    },
    "护理费": {
        "articles": [
            "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第八条"
        ],
        "description": "护理费是因伤残需要他人护理而产生的费用。根据护理人员收入状况、护理人数和护理期限确定。有收入的参照误工费计算，无收入的参照当地护工标准。",
        "keywords": ["护理费", "护理人员", "护理期限", "看护费", "照顾费用"]
    },
    "交通费": {
        "articles": [
            "《中华人民共和国民法典》第一千一百七十九条",
            "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第九条"
        ],
        "description": "交通费是受害人及必要陪护人员因就医或转院治疗实际发生的交通费用。需要票据证明，通常按照实际发生的合理费用计算。",
        "keywords": ["交通费", "交通费用", "车费", "往返费用", "就医交通"]
    },
    "残疾赔偿金": {
        "articles": [
            "《中华人民共和国民法典》第一千一百七十九条",
            "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第十二条"
        ],
        "description": "残疾赔偿金根据伤残等级和劳动能力丧失程度计算。按照受诉法院所在地上一年度城镇居民人均可支配收入标准，自定残之日起按20年计算。",
        "keywords": ["残疾赔偿金", "伤残赔偿", "伤残等级", "劳动能力丧失", "残疾补助"]
    },
    "死亡赔偿金": {
        "articles": [
            "《中华人民共和国民法典》第一千一百七十九条",
            "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第十五条"
        ],
        "description": "死亡赔偿金按照受诉法院所在地上一年度城镇居民人均可支配收入标准，按20年计算。60周岁以上的，年龄每增加1岁减少1年。",
        "keywords": ["死亡赔偿金", "死亡补偿", "丧葬费", "生命权侵害"]
    },
    "精神损害抚慰金": {
        "articles": [
            "《中华人民共和国民法典》第一千一百八十三条",
            "《最高人民法院关于确定民事侵权精神损害赔偿责任若干问题的解释》第五条"
        ],
        "description": "精神损害抚慰金在造成严重精神损害时适用。赔偿数额根据侵权人过错程度、侵害手段、后果严重程度等因素确定。",
        "keywords": ["精神损害抚慰金", "精神损失费", "精神赔偿", "精神痛苦"]
    },
    "个人所得税": {
        "articles": [
            "《中华人民共和国个人所得税法》第三条"
        ],
        "description": "个人所得税针对个人所得收入征收。综合所得适用3%-45%超额累进税率，经营所得适用5%-35%税率，利息股息等适用20%比例税率。",
        "keywords": ["个人所得税", "个税", "工资薪金", "劳务报酬", "稿酬", "税率"]
    },
    "增值税": {
        "articles": [
            "《中华人民共和国增值税暂行条例》第二条"
        ],
        "description": "增值税针对商品和服务的增值额征收。基本税率为13%，特定行业适用9%或6%税率。应纳税额=销项税额-进项税额。",
        "keywords": ["增值税", "增值税率", "销项税额", "进项税额", "增值税缴纳"]
    },
    "违约金": {
        "articles": [
            "《中华人民共和国民法典》第五百八十五条"
        ],
        "description": "违约金是合同一方违约时向另一方支付的赔偿金。可以约定具体数额或计算方法。违约金过分高于实际损失的可以请求减少。",
        "keywords": ["违约金", "违约赔偿", "合同违约", "违约责任"]
    },
    "经济补偿金": {
        "articles": [
            "《中华人民共和国劳动合同法》第四十六条",
            "《中华人民共和国劳动合同法》第四十七条"
        ],
        "description": "经济补偿金在劳动合同解除或终止时支付。按劳动者在本单位工作年限，每满一年支付一个月工资。六个月以上不满一年的按一年计算。",
        "keywords": ["经济补偿金", "解除合同补偿", "离职补偿", "工作年限补偿"]
    },
    "加班费": {
        "articles": [
            "《中华人民共和国劳动法》第四十四条"
        ],
        "description": "加班费是延长工作时间的额外工资报酬。工作日加班支付1.5倍工资，休息日加班支付2倍工资，法定节假日加班支付3倍工资。",
        "keywords": ["加班费", "加班工资", "延长工作时间", "休息日加班"]
    }
}


# ------------------- 3. RAG检索器 -------------------
class LegalRAGRetriever:
    def __init__(self):
        self.legal_docs = []
        self.legal_types = []
        self.vectorizer = TfidfVectorizer()
        self.doc_vectors = None
        self.build_legal_corpus()

    def build_legal_corpus(self):
        """构建法律知识语料库"""
        print("正在构建法律知识语料库...")

        for legal_type, info in LEGAL_KNOWLEDGE_BASE.items():
            # 创建丰富的文档表示
            doc_text = f"{legal_type} {info['description']} {' '.join(info['keywords'])} {' '.join(info['articles'])}"
            self.legal_docs.append(doc_text)
            self.legal_types.append(legal_type)

        # 训练TF-IDF向量化器
        if self.legal_docs:
            self.doc_vectors = self.vectorizer.fit_transform(self.legal_docs)
            print(f"语料库构建完成，共{len(self.legal_docs)}个文档")
        else:
            print("语料库构建失败：无文档")

    def retrieve_similar_laws(self, query, top_k=3, similarity_threshold=0.3):
        """检索与查询最相关的法律条款"""
        if self.doc_vectors is None:
            return []

        try:
            # 将查询转换为向量
            query_vector = self.vectorizer.transform([query])

            # 计算相似度
            similarities = cosine_similarity(query_vector, self.doc_vectors)[0]

            # 获取最相似的结果
            results = []
            for i, similarity in enumerate(similarities):
                if similarity >= similarity_threshold:
                    results.append({
                        "legal_type": self.legal_types[i],
                        "similarity": similarity,
                        "articles": LEGAL_KNOWLEDGE_BASE[self.legal_types[i]]["articles"]
                    })

            # 按相似度排序
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]

        except Exception as e:
            print(f"检索失败: {e}")
            return []


# 初始化RAG检索器
rag_retriever = LegalRAGRetriever()

# ------------------- 4. RAG增强的Prompt模板 -------------------
PROMPT_TEMPLATE_RAG = """
你是一个法律计算专家。请处理以下法律数值计算问题，并参考相关法律条文。

问题：{query}

相关法律参考：
{legal_context}

请按照以下步骤处理：

1. 分析计算逻辑：
   - 提取关键数值参数
   - 说明具体计算过程
   - 得出最终计算结果

2. 确定法律依据：
   - 基于相关法律参考确定适用条款
   - 提取核心法律关键词

3. 输出结构化结果

最终输出格式（严格按此结构）：
reasoning_content：[分析计算逻辑，包含完整计算过程]
numerical_answer：[数值结果列表，保留2位小数]
legal_keyword：[核心法律关键词，仅1-2个词]

示例：
reasoning_content：张某无固定收入且无法提供最近三年的平均收入证明，按照相同或相近行业上一年度职工的平均工资计算。所以张某应得的误工费为80,000元/365天 x 5天 = 1,095.89元。
numerical_answer：[1095.89]
legal_keyword：误工费
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


def build_legal_context(query):
    """构建法律上下文"""
    # 使用RAG检索相关法律
    similar_laws = rag_retriever.retrieve_similar_laws(query, top_k=3)

    legal_context = "相关法律条文：\n"
    if similar_laws:
        for i, law in enumerate(similar_laws, 1):
            legal_context += f"{i}. {law['legal_type']}：{LEGAL_KNOWLEDGE_BASE[law['legal_type']]['description']}\n"
            legal_context += f"   法条依据：{'，'.join(law['articles'])}\n"
    else:
        legal_context += "未找到高度相关的具体法律条文，请参考《中华人民共和国民法典》相关条款。\n"

    return legal_context


def call_baseline_model_with_rag(query):
    """使用RAG增强调用基线模型"""
    # 构建法律上下文
    legal_context = build_legal_context(query)

    # 组装Prompt
    prompt = PROMPT_TEMPLATE_RAG.format(
        query=query,
        legal_context=legal_context
    )

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


def rag_enhanced_match_articles(legal_keyword, query):
    """RAG增强的法条匹配"""
    # 使用RAG检索最相关的法律
    similar_laws = rag_retriever.retrieve_similar_laws(f"{legal_keyword} {query}", top_k=2)

    if similar_laws:
        # 返回相似度最高的法条
        best_match = similar_laws[0]
        print(f"RAG匹配: {legal_keyword} -> {best_match['legal_type']} (相似度: {best_match['similarity']:.3f})")
        return best_match["articles"]
    else:
        # 回退到关键词匹配
        return keyword_fallback_match(legal_keyword)


def keyword_fallback_match(legal_keyword):
    """关键词回退匹配"""
    synonym_map = {
        "医疗费赔偿": "医疗费", "护理费赔偿": "护理费", "交通费赔偿": "交通费",
        "误工费赔偿": "误工费", "闯红灯扣分": "闯红灯", "超速扣分": "超速",
        "违约金支付": "违约金", "工资薪金": "个人所得税", "劳务报酬": "个人所得税",
        "死亡赔偿": "死亡赔偿金", "残疾赔偿": "残疾赔偿金", "精神赔偿": "精神损害抚慰金",
        "经济补偿": "经济补偿金", "加班工资": "加班费"
    }

    if legal_keyword in synonym_map:
        mapped_keyword = synonym_map[legal_keyword]
        if mapped_keyword in LEGAL_KNOWLEDGE_BASE:
            return LEGAL_KNOWLEDGE_BASE[mapped_keyword]["articles"]

    # 默认返回通用侵权法条
    return ["《中华人民共和国民法典》第一千一百七十九条", "《中华人民共和国民法典》第一千一百八十四条"]


# ------------------- 6. 结果生成函数 -------------------
def generate_evaluation_file(test_data):
    """生成最终输出文件"""
    with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as f:
        for data in test_data:
            data_id = data["id"]
            query = data["query"]
            print(f"开始处理ID：{data_id}，问题：{query[:60]}...")

            try:
                # 使用RAG增强调用基线模型
                reasoning, numerical_answer, legal_keyword = call_baseline_model_with_rag(query)

                # 使用RAG增强匹配法条
                article_answer = rag_enhanced_match_articles(legal_keyword, query)

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
                    "article_answer": ["《中华人民共和国民法典》第一千一百七十九条",
                                       "《中华人民共和国民法典》第一千一百八十四条"]
                }
                f.write(json.dumps(error_data, ensure_ascii=False) + '\n')

    print(f"\n所有数据处理结束，结果文件已保存至：{OUTPUT_FILE_PATH}")


# ------------------- 7. 主函数 -------------------
if __name__ == "__main__":
    print(f"===== 开始运行RAG增强的qwen3-235b-a22b-instruct-2507基线模型处理流程 =====")

    # 加载测试数据
    test_data = load_test_data()
    print(f"成功加载 {len(test_data)} 条有效测试数据")
    if not test_data:
        print("无有效测试数据，程序退出")
        exit()

    # 生成结果文件
    generate_evaluation_file(test_data)
    print("===== 流程结束 =====")