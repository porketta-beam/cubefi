from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
from fastapi.middleware.cors import CORSMiddleware
# from mod.bot_response import bot_response  # Commented out - now using RAG system
import asyncio
import uvicorn
import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import API routers
from api.routers.documents import router as documents_router
from api.routers.rag import router as rag_router
from api.services.rag_config_service import rag_config_service

app = FastAPI(title="RAG Lab API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # 또는 ["http://localhost:3000"] 등 프론트엔드 주소로 제한 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(documents_router)
app.include_router(rag_router)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "RAG Lab API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

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
            
            print(f"받은 메시지: {user_message}")
            
            try:
                # 입력 검증
                if not user_message.strip():
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "❌ 빈 메시지입니다. 질문을 입력해주세요."
                    }))
                    continue
                
                # RAG 시스템 스트리밍 호출
                history = [{"role": "user", "content": user_message}]
                
                # 스트리밍 시작 신호
                await websocket.send_text(json.dumps({
                    "type": "start",
                    "message": "🔍 문서를 검색하고 답변을 생성하는 중..."
                }))
                
                # RAG chain 스트리밍 응답 전송
                response_stream = rag_config_service.create_rag_chain_stream(history)
                
                for chunk in response_stream:
                    if hasattr(chunk, "content") and chunk.content:
                        content = chunk.content
                        
                        # JSON 형태로 청크 전송
                        await websocket.send_text(json.dumps({
                            "type": "chunk",
                            "content": content
                        }, ensure_ascii=False))
                        
                        # 실시간 렌더링을 위한 더 짧은 지연
                        await asyncio.sleep(0.005)
                
                # 스트리밍 완료 신호
                await websocket.send_text(json.dumps({
                    "type": "done"
                }))
                
            except Exception as stream_error:
                print(f"RAG 스트리밍 중 오류: {stream_error}")
                
                # 사용자 친화적인 오류 메시지
                error_message = str(stream_error)
                if "❌" not in error_message:
                    error_message = f"❌ RAG 시스템 오류: {error_message}"
                
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": error_message
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

# ========== 기존 bot_response 기반 WebSocket 코드 (주석처리됨) ==========
"""
@app.websocket("/ws/chat")
async def websocket_chat_old(websocket: WebSocket):
    await websocket.accept()
    print("새 WebSocket 연결 수락됨")
    
    try:
        while True:
            # 클라이언트로부터 메시지 수신
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get('message', '')
            
            print(f"받은 메시지: {user_message}")
            
            try:
                # OpenAI API 스트리밍 호출
                history = [{"role": "user", "content": user_message}]
                response_stream = bot_response(history)
                
                # 스트리밍 시작 신호
                await websocket.send_text(json.dumps({
                    "type": "start",
                    "message": "스트리밍 시작"
                }))
                
                # 스트리밍 응답 전송
                for chunk in response_stream:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        
                        # JSON 형태로 청크 전송
                        await websocket.send_text(json.dumps({
                            "type": "chunk",
                            "content": content
                        }, ensure_ascii=False))
                        
                        # 실시간 렌더링을 위한 더 짧은 지연
                        await asyncio.sleep(0.005)
                
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
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)