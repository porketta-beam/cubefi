"""
RAG Lab Server Modules

이 패키지는 RAG Lab의 핵심 기능을 담고 있는 독립 모듈들입니다.

구조:
- auto_rag/: RAG 시스템 핵심 모듈
- api/: FastAPI 백엔드 API
- bot_response.py: OpenAI 클라이언트 유틸리티
- fastapi_app.py: FastAPI 애플리케이션 서버

이 모듈들은 server/ 폴더에서 완전히 독립적으로 실행됩니다.
"""

# 버전 정보
__version__ = "1.0.0"

# 핵심 모듈 re-export
try:
    from .auto_rag.mod import (
        ChromaDBManager,
        RAGSystemManager,
        ChatInterfaceManager
    )
    __all__ = [
        "ChromaDBManager",
        "RAGSystemManager", 
        "ChatInterfaceManager"
    ]
except ImportError:
    # Import 경로 수정 전에는 무시
    __all__ = []