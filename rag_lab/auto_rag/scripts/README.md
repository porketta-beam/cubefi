# RAG Lab Elasticsearch 실행 스크립트

RAG Lab의 하이브리드 검색 시스템을 위한 Elasticsearch Docker 컨테이너를 쉽게 시작/중지할 수 있는 스크립트입니다.

## 🚀 빠른 실행

### Windows 사용자
```cmd
# Elasticsearch 시작
scripts\start-elasticsearch.bat

# Elasticsearch 중지
scripts\stop-elasticsearch.bat
```

### macOS/Linux 사용자
```bash
# Elasticsearch 시작
./scripts/start-elasticsearch.sh

# Elasticsearch 중지
./scripts/stop-elasticsearch.sh
```

## 📋 사전 요구사항

1. **Docker Desktop 설치 및 실행 중**
2. **포트 9200 사용 가능**
3. **최소 4GB RAM 권장**

## ✅ 실행 확인 방법

### 1. 브라우저에서 확인
[http://localhost:9200/_cluster/health](http://localhost:9200/_cluster/health) 접속

### 2. 터미널에서 확인
```bash
# Windows
curl -X GET "localhost:9200/_cluster/health?pretty"

# macOS/Linux
curl -X GET "localhost:9200/_cluster/health?pretty"
```

### 3. 정상 응답 예시
```json
{
  "cluster_name" : "docker-cluster",
  "status" : "green",  // 이 부분이 "green"이어야 함
  "number_of_nodes" : 1,
  ...
}
```

## 🔧 수동 명령어

스크립트 없이 직접 실행하려면:

```bash
# 시작
docker run -d --name es01 -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" docker.elastic.co/elasticsearch/elasticsearch:9.0.3

# 중지
docker stop es01

# 삭제
docker rm es01
```

## 🔍 Streamlit 연동

1. Elasticsearch 시작 후 Streamlit 실행:
   ```bash
   cd auto_rag
   streamlit run rag_streamlit_v2.py
   ```

2. **"Raw Data 동기화"** 탭에서 **"Elasticsearch 병렬 인덱싱 활성화"** 체크

3. **"하이브리드 검색"** 탭에서 검색 테스트

## ❗ 트러블슈팅

**포트 충돌 오류가 나면:**
```bash
# 9200 포트 사용 중인 프로세스 확인
netstat -ano | findstr :9200  # Windows
lsof -i :9200                 # macOS/Linux
```

**Docker 오류가 나면:**
- Docker Desktop이 실행 중인지 확인
- 충분한 메모리 할당 확인 (4GB+)

자세한 내용은 `docs/elasticsearch-docker-setup.md` 참조하세요.