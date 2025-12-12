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
OUTPUT_FILE_PATH = "evaluation.jsonl"

# ------------------- 2. 完整的法律知识库（多部法律） -------------------
COMPLETE_LEGAL_KNOWLEDGE_BASE = [
    # 民法典（侵权责任、合同等）
    {
        "law_name": "中华人民共和国民法典",
        "article_number": "第一千一百七十九条",
        "content": "侵害他人造成人身损害的，应当赔偿医疗费、护理费、交通费、营养费、住院伙食补助费等为治疗和康复支出的合理费用，以及因误工减少的收入。造成残疾的，还应当赔偿辅助器具费和残疾赔偿金；造成死亡的，还应当赔偿丧葬费和死亡赔偿金。",
        "category": "侵权赔偿"
    },
    {
        "law_name": "中华人民共和国民法典",
        "article_number": "第一千一百八十三条",
        "content": "侵害自然人人身权益造成严重精神损害的，被侵权人有权请求精神损害赔偿。",
        "category": "侵权赔偿"
    },
    {
        "law_name": "中华人民共和国民法典",
        "article_number": "第五百八十五条",
        "content": "当事人可以约定一方违约时应当根据违约情况向对方支付一定数额的违约金，也可以约定因违约产生的损失赔偿额的计算方法。",
        "category": "合同纠纷"
    },
    {
        "law_name": "中华人民共和国民法典",
        "article_number": "第五百八十六条",
        "content": "当事人可以约定一方向对方给付定金作为债权的担保。定金合同自实际交付定金时成立。",
        "category": "合同纠纷"
    },
    {
        "law_name": "中华人民共和国民法典",
        "article_number": "第六百八十条",
        "content": "禁止高利放贷，借款的利率不得违反国家有关规定。借款合同对支付利息没有约定的，视为没有利息。",
        "category": "借款合同"
    },
    {
        "law_name": "中华人民共和国民法典",
        "article_number": "第七百零三条",
        "content": "租赁合同是出租人将租赁物交付承租人使用、收益，承租人支付租金的合同。",
        "category": "租赁合同"
    },

    # 道路交通安全法
    {
        "law_name": "中华人民共和国道路交通安全法",
        "article_number": "第九十条",
        "content": "机动车驾驶人违反道路交通安全法律、法规关于道路通行规定的，处警告或者二十元以上二百元以下罚款。",
        "category": "交通违章"
    },
    {
        "law_name": "中华人民共和国道路交通安全法",
        "article_number": "第九十一条",
        "content": "饮酒后驾驶机动车的，处暂扣六个月机动车驾驶证，并处一千元以上二千元以下罚款。",
        "category": "酒驾处罚"
    },
    {
        "law_name": "中华人民共和国道路交通安全法",
        "article_number": "第九十九条",
        "content": "机动车行驶超过规定时速百分之五十的，由公安机关交通管理部门处二百元以上二千元以下罚款。",
        "category": "超速处罚"
    },

    # 个人所得税法
    {
        "law_name": "中华人民共和国个人所得税法",
        "article_number": "第三条",
        "content": "个人所得税的税率：（一）综合所得，适用百分之三至百分之四十五的超额累进税率；（二）经营所得，适用百分之五至百分之三十五的超额累进税率；（三）利息、股息、红利所得，财产租赁所得，财产转让所得和偶然所得，适用比例税率，税率为百分之二十。",
        "category": "个人所得税"
    },
    {
        "law_name": "中华人民共和国个人所得税法",
        "article_number": "第六条",
        "content": "居民个人的综合所得，以每一纳税年度的收入额减除费用六万元以及专项扣除、专项附加扣除和依法确定的其他扣除后的余额，为应纳税所得额。",
        "category": "个人所得税"
    },

    # 劳动合同法
    {
        "law_name": "中华人民共和国劳动合同法",
        "article_number": "第四十六条",
        "content": "有下列情形之一的，用人单位应当向劳动者支付经济补偿：（一）劳动者依照本法第三十八条规定解除劳动合同的；（二）用人单位依照本法第三十六条规定向劳动者提出解除劳动合同并与劳动者协商一致解除劳动合同的；（三）用人单位依照本法第四十条规定解除劳动合同的。",
        "category": "劳动补偿"
    },
    {
        "law_name": "中华人民共和国劳动合同法",
        "article_number": "第四十七条",
        "content": "经济补偿按劳动者在本单位工作的年限，每满一年支付一个月工资的标准向劳动者支付。六个月以上不满一年的，按一年计算；不满六个月的，向劳动者支付半个月工资的经济补偿。",
        "category": "劳动补偿"
    },
    {
        "law_name": "中华人民共和国劳动合同法",
        "article_number": "第八十二条",
        "content": "用人单位自用工之日起超过一个月不满一年未与劳动者订立书面劳动合同的，应当向劳动者每月支付二倍的工资。",
        "category": "双倍工资"
    },

    # 劳动法
    {
        "law_name": "中华人民共和国劳动法",
        "article_number": "第四十四条",
        "content": "有下列情形之一的，用人单位应当按照下列标准支付高于劳动者正常工作时间工资的工资报酬：（一）安排劳动者延长工作时间的，支付不低于工资的百分之一百五十的工资报酬；（二）休息日安排劳动者工作又不能安排补休的，支付不低于工资的百分之二百的工资报酬；（三）法定休假日安排劳动者工作的，支付不低于工资的百分之三百的工资报酬。",
        "category": "加班工资"
    },

    # 消费者权益保护法
    {
        "law_name": "中华人民共和国消费者权益保护法",
        "article_number": "第五十五条",
        "content": "经营者提供商品或者服务有欺诈行为的，应当按照消费者的要求增加赔偿其受到的损失，增加赔偿的金额为消费者购买商品的价款或者接受服务的费用的三倍；增加赔偿的金额不足五百元的，为五百元。",
        "category": "消费赔偿"
    },

    # 产品质量法
    {
        "law_name": "中华人民共和国产品质量法",
        "article_number": "第四十条",
        "content": "售出的产品有下列情形之一的，销售者应当负责修理、更换、退货；给购买产品的消费者造成损失的，销售者应当赔偿损失：（一）不具备产品应当具备的使用性能而事先未作说明的；（二）不符合在产品或者其包装上注明采用的产品标准的；（三）不符合以产品说明、实物样品等方式表明的质量状况的。",
        "category": "产品质量"
    },

    # 保险法
    {
        "law_name": "中华人民共和国保险法",
        "article_number": "第二条",
        "content": "本法所称保险，是指投保人根据合同约定，向保险人支付保险费，保险人对于合同约定的可能发生的事故因其发生所造成的财产损失承担赔偿保险金责任，或者当被保险人死亡、伤残、疾病或者达到合同约定的年龄、期限等条件时承担给付保险金责任的商业保险行为。",
        "category": "保险理赔"
    },

    # 刑法（涉及罚金）
    {
        "law_name": "中华人民共和国刑法",
        "article_number": "第五十二条",
        "content": "判处罚金，应当根据犯罪情节决定罚金数额。",
        "category": "刑事罚金"
    },

    # 行政处罚法
    {
        "law_name": "中华人民共和国行政处罚法",
        "article_number": "第九条",
        "content": "行政处罚的种类：（一）警告、通报批评；（二）罚款、没收违法所得、没收非法财物；（三）暂扣许可证件、降低资质等级、吊销许可证件；（四）限制开展生产经营活动、责令停产停业、责令关闭、限制从业；（五）行政拘留；（六）法律、行政法规规定的其他行政处罚。",
        "category": "行政处罚"
    },

    # 增值税法
    {
        "law_name": "中华人民共和国增值税暂行条例",
        "article_number": "第二条",
        "content": "增值税税率：（一）纳税人销售货物、劳务、有形动产租赁服务或者进口货物，税率为13%；（二）纳税人销售交通运输、邮政、基础电信、建筑、不动产租赁服务，销售不动产，转让土地使用权，税率为9%；（三）纳税人销售服务、无形资产，税率为6%。",
        "category": "增值税"
    },

    # 企业所得税法
    {
        "law_name": "中华人民共和国企业所得税法",
        "article_number": "第四条",
        "content": "企业所得税的税率为25%。非居民企业取得本法第三条第三款规定的所得，适用税率为20%。",
        "category": "企业所得税"
    },

    # 城市房地产管理法
    {
        "law_name": "中华人民共和国城市房地产管理法",
        "article_number": "第三十二条",
        "content": "房地产转让、抵押时，房屋的所有权和该房屋占用范围内的土地使用权同时转让、抵押。",
        "category": "房地产"
    },

    # 最高人民法院司法解释
    {
        "law_name": "最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释",
        "article_number": "第七条",
        "content": "误工费根据受害人的误工时间和收入状况确定。受害人有固定收入的，误工费按照实际减少的收入计算。受害人无固定收入的，按照其最近三年的平均收入计算；受害人不能举证证明其最近三年的平均收入状况的，可以参照受诉法院所在地相同或者相近行业上一年度职工的平均工资计算。",
        "category": "人身损害赔偿"
    },
    {
        "law_name": "最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释",
        "article_number": "第八条",
        "content": "护理费根据护理人员的收入状况和护理人数、护理期限确定。护理人员有收入的，参照误工费的规定计算；护理人员没有收入或者雇佣护工的，参照当地护工从事同等级别护理的劳务报酬标准计算。",
        "category": "人身损害赔偿"
    },
    {
        "law_name": "最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释",
        "article_number": "第九条",
        "content": "交通费根据受害人及其必要的陪护人员因就医或者转院治疗实际发生的费用计算。",
        "category": "人身损害赔偿"
    },
    {
        "law_name": "最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释",
        "article_number": "第十条",
        "content": "住院伙食补助费可以参照当地国家机关一般工作人员的出差伙食补助标准予以确定。",
        "category": "人身损害赔偿"
    },
    {
        "law_name": "最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释",
        "article_number": "第十一条",
        "content": "营养费根据受害人伤残情况参照医疗机构的意见确定。",
        "category": "人身损害赔偿"
    },
    {
        "law_name": "最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释",
        "article_number": "第十二条",
        "content": "残疾赔偿金根据受害人丧失劳动能力程度或者伤残等级，按照受诉法院所在地上一年度城镇居民人均可支配收入或者农村居民人均纯收入标准，自定残之日起按二十年计算。",
        "category": "人身损害赔偿"
    },

    # 道路交通安全违法行为记分管理办法
    {
        "law_name": "道路交通安全违法行为记分管理办法",
        "article_number": "第八条",
        "content": "驾驶机动车违反道路交通信号灯通行的，一次记6分。",
        "category": "交通违章记分"
    },
    {
        "law_name": "道路交通安全违法行为记分管理办法",
        "article_number": "第九条",
        "content": "驾驶校车、中型以上载客载货汽车、危险物品运输车辆在高速公路、城市快速路以外的道路上行驶超过规定时速百分之五十以上的，一次记9分；超过规定时速百分之二十以上未达到百分之五十的，一次记6分。",
        "category": "交通违章记分"
    }
]


