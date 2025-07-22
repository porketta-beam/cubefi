# RAG Lab 아키텍처 다이어그램

이 문서는 RAG Lab 프로젝트의 개발 환경과 배포 환경 아키텍처를 PlantUML 다이어그램으로 설명합니다.

## 🏗️ 개발 환경 구조

### 전체 시스템 아키텍처

```plantuml
@startuml development_architecture
!define RECTANGLE_COLOR #E3F2FD
!define API_COLOR #FFE0B2  
!define WEB_COLOR #E8F5E8
!define DB_COLOR #FFEBEE
!define LEGACY_COLOR #F3E5F5

title RAG Lab 개발 환경 아키텍처

package "rag_lab (개발 환경)" {
  
  package "server/" <<RECTANGLE_COLOR>> {
    component "main.py" as main
    component "FastAPI" as fastapi
    component "Streamlit" as streamlit
    
    package "modules/" {
      component "fastapi_app.py" as app
      
      package "api/" <<API_COLOR>> {
        component "routers/" as routers
        component "services/" as services
        component "models/" as models
      }
      
      package "auto_rag/" {
        component "RAG System" as rag
        component "ChromaDB" as chroma
        component "Document Manager" as docmgr
      }
    }
    
    package "config/" {
      component "settings.py" as settings
      file ".env" as env
    }
  }
  
  package "web/" <<WEB_COLOR>> {
    component "Next.js Dev Server" as nextjs
    component "React Components" as react
    file "package.json" as pkgjson
  }
  
  package "api/ (레거시)" <<LEGACY_COLOR>> {
    component "Legacy API" as legacy_api
  }
  
  package "auto_rag/ (레거시)" <<LEGACY_COLOR>> {
    component "Legacy RAG" as legacy_rag
  }
}

package "External Services" {
  cloud "OpenAI API" as openai
  cloud "LangSmith" as langsmith
  database "Vector Database" as vectordb
}

' Connections
main --> fastapi
main --> streamlit
fastapi --> app
app --> routers
app --> services
services --> rag
rag --> chroma
rag --> docmgr

nextjs --> react
nextjs --> fastapi : "API 호출"

fastapi --> openai
rag --> openai
fastapi --> langsmith
settings --> env

note right of main
  개발 모드:
  - uvicorn --reload
  - 상세 로깅
  - 디버그 모드
end note

note right of nextjs
  포트: 3000
  - 핫 리로드
  - 개발 도구
end note

note right of fastapi
  포트: 8000
  - API 서버
  - Swagger UI
end note

note right of streamlit
  포트: 8501
  - 웹 인터페이스
  - 실시간 채팅
end note

@enduml
```

### 서버 모듈 상세 구조

```plantuml
@startuml server_module_detail
!define SERVER_COLOR #E3F2FD
!define API_COLOR #FFE0B2
!define RAG_COLOR #E8F5E8
!define CONFIG_COLOR #FFEBEE

title Server 모듈 상세 구조

package "server/" <<SERVER_COLOR>> {
  
  component "main.py" as main {
    - 서버 통합 실행
    - 프로세스 관리
    - 헬스 체크
  }
  
  package "modules/" {
    component "fastapi_app.py" as app {
      - FastAPI 앱 팩토리
      - 미들웨어 설정
      - CORS 구성
    }
    
    package "api/" <<API_COLOR>> {
      package "routers/" {
        component "rag.py" as rag_router
        component "documents.py" as doc_router
      }
      
      package "services/" {
        component "rag_service.py" as rag_service
        component "document_service.py" as doc_service
      }
      
      package "models/" {
        component "rag.py" as rag_models
        component "document.py" as doc_models
      }
    }
    
    package "auto_rag/" <<RAG_COLOR>> {
      component "rag_streamlit_v2.py" as streamlit_app
      
      package "mod/" {
        component "rag_system_manager.py" as rag_mgr
        component "chroma_db_manager.py" as chroma_mgr
        component "langsmith_monitor.py" as langsmith_mgr
      }
      
      folder "chroma_db/" as chroma_folder
      folder "raw_data/" as data_folder
    }
  }
  
  package "config/" <<CONFIG_COLOR>> {
    component "settings.py" as settings {
      - 환경 변수 관리
      - 앱 설정
      - 경로 관리
    }
    file ".env" as env_file
  }
  
  folder "logs/" as logs_folder
  folder "tests/" as tests_folder
  file "requirements.txt" as requirements
  file "setup.py" as setup
}

' Internal connections
main --> app
app --> rag_router
app --> doc_router
rag_router --> rag_service
doc_router --> doc_service
rag_service --> rag_mgr
doc_service --> chroma_mgr
rag_mgr --> chroma_folder
chroma_mgr --> chroma_folder
main --> streamlit_app
settings --> env_file

' External connections  
rag_mgr --> "OpenAI API" : "LLM 호출"
langsmith_mgr --> "LangSmith" : "추적 데이터"

note top of main
  통합 실행 파일:
  - FastAPI + Streamlit 동시 실행
  - 프로세스 모니터링
  - 자동 재시작
end note

note right of rag_mgr
  핵심 RAG 로직:
  - 문서 임베딩
  - 벡터 검색  
  - 응답 생성
end note

@enduml
```

