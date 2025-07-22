# RAG Lab Server - 프로덕션급 RAG API 서버

## 개요

RAG Lab Server는 세법 관련 문서 검색 및 질의응답을 위한 프로덕션급 FastAPI 기반 서버입니다. 
OpenAI GPT 모델과 ChromaDB를 활용한 RAG(Retrieval-Augmented Generation) 시스템으로, 
문서 업로드, 벡터화, 실시간 질의응답, 평가 및 모니터링 기능을 제공합니다.

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
# 메인 서버 실행 (권장)
python main.py

# 또는 FastAPI 직접 실행
PYTHONPATH=. python -m modules.fastapi_app

# 개발 환경 실행 (auto-reload)
python run.py
```

### 4. 접속

- **FastAPI API 서버**: http://localhost:8000
- **API 문서 (Swagger)**: http://localhost:8000/docs
- **OpenAPI 스펙**: http://localhost:8000/openapi.json
- **헬스체크**: http://localhost:8000/health

## 📁 프로젝트 구조

```
server/
├── main.py                           # 메인 서버 실행 파일
├── run.py                           # 개발 환경 실행 파일
├── requirements.txt                 # Python 의존성
├── requirements-dev.txt             # 개발 의존성
├── setup.py                        # 패키지 설정
├── raw_data/                       # 업로드된 문서 저장소
├── chroma_db/                      # ChromaDB 벡터 데이터베이스
├── logs/                           # 서버 로그
├── config/                         # 설정 파일
│   ├── __init__.py
│   └── settings.py                 # 애플리케이션 설정
├── modules/                        # 핵심 모듈
│   ├── fastapi_app.py             # FastAPI 애플리케이션
│   ├── bot_response.py            # 응답 처리 로직
│   ├── api/                       # API 관련 모듈
│   │   ├── models/               # Pydantic 데이터 모델
│   │   │   ├── document.py       # 문서 모델
│   │   │   ├── rag.py           # RAG 요청/응답 모델
│   │   │   └── document_config.py # 문서 설정 모델
│   │   ├── routers/              # FastAPI 라우터
│   │   │   ├── documents.py      # 문서 관리 API
│   │   │   ├── rag.py           # RAG 질의응답 API
│   │   │   └── document_configs.py # 문서 설정 API
│   │   └── services/             # 비즈니스 로직
│   │       ├── document_service.py     # 문서 서비스
│   │       ├── rag_service.py          # RAG 서비스
│   │       └── rag_config_service.py   # RAG 설정 서비스
│   ├── services/                  # 핵심 서비스
│   │   ├── document_lifecycle_service.py  # 문서 생명주기 관리
│   │   ├── configurable_ingestion_service.py # 문서 수집 처리
│   │   ├── document_config_service.py      # 문서 설정 관리
│   │   ├── document_delete_service.py      # 문서 삭제 서비스
│   │   └── metadata_extractors.py         # 메타데이터 추출
│   ├── exceptions/               # 커스텀 예외
│   │   ├── __init__.py
│   │   └── document_exceptions.py
│   ├── validators/               # 검증 로직
│   │   ├── __init__.py
│   │   └── chunk_validator.py
│   ├── utils/                    # 유틸리티
│   │   ├── __init__.py
│   │   └── security.py
│   └── auto_rag/                # Streamlit RAG 인터페이스
│       ├── rag_streamlit_v2.py  # Streamlit 앱
│       ├── raw_data/            # 로컬 데이터
│       ├── chroma_db/           # 로컬 벡터 DB
│       └── mod/                 # RAG 관리 모듈
└── scripts/                     # 유틸리티 스크립트
    ├── performance_test.py      # 성능 테스트
    ├── backfill_default_config.py # 설정 마이그레이션
    └── run_tests.py            # 테스트 실행
