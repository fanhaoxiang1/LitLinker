import json
import pymongo
from bson import ObjectId
import re

class Transform:
    # 不需要这个，FastApi会自动化转json
    # @staticmethod
    # def to_json(data):
    #     """将Python数据类型转换为JSON字符串"""
    #     json_data = json.dumps(data, ensure_ascii=False, indent=4)
    #     print(json_data)
    #     return json_data

    @staticmethod
    def parse_json_to_python(json_string):
        """
        将JSON字符串转换为Python数据类型

        参数:
        json_string (str): 一个 JSON 格式的字符串。

        返回:
        dict 或 list: 输入 JSON 字符串的 Python 表示形式。
        """
        try:
            python_data = json.loads(json_string)
            return python_data
        except json.JSONDecodeError as e:
            print(f"解码 JSON 时出错: {e}")
            return None


class LessonTextTransformModel:
    def __init__(self, db_uri, db_name):
        """
        初始化 Transform 类，连接到 MongoDB 数据库。
        """
        self.client = pymongo.MongoClient(db_uri)
        self.db = self.client[db_name]

    def parse_lesson_text(self, txt_content):
        lesson_data = {
            "title": "",
            "author": "",
            "grade": 0,
            "unit": 0,
            "type": "",
            "paragraphs": []
        }
        num = 0
        paragraphs = txt_content.strip().split('\n\n')
        for para in paragraphs:
            if num == 0:
                lines = para.strip().split('\n')
                if lines[1].startswith('$'):
                    lesson_data["author"] = lines[1][1:].strip()
                if lines[2].startswith('!'):
                    lesson_data["type"] = lines[2][1:].strip()
                if lines[0].startswith('#'):
                    metadata = lines[0][1:].strip().split(',')
                    lesson_data["title"] = metadata[0]
                    lesson_data["grade"] = (metadata[1])
                    lesson_data["unit"] = (metadata[2])
                num += 1
            else:
                para_data = {
                    "paragraph_number": len(lesson_data["paragraphs"]) + 1,
                    "paragraph_text": para.strip()
                }
                lesson_data["paragraphs"].append(para_data)

        return lesson_data

    def import_to_db(self, structured_data, collection_name):
        collection = self.db[collection_name]
        collection.insert_one(structured_data)

    def txt2db(self, txt_content, collection_name):
        structured_data = self.parse_lesson_text(txt_content)
        self.import_to_db(structured_data, collection_name)

    def get_lesson_by_id(self, lesson_id, collection_name):
        collection = self.db[collection_name]
        return collection.find_one({"_id": ObjectId(lesson_id)})

    def get_paragraph_by_number(self, lesson_id, paragraph_number, collection_name):
        lesson = self.get_lesson_by_id(lesson_id, collection_name)
        if lesson:
            for paragraph in lesson["paragraphs"]:
                if paragraph["paragraph_number"] == paragraph_number:
                    return paragraph
        return None
    
    def get_lesson_by_title(self, title: str, collection_name: str):
        collection = self.db[collection_name]
        return collection.find_one({"title": title})

    def get_lessons_by_titles(self, titles, collection_name: str):
        collection = self.db[collection_name]
        return list(collection.find({"title": {"$in": titles}}))

    def get_paragraph_text_by_number(self, lesson_id, paragraph_number, collection_name):
        paragraph = self.get_paragraph_by_number(lesson_id, paragraph_number, collection_name)
        if paragraph:
            return paragraph["paragraph_text"]
        return None

class CaseTransformModel:
    def __init__(self, db_uri, db_name):
        self.client = pymongo.MongoClient(db_uri)
        self.db = self.client[db_name]

    def parse_case(self, case_content):
        case_data = {
            "background": "",
            "subjects": [],
            "context": "",
            "goal": "",
            "process": ""
        }

        clean_text = re.sub(r'\uf06c', '', case_content).strip()
        lines = clean_text.strip().split('\n')
        current_section = None
        section_content = []

        for line in lines:
            line = line.strip()
            if line.startswith('1.背景：'):
                if current_section:
                    case_data[current_section] = '\n'.join(section_content).strip()
                current_section = "background"
                section_content = [line[5:].strip()]
            elif line.startswith('2.科目：'):
                if current_section:
                    case_data[current_section] = '\n'.join(section_content).strip()
                current_section = "subjects"
                # Extract subject names and strip any extra spaces
                subjects = line[5:].strip().split('，')
                arr = [subject for subject in subjects]
                case_data["subjects"] = list(arr)
                section_content = []
            elif line.startswith('3.背景：'):
                # if current_section:
                #     case_data[current_section] = '\n'.join(section_content).strip()
                current_section = "context"
                section_content = [line[4:].strip()]
            elif line.startswith('4.教学目标：'):
                if current_section:
                    case_data[current_section] = '\n'.join(section_content).strip()
                current_section = "goal"
                section_content = [line[6:].strip()]
            elif line.startswith('5.流程：'):
                if current_section:
                    case_data[current_section] = '\n'.join(section_content).strip()
                current_section = "process"
                section_content = []
            else:
                section_content.append(line)

        if current_section:
            case_data[current_section] = '\n'.join(section_content).strip()
        return case_data

    def import_to_db(self, structured_data, collection_name):
        collection = self.db[collection_name]
        collection.insert_one(structured_data)

    def txt_case2db(self, case_content, collection_name):
        structured_data = self.parse_case(case_content)
        print(structured_data)
        self.import_to_db(structured_data, collection_name)

    def get_case_by_id(self, case_id, collection_name):
        collection = self.db[collection_name]
        return collection.find_one({"_id": ObjectId(case_id)})