from fastapi import FastAPI, HTTPException, Body
from datetime import datetime
from models.DatabaseHandler import TextDatabaseHandler, CasesDatabaseHandler
import uvicorn
import urllib.parse
from agents.roles import *
from config import SessionConfig
from pydantic import BaseModel
from typing import Optional


DATABASE = ""
USR_NAME= ""
PSW = ""
username = urllib.parse.quote_plus(USR_NAME)
password = urllib.parse.quote_plus(PSW)
db_uri = f"mongodb://{username}:{password}@" + DATABASE

# 对象初始化
ca = CaseAnalysis("CaseAnalysis")
cr = CaseRanker("CaseRanker")
ta = TextAnalysis("TextAnalysis")
tr = TextRanker("TextRanker")
cp = CoursePlanner("TextRanker")
iw = IntroWriter("IntroWriter")
# 配置MongoDB连接
text_db_handler = TextDatabaseHandler(
    uri=db_uri,
    db_name="education",
    collection_name="lesson_text"
)

cases_db_handler = CasesDatabaseHandler(
    uri=db_uri,
    db_name="education",
    collection_name="cases"
)

counter_plus = 8

is_traditional_subject = False


current_session_id = None

app = FastAPI()

# 定义基本的数据类型

class Case(BaseModel):
    process: str
    embedding: List

class Revision(BaseModel):
    request: str
    response: str

class Text(BaseModel):
    title: str
    author: str
    grade: str
    unit: str
    type: str
    text: str
    embedding: List
    

class AnalysedCase(BaseModel):
    case: str
    definition: str
    detail: str
    embedding: List
    revision: List[Revision]

class AnalyseAndRankCasesRequest(BaseModel):
    cases: List[Case]
    texts: List[Text]
    counter: int
    subject: Optional[str] = False
    

class EditCasesRequest(BaseModel):
    selected_case: AnalysedCase
    texts: List[Text]
    advice: str

class AnalyseTextBySelectedCase(BaseModel):
    selected_case: AnalysedCase
    texts: List[Text]
    counter: int

class EditTextBySelectedCase(BaseModel):
    selected_case: AnalysedCase
    texts: List[Text]
    advice: str

class AnalysedText(BaseModel):
    title: str
    analysed_text: str
    rating: str
    reason: str
    text: str
    revision: List[Revision]

class FinalCase(BaseModel):
    case: str
    example_text_title: str
    detail: str
    definition: str
    origin: str
    embedding: List
    revision: List[Revision]


class FinalText(BaseModel):
    title: str
    analysed_text: str
    rating: str
    reason: str
    revision: List[Revision]


class Collection(BaseModel):
    case: FinalCase
    text: List[FinalText]
    class_num: int

class Summary(BaseModel):
    intro: str
    plan: str
    activities: List

class ActivitiesRequest(BaseModel):
    case: FinalCase
    text: List[FinalText]
    summary: Summary


@app.get("/explore/get-text-list")
async def get_text_list():
    """获取课文列表接口"""
    try:
        text_list = text_db_handler.get_text_list()
        return text_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取课文列表失败: {str(e)}")
    
@app.get("/explore/get-text-title-list")
async def get_text_list():
    """获取课文列表接口"""
    try:
        text_list = text_db_handler.get_text_title_list()
        return [{"title":t["title"], "type":t["type"]} for t in text_list]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取课文列表失败: {str(e)}")


class TitleRequest(BaseModel):
    title: str

@app.post("/explore/get-text-by-title")
async def get_text_by_title(request: TitleRequest):
    try:
        # 从请求中获取 title
        title = request.title
        # 查询数据库
        text = text_db_handler.get_lesson_by_title(title)
        # print(text)
        if not text:
            raise HTTPException(status_code=404, detail="课文未找到")
        return text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取课文失败: {str(e)}")


class TitlesRequest(BaseModel):
    titles: List[str]

@app.post("/explore/get-texts-by-titles")
async def get_texts_by_titles(request: TitlesRequest):
    try:
        # 从请求中获取 titles 列表
        titles = request.titles
        # 查询数据库
        texts = text_db_handler.get_lessons_by_titles(titles)
        if not texts:
            raise HTTPException(status_code=404, detail="没有找到课文")
        return texts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取课文失败: {str(e)}")


@app.get("/newSession")
async def new_session():
    """创建一个新的sessionID"""
    global current_session_id
    current_session_id = datetime.now().strftime("%Y%m%d%H%M%S")
    return {"sessionID": current_session_id}


@app.get("/getSessionID")
async def get_session_id():
    """获取当前的sessionID"""
    if current_session_id is None:
        raise HTTPException(status_code=404, detail="Session ID 未创建")
    return {"sessionID": current_session_id}



