# FastAPI Chatbot Server

이 FastAPI 서버는 주식 투자 세금 관련 챗봇 API를 제공합니다.

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
`.env` 파일을 생성하고 OpenAI API 키를 설정하세요:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. 서버 실행
```bash
python main.py
```

서버는 `http://localhost:8000`에서 실행됩니다.

## API 엔드포인트

### 챗봇 메시지 처리
- **URL**: `POST /api/chatbot/message`
- **Request Body**:
```json
{
  "message": "국내주식 양도소득세는 어떻게 되나요?"
}
```
- **Response**:
```json
{
  "success": true,
  "data": {
    "message": "국내주식 양도소득세는 분리과세로 15.4%입니다...",
    "timestamp": "2024-01-01T12:00:00"
  }
}
```

## 기능

- OpenAI GPT-3.5-turbo 모델 사용
- RAG (Retrieval-Augmented Generation) 기반 세금 지식 베이스
- 한국어 주식 투자 세금 전문 챗봇
- 실시간 응답 생성

## 기존 Node.js 서버에서 마이그레이션

이 FastAPI 서버는 기존 Node.js 서버의 챗봇 기능을 Python으로 포팅한 것입니다:
- `stock-d-tax/apps/api/routes/chatbot.js` → `ai/main.py`의 `/api/chatbot/message` 엔드포인트
- `stock-d-tax/apps/api/services/openaiService.js` → `ai/main.py`의 `generate_response()` 함수 