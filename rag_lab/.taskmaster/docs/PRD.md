# RAG Lab - Product Requirements Document (PRD)

## 1. 개요

### 1.1 프로젝트 목표
RAG Lab은 세법 및 세무 관련 문서를 기반으로 한 검색 증강 생성(Retrieval-Augmented Generation) 시스템입니다. 사용자는 복잡한 세법 질문에 대해 정확하고 근거 있는 답변을 실시간으로 받을 수 있으며, 관련 세금 계산까지 수행할 수 있습니다.

### 1.2 핵심 가치 제안
- **정확성**: 세법 문서 기반의 신뢰할 수 있는 답변 제공
- **투명성**: 답변 근거가 되는 문서 출처 명시
- **실시간성**: SSE 스트리밍을 통한 즉시 응답
- **확장성**: 모듈화된 아키텍처로 새로운 기능 추가 용이
- **관측성**: LangSmith 및 OpenTelemetry 기반 모니터링

## 2. 프로젝트 구조 재설계

### 2.1 새로운 디렉터리 구조
```
rag_lab/ (프로젝트 루트)
├── server/                      # 백엔드 서버 코드
│   ├── raw_data/               # 업로드된 원본 문서 저장
│   ├── chroma_db/              # 벡터 데이터베이스 파일
│   ├── api/                    # FastAPI 라우트, 서비스 계층
│   └── modules/                # RAG 코어 모듈 (기존 auto_rag)
├── main.py                     # 서버 전용 실행 파일
├── run.py                      # 서버 실행 스크립트
└── .env                        # 환경 변수 설정
```

**주요 아키텍처 변경사항:**
- 웹(Next.js) 프론트엔드는 별도 저장소에서 독립적으로 실행
- main.py와 run.py는 FastAPI 서버만 담당
- 프론트엔드는 API 호출 및 WebSocket으로만 서버와 통신

### 2.2 마이그레이션 전략
- 기존 `auto_rag` 폴더를 `server/modules`로 이동
- 역방향 호환성을 위한 shim 코드 구현
- import 경로 일괄 변경 자동화
- PYTHONPATH 설정 표준화

## 3. 백엔드 API 리팩토링

### 3.1 문서 관리 API 개선

#### 3.1.1 새로운 엔드포인트
1. **POST /api/documents/{doc_id}/config**
   - 문서별 청킹 설정 저장
   - Body: `{"chunk_size": int, "chunk_overlap": int}`
   - 유효성 검사: chunk_size > 0, chunk_overlap < chunk_size
   - 오타 허용: "chunk_overlab" → "chunk_overlap" 자동 매핑

2. **POST /api/documents/upload-file** (수정)
   - chunk 파라미터 제거, file만 업로드
   - raw_data 폴더 자동 생성
   - PDF, TXT 파일만 지원
   - doc_id 자동 생성 및 Location 헤더 반환

3. **DELETE /api/documents/{doc_id}** (수정)
   - raw_data 폴더 내에서만 삭제 허용
   - 경로 탈출 방지 보안 강화
   - 삭제 가능한 파일 목록 제공

4. **GET /api/documents/sync** (수정)
   - POST → GET 방식으로 변경
   - 파라미터: chunk_size, chunk_overlap, force
   - config.json 기반 설정 fallback

#### 3.1.2 제거될 엔드포인트
- `/api/rag/chat` (WebSocket으로 대체)
- `/api/rag/generate-questions`
- `/api/rag/evaluate`

### 3.2 보안 및 검증 강화
- 경로 탐색 공격 방지
- MIME 타입 및 확장자 이중 검증
- 입력 값 범위 및 타입 검증
- 일관된 에러 응답 포맷

## 4. 서버 전용 실행 시스템

### 4.1 실행 파일 구조
- **main.py**: 서버 진입점
- **run.py**: FastAPI 서버 실행 로직

### 4.2 실행 순서
1. FastAPI 서버 (uvicorn) 시작
2. `/health` 엔드포인트 확인 (최대 30초 대기)
3. 서버 상태 모니터링 및 자동 복구

