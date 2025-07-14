# Stock D-TAX

주식 투자 세금 계산 및 챗봇 서비스

## 프로젝트 구조

```
stock-d-tax/
├── apps/
│   ├── web/              # 프론트엔드 (Next.js)
│   │   ├── components/   # 공통 UI 컴포넌트
│   │   ├── pages/        # 라우트별 페이지
│   │   ├── styles/       # 스타일 파일
│   │   └── package.json
│   └── api/              # 백엔드 (Node.js/Express)
│       ├── routes/       # API 라우트
│       ├── controllers/  # 비즈니스 로직
│       ├── services/     # 외부 API/챗봇 연동
│       └── package.json
├── database/             # DB 마이그레이션/시드
├── docker/               # Docker 관련 파일
└── README.md
```

## 기능

- 📊 **포트폴리오 차트**: 실현/미실현 이익 시각화
- 💰 **세금 계산**: 국내/해외주식, 배당소득세 계산
- 🤖 **AI 챗봇**: OpenAI API + RAG 기반 세금 상담
- 📈 **실시간 데이터**: WebSocket을 통한 주가 업데이트

## 설치 및 실행

### 1. 환경 설정

백엔드 API 키 설정:
```bash
cd apps/api
cp config.env .env
```

`.env` 파일에 OpenAI API 키를 설정:
```
OPENAI_API_KEY=your_openai_api_key_here
```

### 2. 의존성 설치

```bash
# 프론트엔드
cd apps/web
npm install

# 백엔드
cd ../api
npm install
```

### 3. 서버 실행

**백엔드 서버 (포트 4000):**
```bash
cd apps/api
npm run dev
```

**프론트엔드 서버 (포트 3000):**
```bash
cd apps/web
npm run dev
```

### 4. 접속

- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:4000

## API 엔드포인트

### 세금 계산
- `POST /api/tax/calculate` - 세금 계산
- `GET /api/tax/info` - 세금 정보 조회

### 챗봇
- `POST /api/chatbot/message` - 챗봇 메시지 처리

## 기술 스택

### 프론트엔드
- Next.js
- React
- Chart.js
- Axios

### 백엔드
- Node.js
- Express
- Socket.io
- OpenAI API

## 개발 가이드

### 챗봇 RAG 확장
`apps/api/services/openaiService.js`의 `taxKnowledgeBase` 배열에 새로운 세금 지식을 추가할 수 있습니다.

### 차트 데이터 연동
실제 주가 데이터를 연동하려면 `apps/api/services/stockApi.js`를 수정하세요.

## 라이선스

ISC 