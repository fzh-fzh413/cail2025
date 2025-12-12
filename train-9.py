# -*- coding: utf-8 -*-
"""
更新说明：
- 用 TF-IDF / BM25 (若可用) 做 RAG 式检索，从法律文献知识库中检索最相关的法条全文并返回法条标题。
- 支持两种知识库存储方式：legal_docs.jsonl 或 legal_docs/ (每个 txt 文件名为标题)。
- 若检索结果为空或知识库未提供对应文本，回退到 COMPLETE_LEGAL_ARTICLES 的映射（保底）。
"""

import json
import re
import os
from pathlib import Path
from dashscope import Generation

# TF-IDF & BM25
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

# BM25 optional
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except Exception:
    BM25_AVAILABLE = False

# ------------------- 1. 核心配置 -------------------
BASE_MODEL_NAME = "qwen3-235b-a22b-instruct-2507"
DASHSCOPE_API_KEY = "sk-653bf07ab1aa466099d80a3a275afdb4"
TEST_FILE_PATH = r"C:\Users\fzh\Desktop\pythonProject1\stage0_test.jsonl"
OUTPUT_FILE_PATH = "evaluation-9.jsonl"

# 知识库位置（请把你的法律全文/司法解释等放在这里）
LEGAL_DOCS_JSONL = "legal_docs.jsonl"   # 优先
LEGAL_DOCS_DIR = "legal_docs"           # 备用：每个 txt 文件名为标题

