from typing import List
import uuid
from datetime import datetime
from pymongo import MongoClient, DESCENDING
import urllib.parse
from models.DatabaseHandler import DatabaseHandler
from pymongo import ASCENDING

GLOBAL = 'global'

DATABASE = ""
USR_NAME= ""
PSW = ""

class History:
    def __init__(self, session_id: str, agent_name: str, prompt: str, response: str, is_user_edited: bool):
        ######## id的算法需要你补充，和session_id一样，为yyyymmddhhmmss，自动生成 ########
        self.id = datetime.now().strftime("%Y%m%d%H%M%S")
        self.session_id = session_id
        self.agent_name = agent_name
        self.prompt = prompt
        self.response = response
        self.is_user_edited = is_user_edited


class Memory:
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.histories = []  # This will store History objects

    def getHistory(self, num: int) -> List[History]:
        ########## 请在此补充代码 ###############
        # 获取最后num条self.session_id，self.agent_name的消息记录
        # 这里假设self.histories已经按时间顺序存储
        username = urllib.parse.quote_plus(USR_NAME)
        password = urllib.parse.quote_plus(PSW)
        db_uri = f"mongodb://{username}:{password}@" + DATABASE
        db_name = "education"
        collection_name = "history"

        db_handler = DatabaseHandler(
            uri=db_uri,
            db_name=db_name,
            collection_name=collection_name
        )
        query = {"agent_name": self.agent_name}

        # 从数据库中获取消息记录，按照时间降序排序，限制为 num 条
        results = db_handler.collection.find(query).sort("id",DESCENDING).limit(num)

        # 将结果转换为 History 对象，去掉 `_id` 字段和'id' 字段
        for doc in results:
            doc.pop('_id', None)  # 去掉 _id 字段
            doc.pop('id', None)  # 去掉 id 字段
            self.histories.append(History(**doc))

        return self.histories[::-1]  # 反向排序列表，确保按时间升序返回


# 全局方法
def save(history: History):
    """
    将一个History对象写到数据库中
    """

    username = urllib.parse.quote_plus(USR_NAME)
    password = urllib.parse.quote_plus(PSW)
    db_uri = f"mongodb://{username}:{password}@" + DATABASE
    db_name = "education"
    collection_name = "history"

    db_handler = DatabaseHandler(
        uri=db_uri,
        db_name=db_name,
        collection_name=collection_name
    )

    try:
        db_handler.collection.insert_one(history.__dict__)
    except Exception as e:
        print(f"保存历史记录时出错: {e}")
    finally:
        db_handler.close()


def getGlobalHistory() -> List[History]:
    """
    获得agent_name == GLOBAL的History
    """

    username = urllib.parse.quote_plus(USR_NAME)
    password = urllib.parse.quote_plus(PSW)
    db_uri = f"mongodb://{username}:{password}@" + DATABASE
    db_name = "education"
    collection_name = "history"

    db_handler = DatabaseHandler(
        uri=db_uri,
        db_name=db_name,
        collection_name=collection_name
    )
    try:
        global_histories = db_handler.collection.find({"agent_name": GLOBAL})
        return [History(**history) for history in global_histories]
    except Exception as e:
        print(f"获取全局历史记录时出错: {e}")
        return []
    finally:
        db_handler.close()
