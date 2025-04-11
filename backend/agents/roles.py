from agents.agent import Agent
from agents.memory import History, save, getGlobalHistory
from prompts import *
import random
from typing import List
import re
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from concurrent.futures import ThreadPoolExecutor, as_completed


## 要求：[0, k] 上大于0且单调递减。
def inverted_sigmoid_weight(rank, k):
    mid_point = k / 2
    x = (rank - mid_point) / mid_point
    return 1 / (1 + np.exp(x))

def convex_weight(rank, k):
    return 1 - (rank / k) ** 2

def concave_weight(rank, k):
    return 1 - np.sqrt(rank / k)

def vote_weight(rank, k):
    return 1

class CaseAnalysis(Agent):
    def __init__(self, agent_name: str):
        super().__init__(agent_name)

    # def formatter(self, response_list):
    #     result_list = []

    def formatter(self, response_list):
        result_list = []

        for response in response_list:
            # 存储原始的 response 到 origin 字段
            origin = response

            # 用 ## 分割字符串
            parts = response.split('##')
            # 去掉每一个子字符串中的 \n
            parts = [part.replace('\n', '').strip() for part in parts]
            
            # 构建字典，根据分割后的子字符串数量判断格式是否正确
            if len(parts) == 4:  # 分割后会有一个空的部分在最前面
                result = {
                    "case": parts[1],
                    "example_text_title": parts[2],
                    "detail": parts[3],
                    "format": True,
                    "origin": origin
                }
            else:
                result = {
                    "case": parts[1] if len(parts) > 1 else "",
                    "example_text_title": parts[2] if len(parts) > 2 else "",
                    "detail": parts[3] if len(parts) > 3 else "",
                    "format": False,
                    "origin": origin
                }

            # 将处理好的字典添加到结果列表中
            result_list.append(result)

        return result_list
    
    def find_most_relevant_cases(self, text_embeddings, case_set, case_embeddings):
        case_scores = {i: {'total_score': 0, 'case': case, 'embedding': case_embeddings[i]} for i, case in enumerate(case_set)}

        for text in text_embeddings:
            aggregated_text_embedding = text

            # 初始化 ranking_list 来存储每个 case 的相似度和对应的 case_id
            ranking_list = []

            # 遍历每个 case
            for i, case in enumerate(case_set):
                case_chunks = [case_embeddings[i]]

                # 计算相似度
                similarities = cosine_similarity([aggregated_text_embedding], case_chunks).flatten()
                max_similarity = np.max(similarities)

                # 存储相似度和 case_id
                ranking_list.append((max_similarity, i))

            # 对 ranking_list 按相似度从高到低排序
            ranking_list.sort(reverse=True, key=lambda x: x[0])

            # 对排序后的排名进行加权处理
            k = 15
            weight_func = vote_weight
            for rank, (similarity, case_id) in enumerate(ranking_list[:k]):
                weight = weight_func(rank, k)
                case_scores[case_id]['total_score'] += weight
                # case_scores[case_id]['total_score'] += weight * similarity

        # 按累积的投票得分对案例进行排序
        sorted_cases = sorted(case_scores.values(), key=lambda x: x['total_score'], reverse=True)
        top_cases = sorted_cases
        return top_cases

    def chain_set(self, analysed_case_set):
        if not isinstance(analysed_case_set, list) or not all(isinstance(case, str) for case in analysed_case_set):
            raise ValueError("Input must be a list of strings")
        # 用编号连接每个字符串并用换行符分隔
        chained_result = "\n".join(f"{i+1}. {case}" for i, case in enumerate(analysed_case_set))
        return chained_result

    def run(self, send_from: str = '', command: str = '', case_set = None, text_set = None, generate_num = 8, advice =None, text_embeddings=None, case_embeddings = None, counter = 0, is_traditional_subject=False):
        ## 在FastAPI中调用这个函数激活整个流程。
        if send_from == "user" and command == "analyse_case_set_by_text_set":
            response_list = [None] * generate_num  # 预分配列表，确保顺序
            cases = self.find_most_relevant_cases(text_embeddings, case_set, case_embeddings)[counter: counter+generate_num]

            # 定义一个辅助函数，用于生成 response
            def generate_response(index, case):
                # 随机打乱产生更丰富的结果
                text_set_rand = random.sample(text_set, len(text_set))
                if is_traditional_subject == False:
                    return index, self.generate(self.convert_string({"text_set": self.chain_set(text_set_rand), "case": case["case"]}, case_analysis_prompt))
                else:
                    return index, self.generate(self.convert_string({"text_set": self.chain_set(text_set_rand), "case": case["case"]}, case_analysis_prompt_for_subjects))
            # 使用 ThreadPoolExecutor 来并行化任务
            with ThreadPoolExecutor(max_workers=generate_num) as executor:  # max_workers 可以根据需要调整
                futures = {executor.submit(generate_response, idx, case): idx for idx,case in enumerate(cases)}
                
                for future in as_completed(futures):
                    case = futures[future]
                    try:
                        index, response = future.result()
                        response_list[index] = response
                    except Exception as e:
                        print(f"Error processing case {case['case']}: {e}")

            # 结果 res 在 FastAPI 中传给 cr = CaseRanker 示例：cr.run("CaseAnalysis", "rank_analysed_case_set_by_text_set", **res)
            response_list = self.formatter(response_list)
            
            # 增加原始定义
            for ind, r in enumerate(response_list):
                r["definition"] = cases[ind]['case']
                r["embedding"] = list(cases[ind]['embedding'])
                
            return {"analysed_case_set": response_list}
        
        if send_from == "user" and command == "analyse_one_case_by_text_set":
            response_list = []
            cases = case_set
            case = cases[0]
            result = self.generate(self.convert_string({"text_set": self.chain_set(text_set), "case": case}, case_analysis_prompt))
            # 结果res在FastAPI中传给cr = CaseRanker）示例：cr.run("CaseAnalysis", "rank_analysed_case_set_by_text_set", **res)
            response_list = self.formatter([result])
            # 增加原始定义
            for ind, r in enumerate(response_list):
                r["definition"] = cases[ind]
                r["embedding"] = list(self.embed(cases[ind]))
            return {"analysed_case": response_list[0]}
        
        if send_from == "user" and command == "edit_one_case_by_text_set":
            response_list = []
            cases = case_set
            case = cases[0]
            result = self.generate(self.convert_string({"text_set": self.chain_set(text_set), "analysed_case": case, "advice": advice}, case_edit_prompt))
            # 结果res在FastAPI中传给cr = CaseRanker）示例：cr.run("CaseAnalysis", "rank_analysed_case_set_by_text_set", **res)
            # response_list = self.formatter([result])
            # # 增加原始定义
            # for ind, r in enumerate(response_list):
            #     r["definition"] = cases[ind]
            return {"request": advice, "response": result}
        
        if send_from == "user" and command == "analyse_subject_case_by_text_set":
            # cases是复制n次的subject
            ## case是[subject]
            cases = case_set * 3
            response_list = [None] * generate_num  # 预分配列表，确保顺序
            # 定义一个辅助函数，用于生成 response
            def generate_response(index, case):
                # 随机打乱产生更丰富的结果
                text_set_rand = random.sample(text_set, len(text_set))
                # example匹配：
                if case == "科学":
                    example = sci_temp
                elif case == "音乐":
                    example = music_temp
                elif case == "美术":
                    example = art_temp
                elif case == "数学":
                    example = math_temp
                elif case == "历史":
                    example = his_temp
                # print(self.convert_string({"text_set": self.chain_set(text_set_rand), "subject": case, "examples": example}, case_analysis_prompt_more_subject))
                return index, self.generate(self.convert_string({"text_set": self.chain_set(text_set_rand), "subject": case, "example": example}, case_analysis_prompt_more_subject))

            # 使用 ThreadPoolExecutor 来并行化任务
            with ThreadPoolExecutor(max_workers=generate_num) as executor:  # max_workers 可以根据需要调整
                futures = {executor.submit(generate_response, idx, case): idx for idx,case in enumerate(cases)}
                
                for future in as_completed(futures):
                    case = futures[future]
                    try:
                        index, response = future.result()
                        response_list[index] = response
                    except Exception as e:
                        print(f"Error processing case: {e}")

            # 结果 res 在 FastAPI 中传给 cr = CaseRanker 示例：cr.run("CaseAnalysis", "rank_analysed_case_set_by_text_set", **res)
            response_list = self.formatter(response_list)
            
            # 增加原始定义
            for ind, r in enumerate(response_list):
                r["definition"] = "与学科相关的案例暂不提供定义。"
                r["embedding"] = list(self.embed(response_list[ind]["detail"]))
                
            return {"analysed_case_set": response_list}


