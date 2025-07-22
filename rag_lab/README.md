# RAG Lab - AI-Powered Tax Consultation System

이 프로젝트는 RAG (Retrieval-Augmented Generation) 기반의 AI 세금 상담 시스템을 제공합니다. FastAPI 백엔드 서버와 Next.js 프론트엔드로 구성되어 있으며, 주식 투자 세금 관련 전문 지식을 제공합니다.

## 📁 프로젝트 구조

```
rag_lab/
├── server/          # 🚀 FastAPI 백엔드 서버 (독립 실행 가능)
├── web/             # 🌐 Next.js 프론트엔드
├── api/             # 📡 API 모듈 (레거시)
├── auto_rag/        # 🤖 자동 RAG 시스템 (레거시)
└── docs/            # 📚 문서
```

## 🚀 빠른 시작 (server 모듈)

### 자동 설정 (권장)

```bash
cd server
python setup.py
```

자동 설정 스크립트는 다음을 수행합니다:
- Python 3.8+ 버전 확인
- 가상환경 생성 및 활성화
- 의존성 설치
- 환경변수 파일(.env) 생성

### 수동 설정

```bash
cd server
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 환경 변수 설정

`.env` 파일을 생성하고 필요한 API 키를 설정하세요:
```env
# 필수 설정
OPENAI_API_KEY=your_openai_api_key_here

# 선택적 설정 (추적 및 모니터링)
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=rag_lab_project
LANGSMITH_TRACING=true
```

### 서버 실행

```bash
# server 디렉토리에서
python main.py
```

또는 플랫폼별 실행 스크립트 사용:
```bash
# Windows
run.bat

# Linux/Mac
./run.sh
```

## 🌐 접속 URL

- **FastAPI 서버**: http://localhost:8000
- **API 문서 (Swagger)**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔧 서버 모듈 상세 사용법

server 모듈은 독립적으로 실행 가능한 완전한 RAG 시스템입니다.

### 주요 기능

- **RAG 기반 질의응답**: ChromaDB를 이용한 문서 검색 및 GPT 기반 답변 생성
- **실시간 문서 업로드**: PDF 문서를 업로드하여 벡터 DB에 자동 저장
- **LangSmith 추적**: 모든 AI 호출 및 성능 모니터링
- **OpenTelemetry 지원**: 서버 성능 및 로그 추적
- **웹소켓 지원**: 실시간 채팅 인터페이스

### API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/health` | GET | 서버 상태 확인 |
| `/api/chat` | POST | RAG 기반 채팅 |
| `/api/documents/upload` | POST | PDF 문서 업로드 |
| `/api/documents` | GET | 문서 목록 조회 |
| `/ws/chat` | WebSocket | 실시간 채팅 |

### 환경 변수 설정

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `SERVER_PORT` | 8000 | FastAPI 서버 포트 |
| `MODEL_NAME` | gpt-4o-mini | 사용할 OpenAI 모델 |
| `CHUNK_SIZE` | 800 | 문서 청킹 크기 |
| `CHUNK_OVERLAP` | 200 | 청크 겹침 크기 |
| `TEMPERATURE` | 0.2 | AI 응답 온도 |

전체 환경 변수 목록은 [.env.sample](./server/.env.sample)을 참조하세요.

## 🌐 웹 인터페이스 (Next.js)

프론트엔드 웹 애플리케이션은 별도로 실행 가능합니다:

```bash
cd web
npm install
npm run dev
```

- **개발 서버**: http://localhost:3000
- **프로덕션 빌드**: `npm run build && npm start`

## 📚 API 사용 예제

### RAG 채팅 API

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "국내주식 양도소득세는 어떻게 되나요?",
    "session_id": "user123"
  }'
```

**응답 예시**:
```json
{
  "success": true,
  "data": {
    "message": "국내주식 양도소득세는 2024년부터 다음과 같이 적용됩니다...",
    "sources": [
      {
        "content": "관련 세법 조항...",
        "metadata": {
          "source": "소득세법.pdf",
          "page": 15
        }
      }
    ],
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### 문서 업로드 API

```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@tax_document.pdf"
```

### WebSocket 채팅 연결

JavaScript에서 WebSocket을 통한 실시간 채팅:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat');

// 연결 성공
ws.onopen = function(event) {
    console.log('WebSocket 연결됨');
};

// 메시지 전송
ws.send(JSON.stringify({
    message: "국내주식 양도소득세는 어떻게 되나요?"
}));

// 응답 수신
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'chunk') {
        console.log('청크:', data.content);
    } else if (data.type === 'done') {
        console.log('응답 완료');
    }
};
```

## 🌐 CORS 설정 및 외부 프론트엔드 연동

server 모듈은 외부 프론트엔드 애플리케이션과의 연동을 위해 CORS가 설정되어 있습니다.

### 현재 CORS 설정

```python
# server/modules/fastapi_app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Next.js에서 API 호출 예시

