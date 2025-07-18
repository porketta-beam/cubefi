from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio
import uvicorn
import json
from fastapi.middleware.cors import CORSMiddleware
from ref.bot_response import bot_response
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from dotenv import load_dotenv
import os

load_dotenv(override=True)

app = FastAPI()

# 사용자별 대화 메모리 저장소
user_memories = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 또는 ["http://localhost:3000"] 등 프론트엔드 주소로 제한 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"

class MemoryRequest(BaseModel):
    user_id: str

def get_user_memory(user_id: str):
    """사용자별 메모리 가져오기"""
    if user_id not in user_memories:
        user_memories[user_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    return user_memories[user_id]

def create_memory_aware_response(user_id: str, user_message: str):
    """메모리를 고려한 응답 생성"""
    memory = get_user_memory(user_id)
    
    # LangChain ChatOpenAI 모델 생성
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.5,
        openai_api_key=os.getenv("API2")
    )
    
    # 메모리에서 대화 기록 가져오기
    chat_history = memory.chat_memory.messages
    
    # 새로운 사용자 메시지 추가
    memory.chat_memory.add_user_message(user_message)
    
    # AI 응답 생성 (이전 대화 기록 포함)
    messages = [HumanMessage(content=user_message)] + chat_history
    response = llm.invoke(messages)
    
    # AI 응답을 메모리에 저장
    memory.chat_memory.add_ai_message(response.content)
    
    return response.content

@app.post("/chat")
async def chat_response(request: ChatRequest):
    """Simple one-shot chatbot response API with streaming"""
    async def generate_response():
        try:
            # 메모리를 고려한 응답 생성
            response_text = create_memory_aware_response(request.user_id, request.message)
            
            # 스트리밍 형태로 응답 전송
            for char in response_text:
                yield f"data: {char}\n\n"
                await asyncio.sleep(0.01)  # 자연스러운 타이핑 효과
                    
        except Exception as e:
            yield f"data: 챗봇 응답 생성 중 오류가 발생했습니다: {str(e)}\n\n"
    
    return StreamingResponse(generate_response(), media_type="text/event-stream")

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    print("새 WebSocket 연결 수락됨")
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get('message', '')
            user_id = message_data.get('user_id', 'default')
            
            print(f"받은 메시지: {user_message} (사용자: {user_id})")
            
            try:
                # 메모리를 고려한 응답 생성
                response_text = create_memory_aware_response(user_id, user_message)
                
                # 스트리밍 시작 신호
                await websocket.send_text(json.dumps({
                    "type": "start",
                    "message": "스트리밍 시작"
                }))
                
                # 스트리밍 응답 전송
                for char in response_text:
                    await websocket.send_text(json.dumps({
                        "type": "chunk",
                        "content": char
                    }, ensure_ascii=False))
                    
                    # 실시간 렌더링을 위한 짧은 지연
                    await asyncio.sleep(0.01)
                
                # 스트리밍 완료 신호
                await websocket.send_text(json.dumps({
                    "type": "done"
                }))
                
            except Exception as stream_error:
                print(f"스트리밍 중 오류: {stream_error}")
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"스트리밍 중 오류가 발생했습니다: {str(stream_error)}"
                }))
            
    except WebSocketDisconnect:
        print("클라이언트가 연결을 정상적으로 끊었습니다")
    except Exception as e:
        print(f"WebSocket 연결 오류: {e}")
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "연결 오류가 발생했습니다"
            }))
        except:
            print("연결이 이미 끊어져 오류 메시지를 보낼 수 없습니다")
    finally:
        print("WebSocket 연결이 종료되었습니다")

@app.post("/api/chatbot/message")
async def chatbot_message(request: ChatRequest):
    """메모리가 있는 챗봇 메시지 API"""
    try:
        response_text = create_memory_aware_response(request.user_id, request.message)
        return {"response": response_text}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/chatbot/clear-memory")
async def clear_memory(request: MemoryRequest):
    """사용자 메모리 초기화"""
    if request.user_id in user_memories:
        del user_memories[request.user_id]
    return {"message": f"사용자 {request.user_id}의 대화 기록이 초기화되었습니다."}

@app.get("/api/chatbot/users")
async def list_users():
    """현재 메모리가 있는 사용자 목록"""
    return {"users": list(user_memories.keys())}

@app.get("/api/chatbot/memory/{user_id}")
async def get_memory(user_id: str):
    """특정 사용자의 메모리 내용 조회"""
    if user_id in user_memories:
        memory = user_memories[user_id]
        messages = memory.chat_memory.messages
        return {
            "user_id": user_id,
            "message_count": len(messages),
            "messages": [
                {
                    "type": "user" if isinstance(msg, HumanMessage) else "ai",
                    "content": msg.content
                }
                for msg in messages
            ]
        }
    else:
        return {"message": f"사용자 {user_id}의 메모리가 없습니다."}




async def chat_stream():
      for i in range(5):
          yield f"data: 챗봇 응답 {i}\n"
          await asyncio.sleep(0.5)

@app.get("/chat/stream")
async def stream_chat():
    return StreamingResponse(chat_stream(), media_type="text/event-stream")
  
@app.post("/chat/stream")
async def stream_chat_post():
    async def response_stream():
        message = "안녕하세요! 주식 투자 세금에 대해 궁금하신 점을 말씀해주세요."
        # 단어 단위로 스트림 전송
        for word in message.split():
            yield f"data: {word} "
            await asyncio.sleep(0.2)
    return StreamingResponse(response_stream(), media_type="text/event-stream")



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)