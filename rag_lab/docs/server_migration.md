# Server 모듈 마이그레이션 가이드

이 문서는 RAG Lab의 server 모듈을 독립적으로 배포하고 사용하는 방법을 설명합니다.

## 📋 개요

server 모듈은 완전히 독립적으로 실행 가능한 FastAPI 기반의 RAG 시스템입니다. API 서버로 동작하며, 외부 프론트엔드 애플리케이션(Next.js, React 등)에서 HTTP API 및 WebSocket을 통해 접근할 수 있습니다.

## 🏗️ 아키텍처 비교

### 개발 환경 (통합)
```
rag_lab/
├── server/              # FastAPI 백엔드 (독립 실행)
│   ├── main.py          # FastAPI 서버 실행
│   ├── modules/         # 모든 기능 모듈
│   └── config/          # 설정 파일
├── web/                 # Next.js 프론트엔드 (별도 실행)
├── api/                 # 레거시 API 모듈
└── auto_rag/            # 레거시 RAG 시스템
```

### 배포 환경 (서버만)
```
production-server/
├── server/              # 독립 실행되는 API 서버
│   ├── main.py          # FastAPI 서버 (포트 8000)
│   ├── modules/         # 모든 RAG 기능
│   ├── config/          # 환경별 설정
│   ├── chroma_db/       # 벡터 데이터베이스
│   ├── raw_data/        # 원본 문서
│   ├── logs/            # 로그 파일
│   └── .env             # 환경 변수
└── (웹 프론트엔드는 별도 배포)
```

## 🚀 복사 및 배포 전략

### 1. 최소 복사 전략 (권장)

서버 기능만 필요한 경우:

```bash
# 1. server 디렉토리만 복사
cp -r rag_lab/server production-server/

# 2. 대상 서버에서 설정
cd production-server/server
python setup.py

# 3. 환경 변수 설정
cp .env.example .env
# .env 파일 편집하여 API 키 설정

# 4. 실행
python main.py
```

### 2. 전체 복사 후 정리 전략

전체 프로젝트를 복사한 후 필요없는 부분 제거:

```bash
# 1. 전체 복사
cp -r rag_lab production-rag-lab

# 2. 불필요한 디렉토리 제거
cd production-rag-lab
rm -rf web/              # Next.js 프론트엔드 제거
rm -rf api/              # 레거시 API 제거  
rm -rf auto_rag/         # 레거시 RAG 제거
rm -rf Achive/           # 아카이브 제거

# 3. server로 이동하여 설정
cd server
python setup.py
```

## 🔧 Import 경로 변경 가이드

server 모듈은 이미 독립적인 import 구조를 가지고 있어 추가 변경이 불필요합니다.

### 현재 Import 구조 (변경 불필요)

```python
# server/main.py
from modules.fastapi_app import create_app
from config.settings import settings, setup_environment

# server/modules/fastapi_app.py  
from .api.routers import rag, documents
from .auto_rag.mod.rag_system_manager import RAGSystemManager

# server/modules/api/services/rag_service.py
from ...auto_rag.mod.rag_system_manager import RAGSystemManager
from ...config.settings import settings
```

### 검증 방법

Import 경로가 올바른지 확인:

```bash
cd server
python -c "from modules.fastapi_app import create_app; print('✅ Import 성공')"
python -c "from config.settings import settings; print('✅ 설정 로드 성공')"
```

## 🌐 실행 방법 상세

### 1. 기본 실행

```bash
cd server
python main.py
```

실행되는 서비스:
- **FastAPI 서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 2. 프로덕션 모드 실행

```bash
cd server
python main.py --production
```

프로덕션 모드 특징:
- uvicorn 리로드 비활성화
- 로그 파일 저장 활성화
- 성능 모니터링 강화
- 보안 설정 강화

### 3. 개별 구성 요소 실행

FastAPI만 실행:
```bash
cd server
uvicorn modules.fastapi_app:app --host 0.0.0.0 --port 8000
```

### 4. 스크립트를 통한 실행

```bash
# Windows
run.bat

# Linux/Mac
./run.sh

# Python 래퍼
python run.py
```

## 🔧 환경 변수 설정

### 필수 환경 변수

```env
# API 키 (필수)
OPENAI_API_KEY=sk-proj-your-openai-api-key-here

# 서버 포트 (선택적)
SERVER_PORT=8000
DEBUG=false
```

### 선택적 환경 변수

