"""
RAG Lab Server - 독립 배포용 모듈

이 패키지는 팀 배포용으로 완전히 독립적으로 실행 가능한 RAG 시스템입니다.
모든 필요한 의존성이 포함되어 있으며, main.py를 통해 실행할 수 있습니다.

실행 방법:
    PYTHONPATH=. python main.py

구조:
    - api/: FastAPI 백엔드 서비스
    - modules/: RAG 핵심 모듈 (auto_rag 복사본)
    - web/: Next.js 프론트엔드 
    - raw_data/: 업로드된 문서 저장소
    - chroma_db/: 벡터 데이터베이스
"""

__version__ = "1.0.0"
__author__ = "RAG Lab Team"