class CaseRanker(Agent):
    def __init__(self, agent_name: str):
        super().__init__(agent_name)

    def formatter(self, response):
        pass

    def chain_set(self, analysed_case_set):
        if not isinstance(analysed_case_set, list) or not all(isinstance(case, str) for case in analysed_case_set):
            raise ValueError("Input must be a list of strings")
        # 用编号连接每个字符串并用换行符分隔
        chained_result = "\n".join(f"{i+1}. {case}" for i, case in enumerate(analysed_case_set))
        return chained_result

    def run(self, send_from: str = '', command: str = '', analysed_case_set = None, text_set = None, top_num = 3):
        if send_from == "CaseAnalysis" and command == "rank_analysed_case_set_by_text_set":
            analysed_case_set = self.chain_set(analysed_case_set)
            response = self.generate(self.convert_string({"analysed_case_set": analysed_case_set, "text_set": text_set, "top_num": top_num},
                                                          case_ranker_prompt))
            response = self.formatter(response)
            return response

class TextAnalysis(Agent):
    def __init__(self, agent_name: str):
        super().__init__(agent_name)

    def formatter(self, response):
        pass
    def find_most_relevant_texts(self, texts, case_embedding, text_embeddings):
        text_scores = {}
        for i, text in enumerate(texts):
            text_embedding = text_embeddings[i]

            # 将案例的所有块嵌入与该段落嵌入进行比较
            similarities = cosine_similarity([text_embedding], [case_embedding]).flatten()
            max_similarity = np.max(similarities)

            text_scores[i] = {
                'similarity': max_similarity,
                'text': text
            }

        # 按相似度对课文进行排序
        sorted_texts = sorted(text_scores.values(), key=lambda x: x['similarity'], reverse=True)
        top_texts = sorted_texts
        return [t["text"] for t in top_texts]

    def run(self, send_from: str = '', command: str = '', selected_case = '', text_set = [], advice = None, text_embeddings = None, case_embedding=None, top_n = 8, counter=0):
        if send_from == "user" and command == "analyse_text_by_selected_case":
            response_list = []
            # 所有课文都分析
            # 分析 top_n 课文
            text_set = self.find_most_relevant_texts(case_embedding=case_embedding, texts = text_set, text_embeddings=text_embeddings)
            if counter >= len(text_set):
                counter = 0
            text_set = text_set[counter: counter+top_n]

            # 定义一个辅助函数，用于生成分析内容
            def generate_content(text):
                return self.generate(self.convert_string({"text_content": text, "selected_case": selected_case}, text_analysis_prompt))

            # 使用 ThreadPoolExecutor 来并行化任务
            with ThreadPoolExecutor(max_workers=top_n) as executor:  # max_workers 可以根据需要调整
                futures = {executor.submit(generate_content, text): text for text in text_set}
                
                for future in as_completed(futures):
                    text = futures[future]
                    try:
                        content = future.result()
                        response_list.append(content)
                    except Exception as e:
                        print(f"Error processing text {text}: {e}")

            return {"analysed_text_set": response_list}
            ## call text_ranker
        if send_from == "user" and command == "analyse_one_text_by_selected_case":
            try:
                response_list = []
                # 所有课文都分析
                for text in text_set:
                    content = self.generate(self.convert_string({"text_content": text, "selected_case": selected_case}, text_analysis_prompt))
                    response_list.append(content)
                    # print(content)
                    ## 这里的response包含
                response = response_list[0]
                print(response.split('\n', 1))
                response_new = {
                    "title": response.split('\n', 1)[0],
                    "analysed_text": response.split('\n', 1)[1],
                    "rating": "用户添加不参与评分",
                    "reason": "用户添加无评估理由",
                    "revision":[]
                }
                    # response["title"] = response["analysed_text"].split('\n', 1)[0]
                    # response["analysed_text"] = response["analysed_text"].split('\n', 1)[1]
                    # response["rating"] = "用户添加不参与评分"
                    # response["reason"] = "用户添加无评估理由"
                return {"analysed_text": response_new}
            except Exception as e:
                print(e)
                return
        if send_from == "user" and command == "edit_one_text_by_selected_case":
            response_list = []
            # 所有课文都分析
            for text in text_set:
                content = self.generate(self.convert_string({"text_content": text, "selected_case": selected_case, "advice": advice}, text_edit_prompt))
                response_list.append(content)
                # print(content)
                ## 这里的response包含
            response = response_list[0]
            return {"revision": response}       
        