```

## 🚀 주요 기능

### 📄 문서 관리
- **파일 업로드**: PDF, TXT 파일 업로드 및 자동 처리
- **문서 벡터화**: OpenAI text-embedding-3-large 모델 사용
- **청크 분할**: 설정 가능한 청크 크기 및 오버랩
- **메타데이터 추출**: 자동 메타데이터 추출 및 관리
- **문서 삭제**: 안전한 문서 삭제 및 정리

### 🤖 RAG 질의응답
- **실시간 질의응답**: GPT-4 기반 정확한 답변 생성
- **문맥 기반 검색**: 유사도 및 MMR 검색 지원
- **스트리밍 응답**: Server-Sent Events 기반 실시간 응답
- **다중 모델 지원**: GPT-4, GPT-4o-mini, GPT-3.5-turbo 지원
- **설정 가능한 파라미터**: 온도, 검색 개수 등 실시간 조정

### 📊 평가 및 모니터링
- **RAG 평가**: RAGAS 기반 자동 성능 평가
- **LangSmith 추적**: 실시간 쿼리 및 응답 모니터링
- **OpenTelemetry**: 성능 메트릭 및 추적
- **로깅**: 구조화된 로깅 및 에러 추적

### 🔧 설정 관리
- **문서별 설정**: 개별 문서의 처리 설정 관리
- **동적 설정**: 런타임 설정 변경 지원
- **설정 검증**: 자동 설정 검증 및 복구

## 🛠️ 기술 스택

### 백엔드
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **Python 3.11+**: 최신 Python 기능 활용
- **Pydantic**: 데이터 검증 및 설정 관리
- **Uvicorn**: ASGI 서버 (운영 환경)

### AI/ML
- **OpenAI GPT**: GPT-4, GPT-4o-mini, GPT-3.5-turbo
- **OpenAI Embeddings**: text-embedding-3-large
- **LangChain**: LLM 애플리케이션 프레임워크
- **RAGAS**: RAG 시스템 평가 프레임워크

### 데이터베이스
- **ChromaDB**: 벡터 데이터베이스
- **SQLite**: 메타데이터 저장 (ChromaDB 내장)

### 모니터링 & 로깅
- **LangSmith**: LLM 애플리케이션 모니터링
- **OpenTelemetry**: 분산 추적 및 메트릭
- **Structlog**: 구조화된 로깅

### 개발 도구
- **Pytest**: 테스트 프레임워크
- **Ruff**: 코드 포맷팅 및 린팅
- **MyPy**: 정적 타입 검사

## 📡 API 엔드포인트

### 문서 관리 API (`/api/documents`)

```http
POST   /api/documents/upload-file     # 파일 업로드
GET    /api/documents/list           # 문서 목록 조회
GET    /api/documents/status         # 데이터베이스 상태
DELETE /api/documents/{doc_id}       # 문서 삭제
GET    /api/documents/sync           # 문서 동기화
DELETE /api/documents/database       # 데이터베이스 삭제
```

### RAG 질의응답 API (`/api/rag`)

```http
POST   /api/rag/chat                 # 질의응답 (JSON)
POST   /api/rag/chat/stream          # 스트리밍 질의응답
POST   /api/rag/generate-questions   # 질문 생성
POST   /api/rag/evaluate             # RAG 평가
```

### 문서 설정 API (`/api/document-configs`)

```http
GET    /api/document-configs/        # 모든 설정 조회
GET    /api/document-configs/{doc_id} # 특정 문서 설정
PUT    /api/document-configs/{doc_id} # 설정 업데이트
```

### 기타

```http
GET    /health                       # 헬스체크
GET    /docs                         # Swagger UI
GET    /openapi.json                 # OpenAPI 스펙
```

## 💡 사용 예시

### 1. 문서 업로드

```bash
curl -X POST "http://localhost:8000/api/documents/upload-file" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@세법해설.pdf"
```

### 2. 질의응답

```bash
curl -X POST "http://localhost:8000/api/rag/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "개인 투자자의 해외주식 세금은 어떻게 계산되나요?",
    "model": "gpt-4o-mini",
    "temperature": 0.0,
    "search_type": "similarity",
    "k": 3
  }'
```

### 3. 스트리밍 응답

```bash
curl -X POST "http://localhost:8000/api/rag/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "법인세 신고 기한은 언제인가요?",
    "model": "gpt-4o-mini"
  }'
```

### 4. 문서 목록 조회

```bash
curl "http://localhost:8000/api/documents/list"
```

## 🧪 테스트

```bash
# 전체 테스트 실행
python scripts/run_tests.py

# 특정 테스트
pytest tests/unit/test_rag_endpoint.py -v

# 성능 테스트
python scripts/performance_test.py
```

## 🚀 배포

### Docker 배포 (예정)

```bash
# Docker 이미지 빌드
docker build -t rag-lab-server .

# 컨테이너 실행
docker run -p 8000:8000 --env-file .env rag-lab-server
```

### 시스템 요구사항

- **Python**: 3.11 이상
- **메모리**: 최소 4GB RAM (권장 8GB)
- **저장소**: 최소 2GB 여유 공간
- **CPU**: 2코어 이상 권장

## 🔧 문제 해결

### 포트 충돌 시
```bash
# 포트 변경
PORT=8080 python main.py

# 또는 환경 변수 설정
export PORT=8080
python main.py
```

### 의존성 문제 시
```bash
# 의존성 재설치
pip install --force-reinstall -r requirements.txt

# 또는 가상환경 재생성
rm -rf venv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### PYTHONPATH 문제 시
```bash
# 절대 경로로 실행
cd server
export PYTHONPATH=$(pwd)
python main.py

# Windows에서
cd server
set PYTHONPATH=%cd%
python main.py
```

### ChromaDB 문제 시
```bash
# 데이터베이스 리셋
rm -rf chroma_db/
python main.py  # 자동으로 새 DB 생성
```

### OpenAI API 키 문제 시
```bash
# 환경 변수 확인
echo $OPENAI_API_KEY

# .env 파일 확인
cat .env
```

### 메모리 부족 시
```bash
# 청크 크기 조정 (설정에서)
# chunk_size: 1000 → 500
# 또는 더 작은 모델 사용
# model: "gpt-4" → "gpt-4o-mini"
```

## 📚 추가 문서

- [API 상세 문서](http://localhost:8000/docs) - Swagger UI
- [OpenAPI 스펙](http://localhost:8000/openapi.json) - 기계 읽기 가능한 스펙
- [성능 테스트 결과](scripts/performance_test.py) - 벤치마크 데이터
- [배포 가이드](scripts/README.md) - 운영 환경 배포 가이드

## 🤝 기여

1. 이 저장소를 포크합니다
2. 새 기능 브랜치를 생성합니다 (`git checkout -b feature/새기능`)
3. 변경사항을 커밋합니다 (`git commit -am '새 기능 추가'`)
4. 브랜치에 푸시합니다 (`git push origin feature/새기능`)
5. Pull Request를 생성합니다

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원

문제가 있거나 질문이 있으시면:

- GitHub Issues를 통해 버그 리포트 및 기능 요청
- 프로젝트 Wiki에서 추가 문서 확인
- 개발팀에 직접 연락

---

**RAG Lab Server** - 세법 전문 RAG 시스템 🏛️⚖️