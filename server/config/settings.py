"""
RAG Lab Server 설정 모듈

환경 변수와 기본 설정을 관리하는 모듈입니다.
"""

import os
from pathlib import Path
from typing import Optional
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, ConfigDict
except ImportError:
    from pydantic import BaseSettings, Field, ConfigDict

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent.parent

class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # API 키
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    langsmith_api_key: Optional[str] = Field(None, env="LANGSMITH_API_KEY")
    
    # 서버 설정
    server_port: int = Field(8000, env="SERVER_PORT")
    debug: bool = Field(False, env="DEBUG")
    cors_origins: str = Field("http://localhost:3000", env="CORS_ORIGINS")
    
    # LangSmith 설정
    langsmith_project: str = Field("rag_lab_server", env="LANGSMITH_PROJECT")
    langsmith_tracing: bool = Field(True, env="LANGSMITH_TRACING")
    
    # RAG 시스템 설정
    chunk_size: int = Field(800, env="CHUNK_SIZE")
    chunk_overlap: int = Field(200, env="CHUNK_OVERLAP")
    model_name: str = Field("gpt-4o-mini", env="MODEL_NAME")
    temperature: float = Field(0.2, env="TEMPERATURE")
    
    # 파일 경로
    chroma_persist_directory: str = Field("./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    raw_data_directory: str = Field("./raw_data", env="RAW_DATA_DIRECTORY")
    chroma_collection_name: str = Field("rag_collection", env="CHROMA_COLLECTION_NAME")
    
    # 성능 설정
    max_file_size: int = Field(100, env="MAX_FILE_SIZE")
    max_concurrent_requests: int = Field(10, env="MAX_CONCURRENT_REQUESTS")
    
    # 로깅 설정
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("./logs/server.log", env="LOG_FILE")
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # 추가 환경 변수를 무시하도록 설정
    )
        
    def get_chroma_path(self) -> Path:
        """ChromaDB 저장 경로 반환"""
        path = Path(self.chroma_persist_directory)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path.mkdir(parents=True, exist_ok=True)
        return path
        
    def get_raw_data_path(self) -> Path:
        """원본 데이터 저장 경로 반환"""
        path = Path(self.raw_data_directory)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path.mkdir(parents=True, exist_ok=True)
        return path
        
    def get_log_path(self) -> Path:
        """로그 파일 경로 반환"""
        path = Path(self.log_file)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

# 전역 설정 인스턴스
settings = Settings()

# 환경 변수 설정 함수들
def setup_environment():
    """환경 변수 설정"""
    
    # OpenAI 설정
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    
    # LangSmith 설정
    if settings.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
        
        if settings.langsmith_tracing:
            os.environ["LANGSMITH_TRACING"] = "true"
    
    # 경로 설정
    os.environ["CHROMA_PERSIST_DIRECTORY"] = str(settings.get_chroma_path())
    os.environ["RAW_DATA_DIRECTORY"] = str(settings.get_raw_data_path())

def get_api_url(endpoint: str = "") -> str:
    """API URL 생성"""
    base_url = f"http://localhost:{settings.server_port}"
    return f"{base_url}/{endpoint.lstrip('/')}" if endpoint else base_url