class TextRanker(Agent):
    def __init__(self, agent_name: str):
        super().__init__(agent_name)
    def find_most_relevant_texts(self, texts, case_embedding, text_embeddings):
        text_scores = {}
        for i, text in enumerate(texts):
            text_embedding = text_embeddings[i]

            # 将案例的所有块嵌入与该段落嵌入进行比较
            similarities = cosine_similarity([text_embedding], [case_embedding]).flatten()
            max_similarity = np.max(similarities)

            text_scores[i] = {
                'similarity': max_similarity,
                'text': text
            }

        # 按相似度对课文进行排序
        sorted_texts = sorted(text_scores.values(), key=lambda x: x['similarity'], reverse=True)
        top_texts = sorted_texts
        return [t["text"] for t in top_texts]

    # def formatter(self, analysed_text_set, response):
    #     # 用 "## " 分割 response
    #     print(analysed_text_set)
    #     split_responses = response.split("## ")
    #     # 移除空字符串
    #     split_responses = [resp for resp in split_responses if resp.strip() != ""]
    #     print(split_responses)
    #     formatted_response = []
    #     # 遍历所有的元素
    #     for i in range(len(analysed_text_set)):
    #         split_response = split_responses[i].strip()
            
    #         # 用 " - " 分割每个部分
    #         parts = split_response.split(" - ")
            
    #         # 提取 rating 和 reason
    #         rating = parts[0].strip() if len(parts) > 0 else ""
    #         title = parts[1].strip() if len(parts) > 1 else ""
    #         reason = parts[2].strip() if len(parts) > 2 else ""

    #         # 构建分析结果
    #         result = {
    #             "title": title,  # 使用 text_original 中相应的 title
    #             # "analysed_text": analysed_text_set[i],  
    #             "analysed_text": analysed_text_set[i].split('\n', 1)[1],
    #             "rating": rating,
    #             "reason": reason,
    #             "revision": [],
    #         }
    #         formatted_response.append(result)

    #     return {"ranked_text": formatted_response}
    # 全新Formatter
    def formatter(self, analysed_text_set, response):
        # 用 "## " 分割 response
        split_responses = response.split("## ")
        # 移除空字符串
        split_responses = [resp for resp in split_responses if resp.strip() != ""]
        # 构建一个字典，用于存储 response 中的每个部分，以标题为键
        response_dict = {}
        for split_response in split_responses:
            parts = split_response.split(" - ")
            rating = parts[0].strip() if len(parts) > 0 else ""
            title = parts[1].strip() if len(parts) > 1 else ""
            reason = parts[2].strip() if len(parts) > 2 else ""
            
            response_dict[title] = {
                "rating": rating,
                "reason": reason
            }
        print(response)
        formatted_response = []
        
        # 遍历 analysed_text_set，根据标题匹配 response_dict 中的内容
        for text in analysed_text_set:
            title = text.split("\n", 1)[0].strip()  # 提取标题
            analysed_text = text.split("\n", 1)[1].strip()  # 提取分析文本内容

            if title in response_dict:
                matched_response = response_dict[title]
                rating = matched_response["rating"]
                reason = matched_response["reason"]
            else:
                rating = ""
                reason = ""

            # 构建分析结果
            result = {
                "title": title,
                "analysed_text": analysed_text,
                "rating": rating,
                "reason": reason,
                "revision": [],
            }
            formatted_response.append(result)

        return {"ranked_text": formatted_response}

    def chain_set(self, analysed_case_set):
        if not isinstance(analysed_case_set, list) or not all(isinstance(case, str) for case in analysed_case_set):
            raise ValueError("Input must be a list of strings")
        # 用编号连接每个字符串并用换行符分隔
        chained_result = "\n".join(f"{i+1}. {case}" for i, case in enumerate(analysed_case_set))
        return chained_result

    def run(self, send_from: str = '', command: str = '', text_set = None, selected_case = None, analysed_text_set = None, top_n = 8, counter=0, case_embedding=None, text_embeddings=None):
        try:
            if send_from == "TextAnalysis" and command == "rank_analysed_text_set_by_selected_case":
                text_set = self.find_most_relevant_texts(case_embedding=case_embedding, texts = text_set, text_embeddings=text_embeddings)
                if counter >= len(text_set):
                    counter = 0
                text_set = text_set[counter: counter+top_n]
                analysed_text_set_original = analysed_text_set.copy()
                analysed_text_set = self.chain_set(analysed_text_set)
                text_original = text_set.copy()
                # text_set = [t.title + "\n" + t.text for t in text_set]
                text_set = self.chain_set(text_set)
                response = self.generate(self.convert_string({"analysed_text_set": analysed_text_set, "text_set": text_set, "selected_case": selected_case},
                                                            text_ranker_prompt))
                # print(response)
                ## 需要: text in text_original的text.title作为属性title。
                ## 要sentence in analysed_text_set(这是一个List)的每个字符串作为属性analysed_text。
                ## 要response的分数，作为属性rating，同时，要reason。
                # print(analysed_text_set_original)
                # print(text_original)
                response = self.formatter(analysed_text_set_original, response)
                return response
        except Exception as e:
            print(e)
        