### 4.3 프로세스 관리
- SIGINT/SIGTERM 신호 처리
- 안전한 종료 (terminate → kill)
- Windows 호환성 (taskkill 지원)
- 서버 전용 로그 출력 및 파일 저장

### 4.4 설정 가능한 실행 명령
```bash
# 환경 변수로 서버 실행 명령 커스터마이징
SERVER_CMD="uvicorn server.api.main:app --host 0.0.0.0 --port 8000"
```

## 5. 프론트엔드 (별도 저장소)

### 5.1 독립적인 Next.js 애플리케이션
- 별도 저장소에서 독립적으로 개발 및 배포
- 환경 변수를 통한 백엔드 서버 연결
- 순수 클라이언트 애플리케이션 (API 호출 및 WebSocket 통신만)

### 5.2 새로운 페이지
1. **설정 페이지 (/settings)**
   - RAG 시스템 파라미터 설정 (temperature, top_k, 모델명)
   - 문서별 청킹 설정
   - WebSocket 연결 상태 표시

2. **테스트 페이지 (/playground)**
   - RAG 쿼리 실시간 테스트
   - 질문 입력 → 응답 및 citations 출력
   - WebSocket 메시지 로그

### 5.3 WebSocket 연결 관리
- 주기적 ping (5초 간격) 상태 확인
- 자동 재연결 메커니즘
- 연결 상태 시각적 표시 (red/green 배지)

### 5.4 API 연결 모듈
- axios 기반 중앙화된 API 클라이언트
- 환경 변수 기반 엔드포인트 설정 (NEXT_PUBLIC_API_URL)
- 표준화된 에러 처리

## 6. 핵심 기능 현황

### 6.1 완료된 기능 ✅
| ID | 기능 | 설명 | 구현 방식 |
|----|------|------|-----------|
| BE-1 | REST & SSE API | POST /chat, 서버 전송 스트리밍 | FastAPI async 엔드포인트 + Uvicorn |
| BE-3 | 지식 검색 | 세법 문서 벡터 검색 | OpenAI Embedding-3-Large → Chroma |
| BE-4 | 답변 생성 | GPT 인용과 함께 최종 응답 생성 | LangChain StuffDocumentsChain |
| BE-6 | RAG 평가 | RAGAS 배치 평가 | 일일 크론 & GitHub Actions |
| BE-7 | 관측 가능성 | LangSmith 추적, 로깅 | LangSmith 추적 미들웨어 |

### 6.2 진행 중인 기능 🚧
| ID | 기능 | 상태 | 목표 |
|----|------|------|------|
| ST-1 | 프로젝트 구조 재설계 | Task 11 | server/ 폴더 구조 완성 |
| API-1 | 문서 관리 API 리팩토링 | Task 12, 14 | RESTful API 완성 |
| EX-1 | 서버 전용 실행 시스템 | Task 13, 15 | main.py 서버 실행 파일 |
| FE-1 | 독립 프론트엔드 개선 | Task 16 | 설정/테스트 페이지 (별도 저장소) |

### 6.3 지연된 기능 ⏸️
| ID | 기능 | 이유 | 계획 |
|----|------|------|------|
| BE-2 | 세션 메모리 | 구조 재설계 우선 | Phase 2 |
| BE-5 | 세금 계산기 도구 | 구조 재설계 우선 | Phase 2 |
| API-2 | 대화 히스토리 | Redis 구현 대기 | Phase 2 |

## 7. 기술 스택

### 7.1 백엔드
- **Framework**: FastAPI
- **Database**: ChromaDB (벡터), Redis (세션)
- **LLM**: OpenAI GPT models
- **Embedding**: text-embedding-3-large
- **Monitoring**: LangSmith, OpenTelemetry
- **Evaluation**: RAGAS

### 7.2 프론트엔드 (별도 저장소)
- **Framework**: Next.js
- **UI Library**: Chakra UI (최소 스타일링)
- **HTTP Client**: axios
- **State Management**: React hooks

### 7.3 인프라
- **Container**: Docker
- **Process Management**: uvicorn (서버 전용)
- **Logging**: Python logging, 파일 순환