```javascript
// Next.js API 호출 예시
const response = await fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        message: "세금 관련 질문",
        session_id: "user123"
    })
});

const data = await response.json();
console.log(data);
```

### 프로덕션 환경 CORS 설정

프로덕션 환경에서는 보안을 위해 특정 도메인만 허용하도록 설정하세요:

```python
# 프로덕션용 CORS 설정 예시
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com",
        "https://app.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## 🔧 개발 모드 vs 배포 모드

### 개발 모드 특징
- 자동 리로드 (uvicorn --reload)
- 상세한 로그 출력
- 개발용 CORS 설정 (모든 origin 허용)

### 배포 모드 특징
- 프로덕션 최적화
- 로그 파일 저장
- 보안 강화된 CORS (특정 도메인만 허용)
- 성능 모니터링 활성화

배포 모드로 실행:
```bash
cd server
python main.py --production
```

## 🚀 서버만 배포하기

server 모듈은 완전히 독립적으로 실행 가능합니다:

1. **server 디렉토리만 복사**
2. **의존성 설치**: `python setup.py`
3. **환경변수 설정**: `.env` 파일 생성
4. **서버 실행**: `python main.py`

자세한 배포 가이드는 [docs/server_migration.md](./docs/server_migration.md)를 참조하세요.

## 🏗️ 아키텍처

### 개발 환경 구조
```
rag_lab/ (개발)
├── server/          # FastAPI 백엔드 서버
├── web/             # Next.js 개발 서버 (별도 실행)
└── 공유 리소스
```

### 배포 환경 구조
```
production/
├── server/          # FastAPI 전용 (포트 8000)
└── web/             # Next.js 빌드 (포트 3000, 별도 배포)
```

## 🧪 테스트

프로젝트는 포괄적인 테스트 스위트를 제공합니다.

### 테스트 실행

```bash
# 모든 테스트 실행 (e2e 제외)
python run_tests.py

# 특정 테스트 카테고리
python run_tests.py --unit          # 단위 테스트
python run_tests.py --integration   # 통합 테스트  
python run_tests.py --e2e           # E2E 테스트
python run_tests.py --all           # 모든 테스트

# 커버리지 리포트와 함께
python run_tests.py --coverage

# 플랫폼별 스크립트
./run_tests.sh      # Unix/Linux/Mac
run_tests.bat       # Windows
```

### 테스트 구조

```
tests/
├── __init__.py          # 테스트 모듈 초기화 및 경로 설정
├── conftest.py          # 공유 픽스처 및 설정
├── unit/               # 단위 테스트
│   ├── test_document_service.py
│   ├── test_config_endpoint.py
│   ├── test_langchain_trace.py
│   └── test_langsmith_project.py
├── integration/        # API 통합 테스트
│   ├── test_api_endpoints.py
│   ├── test_api_quick.py
│   ├── test_sync_add_apis.py
│   ├── test_empty_vectordb.py
│   └── test_rag_websocket.py
└── e2e/               # 전체 워크플로우 테스트
    ├── test_rag_pipeline.py
    └── test_with_documents.py
```

자세한 테스트 가이드는 [docs/TESTING.md](./docs/TESTING.md)를 참조하세요.

## 🔍 디버깅 및 로그

로그 파일 위치:
- **서버 로그**: `./server/logs/server.log`
- **ChromaDB 로그**: ChromaDB 내부 로그
- **LangSmith 추적**: https://smith.langchain.com 에서 확인

## 🤝 팀원 온보딩

새로운 팀원을 위한 빠른 시작:

1. **저장소 클론**: `git clone [repo_url]`
2. **server 설정**: `cd server && python setup.py`
3. **API 키 설정**: `.env` 파일에 OpenAI API 키 추가
4. **서버 실행**: `python main.py`
5. **브라우저 접속**: http://localhost:8000/docs

## 📖 추가 문서

- [서버 마이그레이션 가이드](./docs/server_migration.md)
- [API 상세 문서](./server/README.md)
- [환경 변수 설정](./server/.env.sample)

## 🔗 관련 프로젝트

이 프로젝트는 기존 Node.js 기반 `stock-d-tax` 프로젝트의 AI 챗봇 기능을 Python/FastAPI로 재구현한 것입니다. 