class CoursePlanner(Agent):
    def __init__(self, agent_name: str):
        super().__init__(agent_name)

    def formatter(self, response):
        return response
    def chain_set(self, analysed_case_set):
        if not isinstance(analysed_case_set, list) or not all(isinstance(case, str) for case in analysed_case_set):
            raise ValueError("Input must be a list of strings")
        # 用编号连接每个字符串并用换行符分隔
        chained_result = "\n".join(f"{i+1}. {case}" for i, case in enumerate(analysed_case_set))
        return chained_result

    def run(self, send_from: str = '', command: str = '', selected_case = None, selected_analysed_text_set = None, class_num = 4):
        if send_from == "user" and command == "plan_course_by_selected_case_and_selected_analysed_text_set":
            selected_analysed_text_set = self.chain_set(selected_analysed_text_set)
            # print(self.convert_string({"selected_analysed_text_set": selected_analysed_text_set, "selected_case": selected_case, "class_num": str(class_num)},
            #                                               course_planner_prompt))
            response = self.generate(self.convert_string({"selected_analysed_text_set": selected_analysed_text_set, "selected_case": selected_case, "class_num": str(class_num)},
                                                          course_planner_prompt))
            response = self.formatter(response)
            return response
        
class IntroWriter(Agent):
    def __init__(self, agent_name: str):
        super().__init__(agent_name)

    def formatter(self, response):
        return response
    def chain_set(self, analysed_case_set):
        if not isinstance(analysed_case_set, list) or not all(isinstance(case, str) for case in analysed_case_set):
            raise ValueError("Input must be a list of strings")
        # 用编号连接每个字符串并用换行符分隔
        chained_result = "\n".join(f"{i+1}. {case}" for i, case in enumerate(analysed_case_set))
        return chained_result
    def run(self, send_from: str = '', command: str = '', selected_case = None, selected_analysed_text_set = None, plan= None, intro=None):
        if send_from == "user" and command == "write_intro_by_selected_case_and_selected_analysed_text_set":
            selected_analysed_text_set = self.chain_set(selected_analysed_text_set)
            response = self.generate(self.convert_string({"selected_analysed_text_set": selected_analysed_text_set, "selected_case": selected_case, "plan": plan},
                                                          intro_writer_prompt))
            response = self.formatter(response)
            return response
        if send_from == "user" and command == "plan_activities":
            selected_analysed_text_set = self.chain_set(selected_analysed_text_set)
            response = self.generate(self.convert_string({"selected_analysed_text_set": selected_analysed_text_set, "selected_case": selected_case, "plan": plan, "intro": intro},
                                                          activity_planner_prompt))
            response = self.formatter(response)
            return response