## 🚀 배포 환경 구조

### 서버 전용 배포 아키텍처

```plantuml
@startuml production_architecture
!define PROD_COLOR #E8F5E8
!define API_COLOR #FFE0B2
!define DB_COLOR #FFEBEE
!define MONITOR_COLOR #F3E5F5

title RAG Lab 프로덕션 배포 아키텍처

package "Production Server" <<PROD_COLOR>> {
  
  package "server/" {
    component "main.py" as prod_main {
      - 프로덕션 모드
      - 리로드 비활성화
      - 로그 파일 저장
    }
    
    component "FastAPI" as prod_fastapi {
      포트: 8000
      - API 서버
      - 보안 강화 CORS
      - 성능 최적화
    }
    
    component "Streamlit" as prod_streamlit {
      포트: 8501  
      - 웹 인터페이스
      - 프로덕션 설정
    }
    
    package "modules/" {
      component "RAG System" as prod_rag
      component "Document Manager" as prod_docs
    }
    
    database "ChromaDB" as prod_chroma <<DB_COLOR>> {
      - 벡터 데이터베이스
      - 문서 임베딩 저장
      - 검색 인덱스
    }
    
    folder "raw_data/" as prod_data {
      - 업로드된 PDF
      - 원본 문서
    }
    
    folder "logs/" as prod_logs {
      - server.log
      - error.log
      - access.log
    }
    
    file ".env" as prod_env {
      프로덕션 환경 변수
      - API 키
      - 포트 설정
      - 보안 설정
    }
  }
}

package "External Services" {
  cloud "OpenAI API" as prod_openai
  cloud "LangSmith" as prod_langsmith
  component "Load Balancer" as lb
  component "Reverse Proxy" as proxy
}

package "Monitoring" <<MONITOR_COLOR>> {
  component "Log Monitoring" as log_monitor
  component "Performance Monitor" as perf_monitor
  component "Health Check" as health_check
}

' Connections
lb --> proxy
proxy --> prod_fastapi
proxy --> prod_streamlit

prod_main --> prod_fastapi
prod_main --> prod_streamlit
prod_fastapi --> prod_rag
prod_rag --> prod_chroma
prod_rag --> prod_data
prod_rag --> prod_openai
prod_fastapi --> prod_langsmith

prod_main --> prod_logs
log_monitor --> prod_logs
perf_monitor --> prod_fastapi
health_check --> prod_fastapi

note right of lb
  선택적 구성 요소:
  - 고가용성 필요시
  - 다중 인스턴스
end note

note right of prod_main
  프로덕션 설정:
  - DEBUG=false
  - UVICORN_RELOAD=false
  - LOG_LEVEL=WARNING
  - 성능 모니터링
end note

note bottom of prod_chroma
  지속성 데이터:
  - 백업 필요
  - 정기 유지보수
end note

@enduml
```

### 배포 플로우 다이어그램

```plantuml
@startuml deployment_flow
!define STEP_COLOR #E3F2FD
!define CHECK_COLOR #E8F5E8
!define ERROR_COLOR #FFEBEE

title Server 모듈 배포 플로우

start

:개발 환경에서 server 디렉토리 복사;

partition "환경 설정" <<STEP_COLOR>> {
  :target 서버 접속;
  :Python 3.8+ 설치 확인;
  :server 디렉토리 업로드;
}

partition "의존성 설치" <<STEP_COLOR>> {
  :cd server;
  :python setup.py 실행;
  
  if (setup.py 성공?) then (예)
    :가상환경 생성됨;
    :의존성 설치 완료;
  else (아니오)
    :수동 설치 시도;
    :python -m venv venv;
    :pip install -r requirements.txt;
    if (수동 설치 성공?) then (예)
      :계속 진행;
    else (아니오)
      :의존성 충돌 해결;
      stop
    endif
  endif
}

partition "환경 변수 설정" <<STEP_COLOR>> {
  :.env 파일 생성;
  :OpenAI API 키 설정;
  :선택적 설정 추가;
  
  if (API 키 유효?) then (예)
    :환경 변수 로드 성공;
  else (아니오)
    :API 키 확인 필요;
    note right : OPENAI_API_KEY 필수
    stop
  endif
}

partition "서버 실행" <<STEP_COLOR>> {
  :python main.py;
  
  if (서버 시작 성공?) then (예)
    :FastAPI 서버 실행됨 (포트 8000);
    :Streamlit 앱 실행됨 (포트 8501);
  else (아니오)
    if (포트 충돌?) then (예)
      :환경 변수로 포트 변경;
      :재시작 시도;
    else (아니오)
      :로그 확인;
      :문제 해결;
      stop
    endif
  endif
}

partition "검증" <<CHECK_COLOR>> {
  :헬스 체크 수행;
  :curl http://localhost:8000/health;
  
  if (헬스 체크 성공?) then (예)
    :API 기능 테스트;
    :Streamlit 접속 확인;
    
    if (모든 기능 정상?) then (예)
      :배포 완료;
    else (아니오)
      :기능별 문제 해결;
      note right 
        - ChromaDB 초기화
        - 문서 업로드 테스트
        - RAG 질의 테스트
      end note
    endif
  else (아니오)
    :서버 로그 확인;
    :오류 해결;
    stop
  endif
}

:모니터링 설정;
:로그 확인;
:성능 모니터링;

stop

@enduml
```