```env
# LangSmith 추적 (선택적)
LANGSMITH_API_KEY=lsv2_pt_your-langsmith-key-here
LANGSMITH_PROJECT=rag_lab_production
LANGSMITH_TRACING=true

# RAG 시스템 설정
MODEL_NAME=gpt-4o-mini
CHUNK_SIZE=800
CHUNK_OVERLAP=200
TEMPERATURE=0.2

# 파일 경로
CHROMA_PERSIST_DIRECTORY=./chroma_db
RAW_DATA_DIRECTORY=./raw_data
LOG_FILE=./logs/server.log

# 로깅 설정  
LOG_LEVEL=INFO
```

### 환경별 설정 예시

#### 개발 환경 (.env.development)
```env
DEBUG=true
LOG_LEVEL=DEBUG
UVICORN_RELOAD=true
LANGSMITH_TRACING=true
```

#### 스테이징 환경 (.env.staging)
```env
DEBUG=false
LOG_LEVEL=INFO
UVICORN_RELOAD=false
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=rag_lab_staging
```

#### 프로덕션 환경 (.env.production)
```env
DEBUG=false
LOG_LEVEL=WARNING
UVICORN_RELOAD=false
LANGSMITH_TRACING=false
```

## 📁 디렉토리 구조 상세

### 배포 후 server 디렉토리 구조

```
server/
├── main.py                 # 🚀 메인 실행 파일
├── run.py                  # 🎛️ 실행 래퍼
├── run.bat                 # 🪟 Windows 실행 스크립트  
├── run.sh                  # 🐧 Linux/Mac 실행 스크립트
├── setup.py                # ⚙️ 자동 설정 스크립트
├── requirements.txt        # 📦 Python 의존성
├── requirements-dev.txt    # 🔧 개발용 의존성
├── .env                    # 🔐 환경 변수 (생성 필요)
├── .env.example           # 📝 환경 변수 템플릿
├── README.md               # 📚 서버 전용 문서
│
├── config/                 # ⚙️ 설정
│   ├── __init__.py
│   └── settings.py         # 🔧 앱 설정
│
├── modules/                # 📦 핵심 모듈
│   ├── __init__.py
│   ├── fastapi_app.py      # 🚀 FastAPI 앱 팩토리
│   ├── bot_response.py     # 🤖 응답 생성 (레거시)
│   │
│   ├── api/                # 🌐 API 라우터
│   │   ├── __init__.py
│   │   ├── models/         # 📊 데이터 모델
│   │   ├── routers/        # 🛣️ API 라우터
│   │   └── services/       # 🔧 비즈니스 로직
│   │
│   └── auto_rag/           # 🤖 RAG 시스템
│       ├── mod/            # 🧩 RAG 모듈들
│       ├── chroma_db/      # 💾 벡터 데이터베이스
│       ├── raw_data/       # 📄 원본 문서
│       └── requirements.txt # 📦 RAG 전용 의존성
│
├── logs/                   # 📝 로그 파일 (자동 생성)
├── chroma_db/             # 💾 ChromaDB 데이터 (자동 생성)
├── raw_data/              # 📄 업로드된 문서 (자동 생성)
├── tests/                 # 🧪 테스트 (선택적)
└── venv/                  # 🐍 가상환경 (자동 생성)
```

## 🔄 업그레이드 및 유지보수

### 의존성 업데이트

```bash
# 의존성 업데이트 확인
pip list --outdated

# 업데이트 실행
pip install --upgrade -r requirements.txt

# 새로운 requirements.txt 생성
pip freeze > requirements.txt
```

### 데이터베이스 백업

ChromaDB 백업:
```bash
# 백업
cp -r chroma_db chroma_db_backup_$(date +%Y%m%d)

# 복원
cp -r chroma_db_backup_20240120 chroma_db
```

### 로그 관리

```bash
# 로그 크기 확인
du -sh logs/

# 로그 순환 (7일 이상 된 로그 삭제)
find logs/ -name "*.log" -mtime +7 -delete

# 실시간 로그 모니터링
tail -f logs/server.log
```

## 🚨 문제 해결

### 자주 발생하는 문제

#### 1. 포트 충돌
```bash
# 포트 사용 확인
netstat -ano | findstr :8000
netstat -ano | findstr :8501

# 환경 변수로 포트 변경
export SERVER_PORT=8080
export WEB_PORT=8502
```

#### 2. 의존성 충돌
```bash
# 가상환경 재생성
rm -rf venv
python setup.py
```

#### 3. ChromaDB 손상
```bash
# ChromaDB 초기화
rm -rf chroma_db
# 서버 재시작하면 자동으로 재생성됨
```

