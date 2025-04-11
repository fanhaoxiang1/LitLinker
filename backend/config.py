from typing import List, Dict
from pymongo import MongoClient
import urllib.parse
from models.DatabaseHandler import DatabaseHandler

DATABASE = ""
USR_NAME= ""
PSW = ""

class Case:
    def __init__(self, background: str, subjects: List[str], context: str, goal: str, process: str):
        self.background = background
        self.subjects = subjects
        self.context = context
        self.goal = goal
        self.process = process

class LessonText:
    def __init__(self, title: str, author: str, grade: str, unit: str, type: str, paragraphs: List[Dict[str, str]]):
        self.title = title
        self.author = author
        self.grade = grade
        self.unit = unit
        self.type = type
        self.paragraphs = paragraphs

class SessionConfig:
    def __init__(self, session_id: str):
        self.session_id = session_id

        username = urllib.parse.quote_plus(USR_NAME)
        password = urllib.parse.quote_plus(PSW)
        db_uri = f"mongodb://{username}:{password}@" + DATABASE
        db_name = "education"
        collection_name = "session_config"
        self.db_handler = DatabaseHandler(
            uri=db_uri,
            db_name=db_name,
            collection_name=collection_name
        )

        self.collections = {
            "selected_cases": [],
            "selected_text": []
        }
        self.selected_case_with_analysis = None
        self._load_from_db()

    def _load_from_db(self):
        # 从数据库加载 session_config
        session_data = self.db_handler.collection.find_one({"session_id": self.session_id})
        if session_data:
            self.collections = session_data.get("collections", self.collections)
            self.selected_case_with_analysis = session_data.get("selected_case_with_analysis", None)

    def _save_to_db(self):
        # 将 session_config 保存到数据库
        session_data = {
            "session_id": self.session_id,
            "collections": self.collections,
            "selected_case_with_analysis": self.selected_case_with_analysis
        }
        # 使用 insert_one 方法来插入新记录
        self.db_handler.collection.insert_one(session_data)

    def get_selected_cases(self) -> List[dict]:
        return self.collections["selected_cases"]

    def set_selected_cases(self, cases: List[dict]):
        self.collections["selected_cases"] = cases
        self._save_to_db()

    def get_selected_text(self) -> List[dict]:
        return self.collections["selected_text"]

    def set_selected_text(self, texts: List[dict]):
        self.collections["selected_text"] = texts
        self._save_to_db()

    def get_selected_case_with_analysis(self) -> dict:
        return self.selected_case_with_analysis

    def set_selected_case_with_analysis(self, case_with_analysis: dict):
        self.selected_case_with_analysis = case_with_analysis
        self._save_to_db()