# RAG Lab Scripts

개인 프로젝트 수준으로 단순한 구조로 작성된 마이그레이션 및 테스트 스크립트들입니다.

## 📁 Scripts

### 1. `backfill_default_config.py`
레거시 문서에 `config.json`과 `metadata.json` 파일을 자동 생성하는 마이그레이션 스크립트

**사용법:**
```bash
# 마이그레이션 대상 문서 확인 (실제 실행하지 않음)
python scripts/backfill_default_config.py --dry-run

# 실제 마이그레이션 실행
python scripts/backfill_default_config.py

# 다른 디렉토리 지정
python scripts/backfill_default_config.py --raw-data-root /path/to/raw_data
```

**기능:**
- 레거시 문서 발견 (config.json 또는 metadata.json이 없는 문서)
- 기본 설정으로 config.json 생성
- 파일 정보 기반으로 metadata.json 생성
- 에러 발생 시 상세 로그 출력

### 2. `run_tests.py`
전체 시스템에 대한 통합 테스트 실행

**사용법:**
```bash
python scripts/run_tests.py
```

**테스트 항목:**
- 서버 임포트 테스트 (기본 의존성 확인)
- 마이그레이션 스크립트 테스트
- API 엔드포인트 테스트 (pytest 설치된 경우)

### 3. `performance_test.py`
API 엔드포인트 성능 테스트

**사용법:**
```bash
# 기본 테스트 (5개 파일)
python scripts/performance_test.py

# 파일 개수 지정
python scripts/performance_test.py --files 10

# 결과를 JSON 파일로 저장
python scripts/performance_test.py --files 5 --output results.json
```

**테스트 항목:**
- 파일 업로드 성능
- 설정 조회/업데이트 성능
- 동기화 성능 (단일/전체)
- 문서 삭제 성능
- 성능 평가 및 권장사항

## 📋 Tests 디렉토리

### `tests/test_api_endpoints.py`
종합적인 API 엔드포인트 테스트 스위트

**테스트 클래스:**
- `TestAPIEndpoints`: FastAPI 통합 테스트
- `TestDocumentLifecycleService`: 서비스 레이어 단위 테스트

**pytest로 실행:**
```bash
# 전체 테스트 실행
pytest tests/test_api_endpoints.py -v

# 특정 테스트만 실행
pytest tests/test_api_endpoints.py::TestAPIEndpoints::test_upload_pdf_success -v

# 상세한 출력
pytest tests/test_api_endpoints.py -v --tb=long
```

## 🚀 빠른 시작

### 1. 전체 시스템 테스트
```bash
# 모든 테스트 실행
python scripts/run_tests.py
```

### 2. 레거시 문서 마이그레이션
```bash
# 마이그레이션 대상 확인
python scripts/backfill_default_config.py --dry-run

# 실제 마이그레이션 실행
python scripts/backfill_default_config.py
```

### 3. 성능 테스트
```bash
# 간단한 성능 테스트
python scripts/performance_test.py --files 3
```

## 📊 성능 기준

### 업로드 성능
- **목표**: 평균 < 2초 (10MB 이하 파일)
- **허용**: 평균 < 5초

### 설정 API 성능
- **GET**: < 100ms
- **PUT**: < 500ms

### 동기화 성능
- **단일 문서**: < 3초
- **전체 동기화**: 문서당 < 2초

## 🔧 의존성

### 필수 의존성
- Python 3.8+
- FastAPI
- 서버의 모든 의존성 (requirements.txt)

### 선택적 의존성
```bash
# 테스트 실행을 위해
pip install pytest pytest-asyncio

# 성능 테스트 결과 저장을 위해 (이미 포함됨)
# json 모듈은 Python 기본 제공
```

## 🐛 문제 해결

### 마이그레이션 실패
1. `raw_data` 디렉토리 경로 확인
2. 권한 문제 확인 (쓰기 권한 필요)
3. 디스크 공간 확인

### 테스트 실패
1. 서버 의존성 설치 확인: `pip install -r requirements.txt`
2. 환경변수 설정 확인
3. 테스트용 임시 디렉토리 생성 권한 확인

### 성능 테스트 문제
1. 서버가 실행 중이지 않아야 함 (TestClient 사용)
2. 충분한 메모리와 디스크 공간 확인
3. 백그라운드 프로세스 종료

## 📝 로그 및 디버깅

모든 스크립트는 상세한 로그를 출력합니다:
- ✓ 성공 (녹색)
- ✗ 실패 (빨간색)
- 경고 및 정보 메시지

에러 발생 시 상세한 traceback과 함께 문제 해결 방법을 제시합니다.