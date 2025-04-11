from pymongo import MongoClient, errors
import numpy as np
import random


def aggregate_text_embedding(text_paragraphs):
    # 通过取平均来聚合嵌入
    aggregated_embedding = np.mean(
        [paragraph["embedding"] for paragraph in text_paragraphs], axis=0
    )
    return aggregated_embedding


def aggregate_text_embedding_max_pooling(text_paragraphs):
    """
    使用最大池化（max pooling）来聚合文本段落的嵌入向量。

    参数：
    text_paragraphs (list of dict): 每个字典包含一个键 'embedding'，其值是一个嵌入向量。

    返回：
    numpy.ndarray: 聚合后的嵌入向量。
    """
    # 提取所有嵌入向量
    embeddings = np.array([paragraph["embedding"] for paragraph in text_paragraphs])

    if len(embeddings) >= 5:
        # 计算每个嵌入向量的模长
        norms = np.linalg.norm(embeddings, axis=1)

        # 找到最大和最小模长的索引
        max_norm_index = np.argmax(norms)
        min_norm_index = np.argmin(norms)

        # 去掉最大和最小模长的嵌入向量
        remaining_indices = [
            i
            for i in range(len(embeddings))
            if i not in [max_norm_index, min_norm_index]
        ]

        if len(remaining_indices) < 2:
            raise ValueError(
                "After removing the largest and smallest norms, there are not enough embeddings left for selection."
            )

        # 随机选择两段
        selected_indices = random.sample(remaining_indices, 3)
        selected_embeddings = embeddings[selected_indices]
    else:
        # 如果段落数小于3，直接使用所有嵌入向量进行最大池化
        selected_embeddings = embeddings

    # 对每个维度进行最大池化
    aggregated_embedding = np.max(selected_embeddings, axis=0)

    return aggregated_embedding


def aggregate_case_embedding(case_embeddings):
    # 通过取平均来聚合嵌入
    aggregated_embedding = np.max([case_embeddings[0]], axis=0)
    return aggregated_embedding


class DatabaseHandler:
    def __init__(self, uri: str, db_name: str, collection_name: str):
        """初始化MongoDB连接"""
        try:
            self.client = MongoClient(uri)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
        except errors.ConnectionFailure as e:
            print(f"数据库连接失败: {e}")
            raise


class TextDatabaseHandler:
    def __init__(self, uri: str, db_name: str, collection_name: str):
        """初始化MongoDB连接"""
        try:
            self.client = MongoClient(uri)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
        except errors.ConnectionFailure as e:
            print(f"数据库连接失败: {e}")
            raise

    def get_text_list(self):
        """从MongoDB中获取课文列表"""
        try:
            result = []
            for doc in self.collection.find(
                {},
                {
                    "_id": 0,
                    "title": 1,
                    "author": 1,
                    "grade": 1,
                    "unit": 1,
                    "type": 1,
                    "paragraphs": 1,
                },
            ):
                result.append(
                    {
                        "title": doc.get("title", ""),
                        "author": doc.get("author", ""),
                        "grade": doc.get("grade", ""),
                        "unit": doc.get("unit", ""),
                        "type": doc.get("type", ""),
                        "paragraphs": doc.get("paragraphs", []),
                    }
                )
            return result
        except Exception as e:
            print(f"获取课文列表时出错: {e}")
            raise

    def get_text_title_list(self):
        """从MongoDB中获取课文列表"""
        try:
            result = []
            for doc in self.collection.find({}, {"title": 1, "type": 1}):
                result.append(
                    {
                        "title": doc.get("title", ""),
                        "type": doc.get("type", ""),
                    }
                )
            return result
        except Exception as e:
            print(f"获取课文title列表时出错: {e}")
            raise

    def get_lesson_by_title(self, title: str):
        """根据标题查询课文，返回结构化数据"""
        try:
            doc = self.collection.find_one(
                {"title": title},
                {
                    "_id": 1,
                    "title": 1,
                    "author": 1,
                    "grade": 1,
                    "unit": 1,
                    "type": 1,
                    "paragraphs": 1,
                },
            )
            if doc:
                text_with_embed = doc.get("paragraphs", "")
                return {
                    "title": doc.get("title", ""),
                    "author": doc.get("author", ""),
                    "grade": doc.get("grade", ""),
                    "unit": doc.get("unit", ""),
                    "type": doc.get("type", ""),
                    "text": "".join(
                        [p["paragraph_text"] + "\n" for p in text_with_embed]
                    ),
                    "embedding": list(
                        aggregate_text_embedding_max_pooling(text_with_embed)
                    ),
                }
            else:
                return None
        except Exception as e:
            print(f"根据标题获取课文时出错: {e}")
            raise

    def get_lessons_by_titles(self, titles):
        """根据多个标题查询课文，返回结构化数据"""
        try:
            docs = self.collection.find(
                {"title": {"$in": titles}},
                {
                    "_id": 0,
                    "title": 1,
                    "author": 1,
                    "grade": 1,
                    "unit": 1,
                    "type": 1,
                    "paragraphs": 1,
                },
            )
            result = []
            for doc in docs:
                text_with_embed = doc.get("paragraphs", "")
                result.append(
                    {
                        "title": doc.get("title", ""),
                        "author": doc.get("author", ""),
                        "grade": doc.get("grade", ""),
                        "unit": doc.get("unit", ""),
                        "type": doc.get("type", ""),
                        "text": "".join(
                            [p["paragraph_text"] + "\n" for p in text_with_embed]
                        ),
                        "embedding": list(
                            aggregate_text_embedding_max_pooling(text_with_embed)
                        ),
                    }
                )
            return result
        except Exception as e:
            print(f"根据多个标题获取课文时出错: {e}")
            raise

    def close(self):
        """关闭MongoDB连接"""
        self.client.close()


class CasesDatabaseHandler:
    def __init__(self, uri: str, db_name: str, collection_name: str):
        """初始化MongoDB连接"""
        try:
            self.client = MongoClient(uri)
            self.db = self.client[db_name]
            self.collection = self.db[collection_name]
        except errors.ConnectionFailure as e:
            print(f"数据库连接失败: {e}")
            raise

    def get_cases_by_subjects(self, subjects: list[str]):
        """根据subjects列表查询包含这些subjects的case，并返回goal和process属性"""
        try:
            query = {"subjects": {"$in": subjects}}
            projection = {
                "_id": 0,
                "subjects": 1,
                "background": 1,
                "goal": 1,
                "process": 1,
                "embeddings": 1,
            }
            docs = self.collection.find(query, projection)

            result = []
            for doc in docs:
                result.append(
                    {
                        # "goal": doc.get("goal", ""),
                        "subjects": doc.get("subjects", []),
                        "background": doc.get("background", ""),
                        "process": doc.get("process", ""),
                        "embedding": list(
                            aggregate_case_embedding(doc.get("embeddings", []))
                        ),
                    }
                )

            # return result
            # 综合实践的特殊处理
            final_result = []

            for r in result:
                final_result.append(
                    {
                        "process": r["background"] + ": " + r["process"],
                        "embedding": r["embedding"],
                    }
                )
            return final_result
        except Exception as e:
            print(f"根据subjects获取cases时出错: {e}")
            raise

    def close(self):
        """关闭MongoDB连接"""
        self.client.close()