### 7.4 구성 요소 스택
| 계층 | 기술 | 비고 |
|-------|------------|-------|
| 웹 서버 | FastAPI 0.111 / Uvicorn | async, SSL 업스트림 종료 |
| 메모리 저장소 | Redis 7 | 1 Gi RAM; TTL 30분; 클러스터 지원 |
| 벡터 DB | Chroma 0.5 영구 클라이언트 | DuckDB+Parquet; 야간 백업 |
| 임베딩 | `text-embedding-3-large` | 3072차원; 청크 크기 512 토큰 |
| LLM | GPT-4o-mini (개발), GPT-4.1 (운영) | temperature 0.2 |
| 오케스트레이션 | LangChain 0.2 | RunnableWithMessageHistory |
| 관측성 | LangSmith 0.3 + OpenTelemetry | 분산 추적 |
| 평가 | RAGAS 0.2 | 별도 워커 포드에서 실행 |

## 8. API 설계

### 8.1 기존 API (운영 중)
#### 채팅
```
POST /chat
{
  "session_id": "uuid", 
  "message": "string"
}
```
스트리밍 응답 (SSE): 점진적 JSON 청크

#### 평가
```
POST /evaluate
{
  "dataset_id": "tax_eval_v1"
}
```
RAGAS 작업 시작; 작업 ID로 응답

### 8.2 새로운 문서 관리 API
#### 설정 저장
```
POST /api/documents/{doc_id}/config
{
  "chunk_size": 800,
  "chunk_overlap": 200
}
```

#### 파일 업로드
```
POST /api/documents/upload-file
Content-Type: multipart/form-data
file: <File>
```

#### 문서 삭제
```
DELETE /api/documents/{doc_id}
```

#### 동기화
```
GET /api/documents/sync?chunk_size=800&chunk_overlap=200&force=true
```

### 8.3 상태 확인
```
GET /health
GET /health/detailed
```

## 9. 데이터 모델

### 9.1 API 모델
```python
class ChatRequest(BaseModel):
    session_id: UUID
    message: str

class DocumentConfig(BaseModel):
    chunk_size: int = Field(gt=0, le=2000)
    chunk_overlap: int = Field(ge=0)
    
    @validator('chunk_overlap')
    def overlap_less_than_size(cls, v, values):
        if 'chunk_size' in values and v >= values['chunk_size']:
            raise ValueError('chunk_overlap must be less than chunk_size')
        return v

class UploadResponse(BaseModel):
    doc_id: str
    file_name: str
    message: str

class SyncResponse(BaseModel):
    processed_docs: int
    total_chunks: int
    used_chunk_size: int
    used_chunk_overlap: int
```

### 9.2 저장 스키마
**Redis 세션:**
```
key: session:{uuid}
value: List[HistoryItem]  (LPUSH / LTRIM)
```

**Chroma 컬렉션:**
```
name: "tax_docs"
metadata: { source: "url", title: str, doc_id: str }
```

**파일 시스템:**
```
server/raw_data/{doc_id}/
├── original_file.pdf
└── config.json
```

## 10. 개발 로드맵

### 10.1 Phase 1: 구조 재설계 (현재)
| 단계 | 구현 사항 | 상태 |
|-------|------------|------|
| **Task 11** | 프로젝트 디렉터리 재설계 | 🚧 진행중 |
| **Task 12** | 문서 관리 API 기초 | 🚧 진행중 |
| **Task 13** | 통합 실행 파일 | 🚧 진행중 |
| **Task 14** | API 엔드포인트 개선 | 🚧 진행중 |
| **Task 15** | 실행 시스템 완성 | 🚧 진행중 |
| **Task 16** | 프론트엔드 최소 개선 | 🚧 진행중 |

### 10.2 Phase 2: 기능 확장
| 단계 | 구현 사항 | 상태 |
|-------|------------|------|
| **Task 2** | Redis 세션 메모리 | ⏸️ 지연 |
| **Task 6** | 세금 계산기 통합 | ⏸️ 지연 |
| **Task 7** | 대화 히스토리 엔드포인트 | ⏸️ 지연 |
| **Task 10** | OpenAPI 문서 및 테스트 | ⏸️ 지연 |