#### 4. 환경 변수 로드 실패
```bash
# .env 파일 확인
cat .env

# 권한 확인
chmod 600 .env

# 수동 환경 변수 설정
export OPENAI_API_KEY=sk-proj-your-key-here
```

### 디버그 모드 실행

상세한 디버그 정보와 함께 실행:
```bash
# 디버그 환경 변수 설정
export DEBUG=true
export LOG_LEVEL=DEBUG

# 실행
python main.py
```

### 헬스 체크

서버 상태 확인:
```bash
# API 헬스 체크
curl http://localhost:8000/health

# 전체 기능 테스트
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "테스트 메시지"}'
```

## 🌐 외부 프론트엔드 연동 및 CORS 설정

server 모듈은 외부 프론트엔드 애플리케이션과의 연동을 위해 CORS가 기본 설정되어 있습니다.

### 현재 CORS 설정

```python
# server/modules/fastapi_app.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 origin 허용 (개발용)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Next.js 프론트엔드에서 API 호출

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

### WebSocket 연결 예시

```javascript
// WebSocket 실시간 채팅
const ws = new WebSocket('ws://localhost:8000/ws/chat');

ws.onopen = function(event) {
    console.log('WebSocket 연결됨');
    
    // 메시지 전송
    ws.send(JSON.stringify({
        message: "실시간 질문입니다"
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    
    if (data.type === 'chunk') {
        // 스트리밍 데이터 처리
        console.log('청크:', data.content);
    } else if (data.type === 'done') {
        console.log('응답 완료');
    }
};
```

### React 프론트엔드 연동 예시

```jsx
// React Hook 예시
import { useState, useEffect } from 'react';

function useChatAPI() {
    const [messages, setMessages] = useState([]);
    
    const sendMessage = async (message) => {
        try {
            const response = await fetch('http://localhost:8000/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: 'user123'
                })
            });
            
            const data = await response.json();
            setMessages(prev => [...prev, data]);
            
        } catch (error) {
            console.error('API 호출 오류:', error);
        }
    };
    
    return { messages, sendMessage };
}
```

### 프로덕션 환경 CORS 설정

프로덕션 환경에서는 보안을 위해 특정 도메인만 허용하도록 수정하세요:

```python
# 프로덕션용 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com", 
        "https://app.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
```

### 환경별 CORS 설정

환경 변수를 활용한 동적 CORS 설정:

```python
import os
from typing import List

# 환경별 허용 도메인 설정
def get_allowed_origins() -> List[str]:
    if os.getenv("DEBUG", "false").lower() == "true":
        # 개발 환경: 모든 origin 허용
        return ["*"]
    else:
        # 프로덕션 환경: 지정된 도메인만 허용
        origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
        return [origin.strip() for origin in origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

환경 변수 설정:
```env
# 개발 환경
DEBUG=true

# 프로덕션 환경  
DEBUG=false
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

## 📊 모니터링 및 성능

### LangSmith 추적

LangSmith를 통한 AI 호출 추적:
1. LANGSMITH_API_KEY 설정
2. https://smith.langchain.com 에서 추적 데이터 확인
3. 성능 메트릭 및 오류 분석

### 로그 분석

중요한 로그 패턴:
```bash
# 오류 로그 확인
grep ERROR logs/server.log

# 성능 지연 확인  
grep "slow" logs/server.log

# API 사용량 확인
grep "POST /api/" logs/server.log | wc -l
```

### 리소스 사용량

```bash
# 메모리 사용량
ps aux | grep python

# 디스크 사용량
du -sh chroma_db/ raw_data/ logs/

# 네트워크 연결 상태
netstat -an | grep :8000
```

## 🔒 보안 고려사항

### API 키 보안
- `.env` 파일을 버전 관리에 포함하지 않음
- 파일 권한을 600으로 설정 (`chmod 600 .env`)
- 정기적인 API 키 순환

### 네트워크 보안
- 필요한 경우에만 외부 접근 허용
- HTTPS 프록시 사용 권장
- 방화벽 설정으로 포트 제한

### 데이터 보안
- 업로드된 문서의 민감 정보 확인
- ChromaDB 데이터 암호화 고려
- 정기적인 데이터 백업

## 📈 확장성 고려사항

### 수평 확장
- 로드 밸런서를 통한 여러 인스턴스 운영
- ChromaDB를 별도 서버로 분리
- Redis 캐시 추가 고려

### 수직 확장  
- 메모리 증설 (ChromaDB 성능 향상)
- GPU 사용 (임베딩 속도 향상)
- SSD 스토리지 (I/O 성능 향상)

이 가이드를 통해 server 모듈을 안전하고 효율적으로 배포할 수 있습니다.