@app.on_event("shutdown")
async def shutdown_event():
    """在应用关闭时关闭数据库连接"""
    await text_db_handler.close()



class GetCaseRequest(BaseModel):
    subjects: List[str]

@app.post("/explore/get-cases-by-categories")
async def get_cases_by_categories(request: GetCaseRequest):
    # global is_traditional_subject
    try:
        # 从请求中获取 subjects 列表
        subjects = request.subjects
        # if ("综合实践" not in subjects):
        #     is_traditional_subject = True
        # else:
        #     is_traditional_subject = False
        # 查询数据库
        cases = cases_db_handler.get_cases_by_subjects(subjects)
        if not cases:
            raise HTTPException(status_code=404, detail="未找到相关案例")
        return cases
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取案例失败: {str(e)}")


@app.post("/explore/analyse-and-rank-cases-with-text")
async def analyse_and_rank_cases_with_text(request: AnalyseAndRankCasesRequest):
    # global is_traditional_subject
    try:
        if request.subject == '综合实践':
            is_traditional_subject = False
        else:
            is_traditional_subject = True
        # is_traditional_subject = request.subjects
        if len(request.cases) > 1:
            cases = [c.process for c in request.cases]
            case_embeddings = [np.array(c.embedding) for c in request.cases]
            texts = [t.title + "\n" + t.text for t in request.texts]
            text_embeddings = [np.array(t.embedding) for t in request.texts]
            print("is_traditional_subject: ", is_traditional_subject)
            result = ca.run("user", "analyse_case_set_by_text_set", case_set=cases, text_set=texts, generate_num=counter_plus, 
                            text_embeddings = text_embeddings, case_embeddings = case_embeddings, counter=request.counter, is_traditional_subject=is_traditional_subject)
            # print(result)
            return result
        else:
            cases = [c.process for c in request.cases]
            texts = [t.title + "\n" + t.text for t in request.texts]
            result = ca.run("user", "analyse_subject_case_by_text_set", case_set = cases, text_set=texts, generate_num = 3)
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析和排名失败: {str(e)}")
    
@app.post("/explore/analyse-one-case-with-text")
async def analyse_one_case_with_text(request: AnalyseAndRankCasesRequest):
    try:
        cases = [c.process for c in request.cases]
        texts = [t.title + "\n" + t.text for t in request.texts]

        result = ca.run("user", "analyse_one_case_by_text_set", case_set=cases, text_set=texts)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加失败: {str(e)}")
    

@app.post("/explore/edit-one-case-with-text")
async def edit_one_case_with_text(request: EditCasesRequest):
    try:
        cases = [request.selected_case.case + "\n" + request.selected_case.detail]
        texts = [t.title + "\n" + t.text for t in request.texts]

        result = ca.run("user", "edit_one_case_by_text_set", case_set=cases, text_set=texts, advice=request.advice)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加失败: {str(e)}")


@app.post("/explore/edit-one-text-by-selected-case")
async def edit_one_text_by_selected_case(request: EditTextBySelectedCase):
    try:
        c = request.selected_case
        case = c.case + "\n" + c.definition + "\n" + c.detail
        # texts = [t.title + "\n" + t.text for t in request.texts]
        texts = request.texts
        analysed_text = ta.run("user", "edit_one_text_by_selected_case", selected_case=case, text_set=[t.title + "\n" + t.text for t in request.texts], advice=request.advice)
        # analysed_text_set = analysed_text_set["analysed_text_set"]
        # ranked_text_set = tr.run('TextAnalysis', 'rank_analysed_text_set_by_selected_case', text_set=texts, selected_case = case, analysed_text_set = analysed_text_set, top_num = 2)
        return analysed_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")
    

@app.post("/explore/analyse-text-by-selected-case")
async def analyse_text_by_selected_case(request: AnalyseTextBySelectedCase):
    try:
        c = request.selected_case
        case = c.case + "\n" + c.definition
        case_embedding = np.array(c.embedding)
        # texts = [t.title + "\n" + t.text for t in request.texts]
        texts = request.texts
        text_embeddings = np.array([t.embedding for t in request.texts])
        counter = request.counter
        analysed_text_set = ta.run("user", "analyse_text_by_selected_case", selected_case=case, text_set=[t.title + "\n" + t.text for t in request.texts],
                                    case_embedding = case_embedding, text_embeddings = text_embeddings, counter= counter, top_n=counter_plus)
        analysed_text_set = analysed_text_set["analysed_text_set"]
        ranked_text_set = tr.run('TextAnalysis', 'rank_analysed_text_set_by_selected_case', text_set=[t.title + "\n" + t.text for t in request.texts], selected_case = case, 
                                 analysed_text_set = analysed_text_set, top_n = counter_plus, counter= counter, case_embedding = case_embedding, text_embeddings = text_embeddings)
        return ranked_text_set
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析和排名失败: {str(e)}")

