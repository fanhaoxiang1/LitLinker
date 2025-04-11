from pymongo import MongoClient
import urllib.parse
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import time

DATABASE = ""
USR_NAME= ""
PSW = ""

username = urllib.parse.quote_plus(USR_NAME)
password = urllib.parse.quote_plus(PSW)
db_uri = f"mongodb://{username}:{password}@" + DATABASE
client = MongoClient(db_uri)
db = client["education"]
cases_collection = db["cases"]
texts_collection = db["lesson_text"]

# 加载案例和文本
cases = list(cases_collection.find())
texts = list(texts_collection.find())
text = []
# 这里就是模仿一下选择哪些课文
for i in texts:
    if i["title"] == "我的伯父鲁迅先生":
        text.append(i)
    if i["title"] == "狼牙山五壮士":
        text.append(i)
    if i["title"] == "七律·长征":
        text.append(i)
    if i["title"] == "开国大典":
        text.append(i)
    if i["title"] == "让生活更美好":
        text.append(i)


def aggregate_text_embedding(text_paragraphs):
    # 通过取平均来聚合嵌入
    aggregated_embedding = np.mean([paragraph['embedding'] for paragraph in text_paragraphs], axis=0)
    return aggregated_embedding


def find_most_relevant_cases(texts, cases, top_n=5):
    case_scores = {}

    for text in texts:
        # 将文本的段落聚合成一个单一的嵌入
        aggregated_text_embedding = aggregate_text_embedding(text['paragraphs'])

        for case in cases:
            case_chunks = case['embeddings']

            # 将聚合的文本嵌入与案例中的所有块进行比较
            similarities = cosine_similarity([aggregated_text_embedding], case_chunks).flatten()
            max_similarity = np.max(similarities)

            case_id = case['_id']
            # 累积案例的最佳相似度分数
            if case_id not in case_scores:
                case_scores[case_id] = {
                    'max_similarity': max_similarity,
                    'case': case
                }
            else:
                if max_similarity > case_scores[case_id]['max_similarity']:
                    case_scores[case_id]['max_similarity'] = max_similarity

    # 按最大相似度分数对案例进行排序
    sorted_cases = sorted(case_scores.values(), key=lambda x: x['max_similarity'], reverse=True)
    top_cases = sorted_cases[:top_n]
    return top_cases

# 为给定文本找到前 n 个最相关的案例
stime = time.time()
top_cases = find_most_relevant_cases(text, cases, top_n=10)
etime = time.time()
print(etime - stime)

# 输出最相关的案例
for i, case_info in enumerate(top_cases):
    case = case_info['case']
    print(f"案例 {i + 1}:")
    print(f"背景: {case['background']}")
    print(f"最大相似度: {case_info['max_similarity']}")
    print(f"过程: {case['process']}")
    print("-" * 100)