# ------------------- 3. RAG检索器 -------------------
class MultiLawRAGRetriever:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words=None)
        self.document_vectors = None
        self.documents_text = []
        self.build_index()

    def build_index(self):
        """构建多法律知识索引"""
        print("正在构建多法律知识索引...")

        # 为每个法条创建检索文本
        for law in COMPLETE_LEGAL_KNOWLEDGE_BASE:
            # 组合法条名称、编号、内容和类别作为检索文本
            doc_text = f"{law['law_name']} {law['article_number']} {law['content']} {law['category']}"
            self.documents_text.append(doc_text)

        # 训练TF-IDF向量化器
        if self.documents_text:
            self.document_vectors = self.vectorizer.fit_transform(self.documents_text)
            print(f"多法律知识索引构建完成，共{len(self.documents_text)}个法条")
            print(
                f"涵盖法律包括：民法典、道路交通安全法、个人所得税法、劳动合同法、劳动法、消费者权益保护法、产品质量法、保险法、刑法、行政处罚法、增值税暂行条例、企业所得税法、城市房地产管理法及相关司法解释")
        else:
            print("多法律知识索引构建失败")

    def search_similar_laws(self, query, top_k=3, similarity_threshold=0.1):
        """搜索与查询相似的法条"""
        if self.document_vectors is None:
            return []

        try:
            # 将查询转换为向量
            query_vector = self.vectorizer.transform([query])

            # 计算相似度
            similarities = cosine_similarity(query_vector, self.document_vectors)[0]

            # 获取相似度最高的结果
            results = []
            for i, similarity in enumerate(similarities):
                if similarity >= similarity_threshold:
                    law_info = COMPLETE_LEGAL_KNOWLEDGE_BASE[i].copy()
                    law_info["similarity"] = float(similarity)
                    results.append(law_info)

            # 按相似度排序
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]

        except Exception as e:
            print(f"语义搜索失败: {e}")
            return []