# ------------------- 2. 完整的法条知识库（保底映射） -------------------
COMPLETE_LEGAL_ARTICLES = {
    # （与原来相同）...
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
    "个人所得税": [
        "《中华人民共和国个人所得税法》第三条"
    ],
    "增值税": [
        "《中华人民共和国增值税暂行条例》第二条"
    ],
    "违约金": [
        "《中华人民共和国民法典》第五百八十五条"
    ],
    "定金": [
        "《中华人民共和国民法典》第五百八十六条"
    ],
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

# ------------------- 3. Prompt 模板（保持不变或按需微调） -------------------
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
"""

# ------------------- 4. 知识库加载与检索构建 -------------------

class LegalKnowledgeBase:
    def __init__(self, jsonl_path=LEGAL_DOCS_JSONL, dir_path=LEGAL_DOCS_DIR):
        self.docs = []           # list of dicts: {"title":..., "text":..., "source":...}
        self.titles = []
        self.texts = []
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.bm25 = None
        # 尝试加载 jsonl 优先
        if os.path.exists(jsonl_path):
            self._load_from_jsonl(jsonl_path)
        elif os.path.isdir(dir_path):
            self._load_from_dir(dir_path)
        else:
            print("未找到法律文献知识库（legal_docs.jsonl 或 legal_docs/），将回退到内置映射。")
        # 构建检索索引（若有文本且 sklearn 可用）
        if SKLEARN_AVAILABLE and self.texts:
            self._build_tfidf_index()
        if BM25_AVAILABLE and self.texts:
            self._build_bm25_index()

    def _load_from_jsonl(self, path):
        print(f"加载法律知识库（jsonl）：{path}")
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    jd = json.loads(line)
                    title = jd.get("title") or jd.get("id") or "unknown"
                    text = jd.get("text") or ""
                    source = jd.get("source", "")
                    if text.strip():
                        self.docs.append({"title": title, "text": text, "source": source})
                except Exception:
                    continue
        self._sync_lists()

    def _load_from_dir(self, dirpath):
        print(f"加载法律知识库（目录）：{dirpath}")
        p = Path(dirpath)
        for f in p.glob("*.txt"):
            title = f.stem
            text = f.read_text(encoding='utf-8')
            if text.strip():
                self.docs.append({"title": title, "text": text, "source": str(f)})
        self._sync_lists()

    def _sync_lists(self):
        self.titles = [d["title"] for d in self.docs]
        self.texts = [d["text"] for d in self.docs]

    def _build_tfidf_index(self):
        self.tfidf_vectorizer = TfidfVectorizer(ngram_range=(1,2), max_features=20000)
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.texts)
        print("已构建 TF-IDF 索引。")

    def _build_bm25_index(self):
        # BM25 使用分词 (简单空格分词，如果需要可替换为更复杂的中文分词)
        tokenized = [doc.split() for doc in self.texts]
        self.bm25 = BM25Okapi(tokenized)
        print("已构建 BM25 索引。")

    def retrieve(self, query: str, top_k: int = 3):
        """
        返回 top_k 最相关文档的标题列表（如果没有索引则返回空列表）
        优先使用 BM25（若可用且 query 分词后长度合适），否则 TF-IDF。
        """
        if not self.texts:
            return []

        candidates = []
        # try BM25
        if BM25_AVAILABLE and self.bm25:
            q_tokens = query.split()
            if len(q_tokens) > 0:
                scores = self.bm25.get_scores(q_tokens)
                idxs = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
                candidates = [(self.titles[i], float(scores[i])) for i in idxs if scores[i] > 0]
                if candidates:
                    return [t for t, s in candidates]

        # fallback to TF-IDF cosine similarity
        if SKLEARN_AVAILABLE and self.tfidf_vectorizer and self.tfidf_matrix is not None:
            q_vec = self.tfidf_vectorizer.transform([query])
            # cosine similarity
            import numpy as np
            sims = (self.tfidf_matrix @ q_vec.T).toarray().ravel()
            idxs = sims.argsort()[::-1][:top_k]
            candidates = [(self.titles[i], float(sims[i])) for i in idxs if sims[i] > 0]
            if candidates:
                return [t for t, s in candidates]

        return []

# 初始化一次知识库（全程序可复用）
LEGAL_KB = LegalKnowledgeBase()

# ------------------- 5. 调用模型与解析函数（沿用原有） -------------------
def call_baseline_model(query):
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
    reasoning_match = re.search(r'reasoning_content：(.*?)(?=numerical_answer：|legal_keyword：|$)', model_output, re.DOTALL)
    reasoning = reasoning_match.group(1).strip() if reasoning_match else "未解析出思考过程"
    num_match = re.search(r'numerical_answer：(\[.*?\])', model_output)
    numerical_answer = [0.00]
    if num_match:
        try:
            num_list = json.loads(num_match.group(1))
            if isinstance(num_list, list) and len(num_list) > 0:
                numerical_answer = [round(float(num_list[0]) + 0.0, 2)]
        except Exception:
            numerical_answer = [0.00]
    keyword_match = re.search(r'legal_keyword：(.*)', model_output, re.DOTALL)
    legal_keyword = keyword_match.group(1).strip() if keyword_match else "未提取到关键词"
    return reasoning, numerical_answer, legal_keyword

# ------------------- 6. 用 RAG 替代原有 smart_match_legal_articles -------------------
def rag_match_legal_articles(legal_keyword, reasoning_content, top_k=3):
    """
    使用 RAG（检索）返回法条标题列表：
    - 优先用 legal_keyword + reasoning_content 作为检索 query
    - 如果检索到文档就返回这些文档的标题（代表法条/解释）
    - 否则回退到 COMPLETE_LEGAL_ARTICLES 的映射策略（原有保底）
    """
    # 准备检索 query：关键词+推理内容（取前256字符）
    query_parts = []
    if legal_keyword and legal_keyword != "未提取到关键词":
        query_parts.append(legal_keyword)
    if reasoning_content:
        query_parts.append(reasoning_content[:512])
    query = " ".join(query_parts).strip()
    if not query:
        # 彻底没有可检索信息
        return fallback_mapping(legal_keyword)

    # run retrieval
    hits = LEGAL_KB.retrieve(query, top_k=top_k)
    if hits:
        # hits 是标题列表，返回这些标题（如果需要返回具体条文，可把匹配标题映射回实际条文）
        print(f"RAG检索命中（{len(hits)}）：{hits}")
        # 如果 titles 本身是条文标题（例如 "《民法典》第一千一百七十九条"），直接返回
        # 否则尝试基于标题在 COMPLETE_LEGAL_ARTICLES 找到映射的条目
        matched_articles = []
        for t in hits:
            # 若标题本身就是标准法条字符串，则直接使用；否则尝试映射回 COMPLETE_LEGAL_ARTICLES
            if "第" in t and "条" in t and "《" in t:
                matched_articles.append(t)
            else:
                # 尝试在 COMPLETE_LEGAL_ARTICLES 中按包含匹配
                found = False
                for key, vals in COMPLETE_LEGAL_ARTICLES.items():
                    for v in vals:
                        if t in v or key in t:
                            matched_articles.extend(vals)
                            found = True
                            break
                    if found:
                        break
                if not found:
                    # 把标题原样加入（至少给出检索到的文献标题）
                    matched_articles.append(t)
        # 去重并返回
        seen = []
        for a in matched_articles:
            if a not in seen:
                seen.append(a)
        return seen

    # 没检索到则回退
    print("RAG未命中，回退到映射策略。")
    return fallback_mapping(legal_keyword)

def fallback_mapping(legal_keyword):
    """原先的同义词/规则映射（保底）"""
    if not legal_keyword or legal_keyword == "未提取到关键词":
        # 若完全没有关键词，则分析推理内容或直接返回通用侵权
        return COMPLETE_LEGAL_ARTICLES.get("通用侵权")
    # 精确匹配
    if legal_keyword in COMPLETE_LEGAL_ARTICLES:
        return COMPLETE_LEGAL_ARTICLES[legal_keyword]
    # 同义词表（沿用你原来的映射）
    synonym_map = {
        "医疗费赔偿": "医疗费", "护理费赔偿": "护理费", "交通费赔偿": "交通费",
        "误工费赔偿": "误工费", "闯红灯扣分": "闯红灯", "超速扣分": "超速",
        "违约金支付": "违约金", "工资薪金": "个人所得税", "劳务报酬": "个人所得税",
        "死亡赔偿": "死亡赔偿金", "残疾赔偿": "残疾赔偿金", "精神赔偿": "精神损害抚慰金",
        "经济补偿": "经济补偿金", "加班工资": "加班费", "双倍工资赔偿": "双倍工资",
    }
    if legal_keyword in synonym_map:
        mk = synonym_map[legal_keyword]
        if mk in COMPLETE_LEGAL_ARTICLES:
            return COMPLETE_LEGAL_ARTICLES[mk]
    # 包含匹配
    for legal_type in COMPLETE_LEGAL_ARTICLES:
        if legal_keyword in legal_type or legal_type in legal_keyword:
            return COMPLETE_LEGAL_ARTICLES[legal_type]
    # 通用兜底
    return COMPLETE_LEGAL_ARTICLES.get("通用侵权")

# ------------------- 7. 生成结果与主流程（保留原有） -------------------
def load_test_data():
    test_data = []
    with open(TEST_FILE_PATH, 'r', encoding='utf-8') as f:
        for line in f:
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

def generate_evaluation_file(test_data):
    with open(OUTPUT_FILE_PATH, 'w', encoding='utf-8') as f:
        for data in test_data:
            data_id = data["id"]
            query = data["query"]
            print(f"开始处理ID：{data_id} ...")
            try:
                reasoning, numerical_answer, legal_keyword = call_baseline_model(query)
                # 这里可以把检索到的 top_k 法条文本（或标题）拼回给模型做第二次生成精校（RAG end-to-end）
                # examples:
                # retrieved_titles = rag_match_legal_articles(legal_keyword, reasoning, top_k=3)
                # second_prompt = PROMPT_TEMPLATE + "\n\n参考法条:\n" + "\n".join(retrieved_titles) + "\n\n问题内容：" + query
                # .... call model again if你想要基于检索到的法条让模型重新生成reasoning_content/ article_answer
                article_answer = rag_match_legal_articles(legal_keyword, reasoning, top_k=3)
                output_data = {
                    "id": data_id,
                    "reasoning_content": reasoning,
                    "numerical_answer": numerical_answer,
                    "article_answer": article_answer
                }
                f.write(json.dumps(output_data, ensure_ascii=False) + '\n')
                print(f"ID：{data_id} 完成，法条数：{len(article_answer)}")
            except Exception as e:
                print(f"ID：{data_id} 处理失败：{e}")
                error_data = {
                    "id": data_id,
                    "reasoning_content": f"处理异常：{str(e)}",
                    "numerical_answer": [0.00],
                    "article_answer": COMPLETE_LEGAL_ARTICLES["通用侵权"]
                }
                f.write(json.dumps(error_data, ensure_ascii=False) + '\n')
    print(f"全部处理完毕，输出文件：{OUTPUT_FILE_PATH}")

if __name__ == "__main__":
    print("===== 启动：RAG + 基线模型工作流 =====")
    test_data = load_test_data()
    print(f"加载到 {len(test_data)} 条测试数据")
    if not test_data:
        print("无有效测试数据，退出。")
        exit()
    generate_evaluation_file(test_data)
