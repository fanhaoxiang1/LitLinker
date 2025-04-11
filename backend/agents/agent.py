from zhipuai import ZhipuAI
from agents.memory import History, Memory, save

from typing import List

API_KEY = ""

class Agent:
    # 这里假设 ZhipuAI 是一个已经定义好的类，用于与 API 交互
    client = ZhipuAI(api_key=API_KEY)

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.memory = Memory(agent_name)
    
    def convert_string(self, d, s):
        for key, value in d.items():
            s = s.replace(f"{{{key}}}", value)
        return s

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model="GLM-4-0520", 
            messages=[
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )
        return response.choices[0].message.content
    
    def embed(self, content: str) -> List[float]:
        client = ZhipuAI(api_key="ee5b61796531485267cc9e1451af3662.ehHFtIupifZG7Mmj") 
        response = client.embeddings.create(
            model="embedding-3", #填写需要调用的模型编码
            input=[content
            ],
        )
        return response.data[0].embedding
    
    def run(self, send_from: str = '', command: str = ''):
        raise NotImplementedError("Subclasses should implement this method.")

