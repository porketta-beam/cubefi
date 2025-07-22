# RAG Lab Server - 독립 배포 모듈

## 개요

이 모듈은 RAG Lab 프로젝트의 팀 배포용 독립 실행 패키지입니다. 모든 필요한 의존성이 포함되어 있어 이 폴더만으로 완전한 RAG 시스템을 실행할 수 있습니다.

## 실행 방법

### 1. 환경 설정

```bash
# Python 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가:

```env
OPENAI_API_KEY=your_openai_api_key_here
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=rag_lab_server
```

### 3. 서버 실행

```bash
# 통합 실행 (FastAPI + Next.js 동시)
PYTHONPATH=. python main.py

# 개별 실행
PYTHONPATH=. python -m server.api.main    # FastAPI만
PYTHONPATH=. streamlit run web/app.py      # Streamlit만
```

### 4. 접속

- FastAPI 백엔드: http://localhost:8000
- Streamlit 웹: http://localhost:8501
- API 문서: http://localhost:8000/docs

## 폴더 구조

```
server/
├── main.py                # 통합 실행 파일
├── requirements.txt       # Python 의존성
├── .env.example          # 환경 변수 예시
├── raw_data/             # 업로드된 문서
├── chroma_db/            # 벡터 데이터베이스
├── api/                  # FastAPI 백엔드
│   ├── models/           # 데이터 모델
│   ├── routers/          # API 라우터
│   └── services/         # 비즈니스 로직
├── modules/              # RAG 핵심 모듈
│   └── mod/              # 유틸리티 모듈
└── web/                  # Next.js 프론트엔드
    ├── components/       # React 컴포넌트
    ├── pages/            # 페이지
    └── util/             # 유틸리티
```

## 주요 기능

- **문서 업로드 및 처리**: PDF, TXT 파일 업로드 및 벡터화
- **RAG 질의응답**: 세법 관련 질문에 대한 정확한 답변
- **실시간 스트리밍**: Server-Sent Events 기반 실시간 응답
- **문서 관리**: 업로드된 문서 관리 및 설정
- **모니터링**: LangSmith 기반 추적 및 모니터링

## 개발 정보

- FastAPI: 백엔드 API 서버
- Next.js: 프론트엔드 웹 애플리케이션  
- ChromaDB: 벡터 데이터베이스
- OpenAI: LLM 및 임베딩 모델
- LangSmith: 모니터링 및 추적

## 문제 해결

### 포트 충돌 시
```bash
# 포트 변경
SERVER_PORT=8080 WEB_PORT=8502 python main.py
```

### 의존성 문제 시
```bash
# 의존성 재설치
pip install --force-reinstall -r requirements.txt
```

### PYTHONPATH 문제 시
```bash
# 절대 경로로 실행
cd server
export PYTHONPATH=$(pwd)
python main.py
```