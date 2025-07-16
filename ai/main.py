from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
import datetime
from openai import OpenAI
from dotenv import load_dotenv

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

# Pydantic models
class ChatbotMessage(BaseModel):
    message: str

class ChatbotResponse(BaseModel):
    success: bool
    data: dict

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

async def generate_response(user_message: str) -> str:
    """OpenAI API 호출"""
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
async def chatbot_message(message: str = Form(...)):
    """챗봇 메시지 처리"""
    try:
        print("=== RECEIVED MESSAGE ===")
        print(message)
        print("=== RECEIVED MESSAGE END ===")
        
        if not message:
            return {"error": "메시지가 필요합니다."}
        
        # OpenAI API로 응답 생성
        response = await generate_response(message)
        
        return {
            "success": True,
            "data": {
                "message": response,
                "timestamp": str(datetime.datetime.now().isoformat())
            }
        }
        
    except Exception as error:
        print(f'=== CHATBOT ERROR ===')
        print(error)
        print(f'=== CHATBOT ERROR END ===')
        return {"error": "챗봇 응답 생성 중 오류가 발생했습니다."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)