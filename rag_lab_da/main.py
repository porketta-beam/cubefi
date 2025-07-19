from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
import datetime
from openai import OpenAI
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI client
openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# LangChain 메모리 설정
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# 대화 메모리 (사용자별로 관리)
conversation_memories = {}

# Pydantic models
class ChatbotMessage(BaseModel):
    message: str
    user_id: Optional[str] = "default"

class ChatbotResponse(BaseModel):
    success: bool
    data: dict

class ClearMemoryRequest(BaseModel):
    user_id: str = "default"

# 세금 관련 지식 베이스 (RAG용)
tax_knowledge_base = [
    {
        "category": "국내주식 양도소득세",
        "content": "국내주식 양도소득세는 분리과세로 15.4%입니다. 2,000만원 이하는 15.4%, 초과분은 종합소득세율이 적용됩니다. 종합소득세율은 소득에 따라 6.6%~49.5%까지 적용됩니다."
    },
    {
        "category": "해외주식 양도소득세", 
        "content": "해외주식 양도소득세는 22%로 국내주식보다 높습니다. 해외주식은 종합과세로 처리되며, 다른 소득과 합산하여 과세됩니다."
    },
    {
        "category": "배당소득세",
        "content": "배당소득세는 15.4%입니다. 배당소득은 분리과세로 처리되며, 연간 배당소득이 2,000만원 이하인 경우 15.4%가 적용됩니다."
    },
    {
        "category": "세금 신고",
        "content": "주식 양도소득세는 매년 5월에 종합소득세 신고와 함께 신고합니다. 증권사에서 발급하는 거래내역서를 준비해야 합니다."
    },
    {
        "category": "절세 방법",
        "content": "주식 투자 절세 방법: 1) 손실과 이익을 상계하여 과세표준을 줄이기, 2) 장기투자로 세율 혜택 받기, 3) 연말정산 시 손실공제 활용하기"
    }
]

def find_relevant_knowledge(user_question: str) -> str:
    """RAG: 관련 지식 검색"""
    relevant_docs = []
    keywords = user_question.lower().split(' ')
    
    for doc in tax_knowledge_base:
        if any(keyword in doc["content"].lower() or keyword in doc["category"].lower() 
               for keyword in keywords):
            relevant_docs.append(f"{doc['category']}: {doc['content']}")
    
    return '\n\n'.join(relevant_docs)

def get_user_memory(user_id: str):
    """사용자별 메모리 반환"""
    if user_id not in conversation_memories:
        conversation_memories[user_id] = ConversationBufferMemory(
            memory_key="history",
            return_messages=True
        )
    return conversation_memories[user_id]

def create_conversation_chain(user_id: str):
    """사용자별 대화 체인 생성"""
    memory = get_user_memory(user_id)
    
    prompt_template = """
    당신은 주식 투자 세금 전문가입니다. 다음 세금 관련 지식을 바탕으로 사용자의 질문에 답변해주세요.

    세금 관련 지식:
    {rag_context}

    대화 기록:
    {history}

    사용자: {input}
    세금 전문가:
    """
    
    prompt = PromptTemplate(
        input_variables=["rag_context", "history", "input"],
        template=prompt_template
    )
    
    return ConversationChain(
        llm=llm,
        memory=memory,
        prompt=prompt,
        verbose=False
    )

async def generate_response_with_memory(user_message: str, user_id: str = "default") -> str:
    """메모리를 사용한 OpenAI API 호출"""
    try:
        # RAG: 관련 지식 검색
        relevant_knowledge = find_relevant_knowledge(user_message)
        
        # 사용자별 대화 체인 생성
        conversation_chain = create_conversation_chain(user_id)
        
        # 대화 체인으로 응답 생성
        response = conversation_chain.predict(
            input=user_message,
            rag_context=relevant_knowledge
        )
        
        return response
    except Exception as error:
        print(f'LangChain API Error: {error}')
        return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

async def generate_response(user_message: str) -> str:
    """기존 OpenAI API 호출 (메모리 없음)"""
    try:
        # RAG: 관련 지식 검색
        relevant_knowledge = find_relevant_knowledge(user_message)
        
        system_prompt = f"""당신은 주식 투자 세금 전문가입니다. 다음 세금 관련 지식을 바탕으로 사용자의 질문에 답변해주세요:

{relevant_knowledge}

답변 시 다음 규칙을 따라주세요:
1. 정확하고 이해하기 쉽게 설명
2. 구체적인 수치와 예시 제공
3. 친근하고 도움이 되는 톤으로 답변
4. 한국어로 답변"""

        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7,
        )

        return completion.choices[0].message.content
    except Exception as error:
        print(f'OpenAI API Error: {error}')
        return "죄송합니다. 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.post("/api/chatbot/message")
async def chatbot_message(message: str = Form(...), user_id: str = Form("default")):
    """챗봇 메시지 처리 (메모리 기능 포함)"""
    try:
        print("=== RECEIVED MESSAGE ===")
        print(f"Message: {message}")
        print(f"User ID: {user_id}")
        print("=== RECEIVED MESSAGE END ===")
        
        if not message:
            return {"error": "메시지가 필요합니다."}
        
        # 메모리를 사용한 응답 생성
        response = await generate_response_with_memory(message, user_id)
        
        return {
            "success": True,
            "data": {
                "message": response,
                "timestamp": str(datetime.datetime.now().isoformat()),
                "user_id": user_id
            }
        }
        
    except Exception as error:
        print(f'=== CHATBOT ERROR ===')
        print(error)
        print(f'=== CHATBOT ERROR END ===')
        return {"error": "챗봇 응답 생성 중 오류가 발생했습니다."}

@app.post("/api/chatbot/clear-memory")
async def clear_memory(request: ClearMemoryRequest):
    """사용자 대화 메모리 초기화"""
    try:
        if request.user_id in conversation_memories:
            conversation_memories[request.user_id].clear()
            return {
                "success": True,
                "message": f"사용자 {request.user_id}의 대화 메모리가 초기화되었습니다."
            }
        else:
            return {
                "success": True,
                "message": f"사용자 {request.user_id}의 메모리가 존재하지 않습니다."
            }
    except Exception as error:
        print(f'=== CLEAR MEMORY ERROR ===')
        print(error)
        return {"error": "메모리 초기화 중 오류가 발생했습니다."}

@app.get("/api/chatbot/users")
async def get_all_users():
    """모든 사용자 목록 조회"""
    try:
        users = list(conversation_memories.keys())
        return {
            "success": True,
            "data": {
                "users": users
            }
        }
    except Exception as error:
        print(f'=== GET USERS ERROR ===')
        print(error)
        return {"error": "사용자 목록 조회 중 오류가 발생했습니다."}

# 자동 리로드 켜져있음
# reload=True 일 때, 코드 수정 때마다 최신 코드로 자동 리로드됨
# 다만, 여러 개의 uvicorn을 실행할 때는 여러 uvicorn이 실행될 수도 있으니 주의할 것
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)