# 初始化RAG检索器
rag_retriever = MultiLawRAGRetriever()

# ------------------- 4. Prompt模板 -------------------
PROMPT_TEMPLATE = """
你需要处理法律数值计算问题，严格按照以下3个步骤输出结果：

步骤1：输出思考过程（key: reasoning_content）
- 先明确问题类型（从"补偿类型/费用类型/罚金类型/税费税率类型/交通违章行为扣分类型"中选择1个）；
- 提取问题中的关键数值（如"年平均工资80000元""误工5天"）；
- 说明具体计算逻辑（如"年工资÷365天×误工天数"）。

步骤2：输出数值结果（key: numerical_answer）
- 仅保留计算结果，保留2位小数（整数需补两位小数，如6→6.00）；
- 用列表包裹，格式示例：[1095.89]。

步骤3：输出法条关键词（key: legal_keyword）
- 提取1-2个能代表问题核心的关键词（用于匹配法条，如"误工费""闯红灯""个人所得税 综合所得"）；
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


def multi_law_semantic_match(query, legal_keyword, reasoning_content):
    """使用多法律进行语义匹配"""
    # 组合查询、关键词和推理内容进行搜索
    search_query = f"{query} {legal_keyword} {reasoning_content}"
    similar_laws = rag_retriever.search_similar_laws(search_query, top_k=2)

    if similar_laws:
        # 返回匹配的法条引用
        articles = []
        for law in similar_laws:
            article_ref = f"{law['law_name']} {law['article_number']}"
            articles.append(article_ref)
            print(f"多法律语义匹配: {legal_keyword} -> {article_ref} (相似度: {law['similarity']:.3f})")

        return articles
    else:
        # 基于推理内容的智能匹配
        return intelligent_multi_law_match(reasoning_content, legal_keyword)


def intelligent_multi_law_match(reasoning_content, legal_keyword):
    """基于推理内容的多法律智能匹配"""
    reasoning_lower = reasoning_content.lower()

    # 人身损害赔偿相关
    if any(word in reasoning_lower for word in ["误工费", "工资", "收入", "误工"]):
        return ["《中华人民共和国民法典》第一千一百七十九条",
                "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第七条"]
    elif any(word in reasoning_lower for word in ["医疗费", "医药费", "治疗费"]):
        return ["《中华人民共和国民法典》第一千一百七十九条",
                "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第六条"]
    elif any(word in reasoning_lower for word in ["护理费", "护理人员"]):
        return ["《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第八条",
                "《中华人民共和国民法典》第一千一百七十九条"]
    elif any(word in reasoning_lower for word in ["交通费", "车费"]):
        return ["《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第九条",
                "《中华人民共和国民法典》第一千一百七十九条"]
    elif any(word in reasoning_lower for word in ["精神损害", "精神赔偿"]):
        return ["《中华人民共和国民法典》第一千一百八十三条",
                "《最高人民法院关于确定民事侵权精神损害赔偿责任若干问题的解释》第五条"]
    elif any(word in reasoning_lower for word in ["残疾赔偿金", "伤残"]):
        return ["《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第十二条",
                "《中华人民共和国民法典》第一千一百七十九条"]

    # 交通违章相关
    elif any(word in reasoning_lower for word in ["闯红灯", "交通信号"]):
        return ["《道路交通安全违法行为记分管理办法》第八条", "《中华人民共和国道路交通安全法》第九十条"]
    elif any(word in reasoning_lower for word in ["超速", "超速行驶"]):
        return ["《中华人民共和国道路交通安全法》第九十九条", "《道路交通安全违法行为记分管理办法》第九条"]
    elif any(word in reasoning_lower for word in ["酒驾", "饮酒驾驶"]):
        return ["《中华人民共和国道路交通安全法》第九十一条", "《道路交通安全违法行为记分管理办法》第八条"]

    # 税收相关
    elif any(word in reasoning_lower for word in ["个人所得税", "个税", "税率"]):
        return ["《中华人民共和国个人所得税法》第三条", "《中华人民共和国个人所得税法》第六条"]
    elif any(word in reasoning_lower for word in ["增值税", "增值税率"]):
        return ["《中华人民共和国增值税暂行条例》第二条", "《中华人民共和国税收征收管理法》相关条款"]
    elif any(word in reasoning_lower for word in ["企业所得税"]):
        return ["《中华人民共和国企业所得税法》第四条", "《中华人民共和国税收征收管理法》相关条款"]

    # 劳动相关
    elif any(word in reasoning_lower for word in ["经济补偿金", "工作年限", "离职补偿"]):
        return ["《中华人民共和国劳动合同法》第四十七条", "《中华人民共和国劳动合同法》第四十六条"]
    elif any(word in reasoning_lower for word in ["加班费", "加班工资"]):
        return ["《中华人民共和国劳动法》第四十四条", "《中华人民共和国劳动合同法》相关条款"]
    elif any(word in reasoning_lower for word in ["双倍工资", "未签合同"]):
        return ["《中华人民共和国劳动合同法》第八十二条", "《中华人民共和国劳动法》相关条款"]

    # 合同相关
    elif any(word in reasoning_lower for word in ["违约金", "违约"]):
        return ["《中华人民共和国民法典》第五百八十五条", "《中华人民共和国民法典》第五百七十七条"]
    elif any(word in reasoning_lower for word in ["定金", "订金"]):
        return ["《中华人民共和国民法典》第五百八十六条", "《中华人民共和国民法典》第五百八十五条"]

    # 消费相关
    elif any(word in reasoning_lower for word in ["消费者", "欺诈", "三倍赔偿"]):
        return ["《中华人民共和国消费者权益保护法》第五十五条", "《中华人民共和国产品质量法》第四十条"]

    # 默认返回侵权责任基础法条
    else:
        return ["《中华人民共和国民法典》第一千一百七十九条",
                "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第七条"]


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

                # 使用多法律语义匹配法条
                article_answer = multi_law_semantic_match(query, legal_keyword, reasoning)

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
                    "article_answer": ["《中华人民共和国民法典》第一千一百七十九条",
                                       "《最高人民法院关于审理人身损害赔偿案件适用法律若干问题的解释》第七条"]
                }
                f.write(json.dumps(error_data, ensure_ascii=False) + '\n')

    print(f"\n所有数据处理结束，结果文件已保存至：{OUTPUT_FILE_PATH}")


# ------------------- 7. 主函数 -------------------
if __name__ == "__main__":
    print(f"===== 开始运行多法律RAG语义匹配的qwen3-235b-a22b-instruct-2507基线模型处理流程 =====")

    # 加载测试数据
    test_data = load_test_data()
    print(f"成功加载 {len(test_data)} 条有效测试数据")
    if not test_data:
        print("无有效测试数据，程序退出")
        exit()

    # 生成结果文件
    generate_evaluation_file(test_data)
    print("===== 流程结束 =====")