@app.post("/explore/analyse-one-text-by-selected-case")
async def analyse_one_text_by_selected_case(request: AnalyseTextBySelectedCase):
    try:
        c = request.selected_case
        case = c.case + "\n" + c.definition
        # texts = [t.title + "\n" + t.text for t in request.texts]
        texts = request.texts
        analysed_text = ta.run("user", "analyse_one_text_by_selected_case", selected_case=case, text_set=[t.title + "\n" + t.text for t in texts])
        # analysed_text_set = analysed_text_set["analysed_text_set"]
        # ranked_text_set = tr.run('TextAnalysis', 'rank_analysed_text_set_by_selected_case', text_set=texts, selected_case = case, analysed_text_set = analysed_text_set, top_num = 2)
        return analysed_text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@app.post("/explore/plan-course")
async def plan_course(request: Collection):
    try:
        c = request.case
        # if c.revision != []:
        #     revision = '\n'.join(["user: " + r.request + "AI: " + r.response for r in c.revision])
        #     case = c.case +'\n定义：'+ c.definition +'\n分析：' + c.detail + "\n教师感兴趣的部分和提问：" + revision
        # else:
        case = c.case +'\n分析：' + c.detail
        texts = []
        for t in request.text:
            content = "《" + t.title + "》\n" + t.analysed_text
            # if t.revision != []:
            #     revision_text = '\n'.join(["user: " + r.request + "AI: " + r.response for r in t])
            # else:
            revision_text = ''
            texts.append('\n'.join([content, revision_text]))
        text_set = texts
        plan = cp.run("user", "plan_course_by_selected_case_and_selected_analysed_text_set", selected_case=case, selected_analysed_text_set=text_set,
                                    class_num = request.class_num)
        intro = iw.run("user", "write_intro_by_selected_case_and_selected_analysed_text_set", selected_case=case, selected_analysed_text_set=text_set, plan=plan)
        return {"plan": plan, "intro": intro}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析和排名失败: {str(e)}")
    


@app.post("/explore/plan-activities")
async def plan_activities(request: ActivitiesRequest):
    try:
        c = request.case
        # if c.revision != []:
        #     revision = '\n'.join(["user: " + r.request + "AI: " + r.response for r in c.revision])
        #     case = c.case +'\n定义：'+ c.definition +'\n分析：' + c.detail + "\n教师感兴趣的部分和提问：" + revision
        # else:
        case = c.case +'\n分析：' + c.detail
        texts = []
        for t in request.text:
            content = "《" + t.title + "》\n" + t.analysed_text
            # if t.revision != []:
            #     revision_text = '\n'.join(["user: " + r.request + "AI: " + r.response for r in t])
            # else:
            revision_text = ''
            texts.append('\n'.join([content, revision_text]))
        text_set = texts
        plan = request.summary.plan
        intro = request.summary.intro
        activities = iw.run("user", "plan_activities", selected_case=case, selected_analysed_text_set=text_set, plan=plan, intro=intro)
        return {"activities": activities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析和排名失败: {str(e)}")


@app.post("/explore/set-preference")
async def set_preference(preference: dict = Body(...)):
    """
    设置会话配置的接口，用于更新已选择的案例、文本和案例分析。

    该函数根据提供的JSON数据更新会话配置。它期望接收到一个包含`session_id`以及
    `selected_cases`、`selected_text`、`selected_case_with_analysis`的JSON对象。
    如果提供了这些属性中的任何一个，它们将用于更新数据库中的相应会话配置。
    如果某个属性未提供，则该配置保持不变。

    参数:
        preference (dict): 包含会话配置数据的JSON对象。预期的键包括:
                           - session_id: 表示唯一会话标识符的字符串。
                           - selected_cases (可选): 表示选定案例的字典列表。
                           - selected_text (可选): 表示选定文本的字典列表。
                           - selected_case_with_analysis (可选): 表示选定案例及其分析的字典。

    返回:
        dict: 包含状态消息的JSON响应，指示更新是否成功。
    """
    session_id = preference.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")

    # 检查是否需要更新属性
    has_updates = False
    session_config = SessionConfig(session_id=session_id)

    if "selected_cases" in preference:
        session_config.set_selected_cases(preference["selected_cases"])
        has_updates = True

    if "selected_text" in preference:
        session_config.set_selected_text(preference["selected_text"])
        has_updates = True

    if "selected_case_with_analysis" in preference:
        session_config.set_selected_case_with_analysis(preference["selected_case_with_analysis"])
        has_updates = True

    if has_updates:
        return {"status": "success", "message": "Session preferences updated."}
    else:
        return {"status": "no_change", "message": "No updates were made."}
    


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000, reload=True)
