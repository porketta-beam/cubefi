from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import redis
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='../.env', override=True)

class SimpleQACacheBot:
    def __init__(self):
        self.apikey = os.getenv("API2")
        self.chain_model = os.getenv("OPENAI_DEFAULT_MODEL")
        self.host = os.getenv("REDIS_HOST")
        self.pwd = os.getenv("REDIS_PWD")
        self.redis_client = redis.Redis(
            host=self.host,
            port=17159,
            password=self.pwd
        )
        self.llm = ChatOpenAI(model=self.chain_model,
                              temperature=0.7,
                              api_key=self.apikey)

    def get_ai_response(self, user_text: str) -> str:
        # 1. Redis에서 캐시 조회
        cached = self.redis_client.get(user_text)
        if cached:
            return cached.decode("utf-8")
        # 2. 캐시 없으면 LLM 호출
        response = self.llm.invoke([HumanMessage(content=user_text)])
        ai_text = response.content
        # 3. 캐시에 저장
        self.redis_client.set(user_text, ai_text)
        return ai_text