### 시스템 상호작용 다이어그램

```plantuml
@startuml system_interactions
!define USER_COLOR #E3F2FD
!define API_COLOR #FFE0B2
!define RAG_COLOR #E8F5E8
!define DB_COLOR #FFEBEE

title 시스템 구성 요소 상호작용

actor "사용자" as user
participant "Load Balancer" as lb
participant "FastAPI" as api
participant "RAG Service" as rag
participant "ChromaDB" as chroma
participant "OpenAI API" as openai
participant "LangSmith" as langsmith

user -> lb : HTTP 요청
lb -> api : 로드 밸런싱
api -> rag : 질의 처리 요청

alt RAG 질의 처리
  rag -> chroma : 유사 문서 검색
  chroma -> rag : 관련 문서 반환
  rag -> openai : LLM 요청 (컨텍스트 포함)
  openai -> rag : 생성된 응답
  rag -> langsmith : 추적 데이터 전송
  rag -> api : 최종 응답
  api -> lb : JSON 응답
  lb -> user : 응답 반환
end

alt 문서 업로드
  user -> api : PDF 업로드
  api -> rag : 문서 처리 요청
  rag -> chroma : 벡터 임베딩 저장
  chroma -> rag : 저장 완료
  rag -> api : 처리 완료
  api -> user : 업로드 성공
end

alt 헬스 체크
  lb -> api : /health 요청
  api -> rag : 시스템 상태 확인
  rag -> chroma : DB 연결 확인
  chroma -> rag : 상태 응답
  rag -> api : 전체 상태
  api -> lb : 200 OK
end

note over user, langsmith
  모든 AI 호출은 LangSmith로
  추적되어 성능 모니터링 가능
end note

@enduml
```

## 📊 성능 및 확장성 다이어그램

### 확장성 전략

```plantuml
@startuml scalability_strategy
!define SCALE_COLOR #E8F5E8
!define DB_COLOR #FFEBEE
!define CACHE_COLOR #FFF3E0

title RAG Lab 확장성 전략

package "수평 확장" <<SCALE_COLOR>> {
  component "Load Balancer" as lb
  component "Server Instance 1" as s1
  component "Server Instance 2" as s2  
  component "Server Instance N" as sn
}

package "데이터 계층" <<DB_COLOR>> {
  database "ChromaDB Cluster" as chroma_cluster
  database "Shared Storage" as storage
  database "Backup DB" as backup
}

package "캐싱 계층" <<CACHE_COLOR>> {
  component "Redis Cache" as redis
  component "Memory Cache" as memory
}

package "모니터링" {
  component "Metrics Collector" as metrics
  component "Log Aggregator" as logs
  component "Alert Manager" as alerts
}

' Connections
lb --> s1
lb --> s2
lb --> sn

s1 --> redis
s2 --> redis
sn --> redis

s1 --> chroma_cluster
s2 --> chroma_cluster
sn --> chroma_cluster

chroma_cluster --> storage
chroma_cluster --> backup

s1 --> metrics
s2 --> metrics
sn --> metrics

metrics --> alerts
logs --> alerts

note right of lb
  트래픽 분산:
  - Round Robin
  - Least Connections
  - Health Check
end note

note right of chroma_cluster
  데이터 분산:
  - 샤딩 지원
  - 복제 설정
  - 자동 백업
end note

note right of redis
  캐싱 전략:
  - 검색 결과 캐싱
  - 세션 저장
  - Rate Limiting
end note

@enduml
```

이러한 다이어그램들을 통해 RAG Lab의 아키텍처를 명확히 이해하고, 개발 환경에서 프로덕션 환경으로의 전환을 원활하게 수행할 수 있습니다.