### 10.3 Phase 3: 고도화
- 다중 모델 지원
- BM25 하이브리드 검색  
- 실시간 문서 업데이트
- 고급 평가 메트릭

## 11. 품질 보증

### 11.1 테스트 전략
- **단위 테스트**: pytest 기반 모든 핵심 모듈
- **통합 테스트**: FastAPI TestClient
- **E2E 테스트**: 실제 서버/웹 기동 검증
- **성능 테스트**: 응답 시간 및 처리량 측정

### 11.2 코드 품질
- **정적 분석**: ruff, mypy
- **타입 힌팅**: 모든 함수 타입 어노테이션
- **문서화**: OpenAPI 자동 생성, docstring
- **CI/CD**: GitHub Actions 자동화

### 11.3 보안
- 경로 탐색 공격 방지
- 입력 검증 및 살균
- CORS 및 보안 헤더 설정
- 민감 정보 로깅 방지

## 12. 성능 및 확장성

### 12.1 성능 목표
- API 응답 시간: < 500ms (단순 쿼리)
- RAG 응답 시간: < 5초 (복잡한 질문)
- 동시 사용자: 100명
- 문서 처리량: 1000개/시간

### 12.2 모니터링
- **메트릭**: LangSmith 대시보드
- **로깅**: 구조화된 JSON 로그
- **추적**: 분산 트레이싱 (OpenTelemetry)
- **알림**: 에러율 및 응답 시간 임계값

## 13. 배포 및 운영

### 13.1 배포 방식
- **개발**: `python main.py --debug` (서버만)
- **스테이징**: Docker Compose
- **프로덕션**: Kubernetes 또는 Docker Swarm

### 13.2 환경 설정
```bash
# 서버 필수 환경 변수
OPENAI_API_KEY=sk-...
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=rag_lab_project

# 서버 선택적 환경 변수
SERVER_PORT=8000
CHUNK_SIZE=800
CHUNK_OVERLAP=200

# 프론트엔드 환경 변수 (별도 저장소)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 13.3 데이터 관리
- **백업**: ChromaDB 정기 백업
- **마이그레이션**: 스키마 변경 자동화
- **정리**: 임시 파일 및 로그 순환

## 14. 위험 요소 및 완화 방안

| 위험 | 완화 방안 |
|------|-----------|
| OpenAI 속도 제한 | 지수 백오프, 임베딩 Redis 캐시 |
| 벡터 DB 손상 | 야간 S3 내보내기; WAL 재생 스크립트 |
| 메모리 과부하 | 슬라이딩 윈도우 k = 6 + TTL 제거 |
| 메트릭 드리프트 | RAGAS CI 게이트: 충실성 < 0.6이면 병합 차단 |
| 프로젝트 구조 변경 | 역방향 호환성 shim, 점진적 마이그레이션 |
| 서버 프로세스 관리 | 신호 처리, 안전한 종료, 상태 모니터링 (서버 전용) |
| 프론트엔드 분리 | 독립적인 버전 관리, API 계약 관리, CORS 설정 |

## 15. 성공 지표

### 15.1 기술적 지표
- 시스템 가용률 > 99%
- 평균 응답 시간 < 3초
- 에러율 < 1%
- 테스트 커버리지 > 90%

### 15.2 사용성 지표
- 사용자 만족도 점수
- 답변 정확도 (전문가 평가)
- 기능 사용률
- 문서 업로드 성공률

## 16. 참고 자료

### 16.1 기술 문서
- FastAPI + LangChain 통합 가이드
- Redis 세션 관리 예시
- Chroma 운영 쿡북
- LangSmith 추적 문서
- RAGAS 평가 패턴

### 16.2 아키텍처 결정 기록
- 프로젝트 구조 재설계 결정
- API 엔드포인트 리팩토링 방향
- 서버 전용 실행 시스템 설계
- 프론트엔드 분리 및 독립화 전략

---

*이 PRD는 2025년 7월 기준으로 작성되었으며, 프로젝트 진행에 따라 지속적으로 업데이트됩니다.*

**Last Updated**: 2025-07-19  
**Version**: 2.0  
**Next Review**: Task 11-16 완료 후