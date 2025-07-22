# Elasticsearch Docker 설치 및 실행 가이드

RAG Lab의 하이브리드 검색 시스템을 위한 Elasticsearch Docker 컨테이너 설치 및 실행 가이드입니다.

## 📋 사전 요구사항

### 1. Docker Desktop 설치
- **Windows/Mac**: [Docker Desktop](https://www.docker.com/products/docker-desktop/) 다운로드 및 설치
- **Linux**: [Docker Engine](https://docs.docker.com/engine/install/) 설치

### 2. 시스템 요구사항
- **RAM**: 최소 4GB (8GB 권장)
- **디스크 공간**: 최소 5GB
- **포트**: 9200번 포트가 사용 가능해야 함

## 🚀 빠른 시작 (Quick Start)

### Windows PowerShell / Command Prompt
```powershell
# 1. Elasticsearch 컨테이너 실행
docker run -d --name es01 -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" docker.elastic.co/elasticsearch/elasticsearch:9.0.3

# 2. 컨테이너 상태 확인
docker ps | findstr es01

# 3. 연결 테스트 (30초 후)
curl -X GET "localhost:9200/_cluster/health?pretty"
```

### macOS/Linux Terminal
```bash
# 1. Elasticsearch 컨테이너 실행
docker run -d --name es01 -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" docker.elastic.co/elasticsearch/elasticsearch:9.0.3

# 2. 컨테이너 상태 확인
docker ps | grep es01

# 3. 연결 테스트 (30초 후)
curl -X GET "localhost:9200/_cluster/health?pretty"
```

## 📖 단계별 설명

### 1. Docker 컨테이너 실행

```bash
docker run -d \
  --name es01 \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  docker.elastic.co/elasticsearch/elasticsearch:9.0.3
```

**파라미터 설명:**
- `-d`: 백그라운드에서 실행
- `--name es01`: 컨테이너 이름을 'es01'로 설정
- `-p 9200:9200`: 호스트의 9200 포트를 컨테이너의 9200 포트에 매핑
- `discovery.type=single-node`: 단일 노드 클러스터로 실행
- `xpack.security.enabled=false`: 보안 기능 비활성화 (개발용)
- `ES_JAVA_OPTS=-Xms512m -Xmx512m`: Java 힙 메모리 설정

### 2. 컨테이너 상태 확인

```bash
# 실행 중인 컨테이너 확인
docker ps

# 모든 컨테이너 확인 (중지된 것 포함)
docker ps -a

# 특정 컨테이너 로그 확인
docker logs es01 --tail 20
```

### 3. Elasticsearch 연결 테스트

#### 방법 1: curl 사용
```bash
curl -X GET "localhost:9200/_cluster/health?pretty"
```

#### 방법 2: 웹 브라우저
브라우저에서 `http://localhost:9200/_cluster/health` 접속

#### 방법 3: PowerShell (Windows)
```powershell
Invoke-RestMethod -Uri "http://localhost:9200/_cluster/health" -Method GET
```

**정상 응답 예시:**
```json
{
  "cluster_name" : "docker-cluster",
  "status" : "green",
  "timed_out" : false,
  "number_of_nodes" : 1,
  "number_of_data_nodes" : 1,
  "active_primary_shards" : 0,
  "active_shards" : 0,
  "relocating_shards" : 0,
  "initializing_shards" : 0,
  "unassigned_shards" : 0,
  "unassigned_primary_shards" : 0,
  "delayed_unassigned_shards" : 0,
  "number_of_pending_tasks" : 0,
  "number_of_in_flight_fetch" : 0,
  "task_max_waiting_in_queue_millis" : 0,
  "active_shards_percent_as_number" : 100.0
}
```

## 🔧 컨테이너 관리 명령어

### 컨테이너 시작/중지/재시작
```bash
# 컨테이너 중지
docker stop es01

# 컨테이너 시작
docker start es01

# 컨테이너 재시작
docker restart es01

# 컨테이너 삭제 (중지 후)
docker rm es01

# 컨테이너 강제 삭제
docker rm -f es01
```

### 로그 확인
```bash
# 실시간 로그 확인
docker logs -f es01

# 최근 20줄 로그 확인
docker logs es01 --tail 20

# 특정 시간 이후 로그 확인
docker logs es01 --since="2024-01-01T00:00:00"
```

## 🛠️ 트러블슈팅

### 1. 포트 9200이 이미 사용 중인 경우

**문제**: `bind: address already in use` 오류

**해결방법:**
```bash
# 9200 포트를 사용하는 프로세스 확인 (Windows)
netstat -ano | findstr :9200

# 9200 포트를 사용하는 프로세스 확인 (macOS/Linux)
lsof -i :9200

# 다른 포트 사용 (예: 9201)
docker run -d --name es01 -p 9201:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" docker.elastic.co/elasticsearch/elasticsearch:9.0.3
```

### 2. 메모리 부족 오류

**문제**: `max virtual memory areas vm.max_map_count [65530] is too low`

**해결방법 (Linux/WSL2):**
```bash
# 임시 해결
sudo sysctl -w vm.max_map_count=262144

# 영구 해결
echo 'vm.max_map_count=262144' | sudo tee -a /etc/sysctl.conf
```

**해결방법 (Windows Docker Desktop):**
1. Docker Desktop 설정 열기
2. Resources → Advanced
3. Memory를 4GB 이상으로 설정

### 3. 컨테이너 실행되지만 연결 안 됨

**문제**: 컨테이너는 실행되지만 curl 연결 실패

**해결방법:**
```bash
# 1. 컨테이너 로그 확인
docker logs es01

# 2. 충분한 초기화 시간 대기 (30-60초)
sleep 30

# 3. 재시작
docker restart es01

# 4. 완전히 삭제 후 재실행
docker rm -f es01
docker run -d --name es01 -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" docker.elastic.co/elasticsearch/elasticsearch:9.0.3
```

### 4. Docker Desktop이 실행되지 않은 경우

**문제**: `Cannot connect to the Docker daemon`

**해결방법:**
1. Docker Desktop 애플리케이션 실행
2. Docker daemon이 시작될 때까지 대기 (2-3분)
3. 명령어 재실행

## 📊 RAG Lab과의 연동 확인

### 1. Streamlit 애플리케이션 실행
```bash
cd auto_rag
streamlit run rag_streamlit_v2.py
```

### 2. Elasticsearch 연동 테스트
1. **"Raw Data 동기화"** 탭으로 이동
2. **"Elasticsearch 병렬 인덱싱 활성화"** 체크박스 선택
3. **"✅ Elasticsearch 연결 확인"** 메시지 확인
4. 동기화 실행

### 3. 하이브리드 검색 테스트
1. **"하이브리드 검색"** 탭으로 이동
2. 검색 시스템 상태에서 **"✅ 사용 가능"** 확인
3. 검색어 입력하여 테스트

## 💡 성능 최적화 팁

### 메모리 설정
```bash
# 개발용 (2GB RAM 시)
-e "ES_JAVA_OPTS=-Xms256m -Xmx512m"

# 일반용 (4GB RAM 시)
-e "ES_JAVA_OPTS=-Xms512m -Xmx1g"

# 고성능 (8GB+ RAM 시)
-e "ES_JAVA_OPTS=-Xms1g -Xmx2g"
```

### Docker Compose 사용 (선택사항)

**docker-compose.yml 파일 생성:**
```yaml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:9.0.3
    container_name: es01
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    restart: unless-stopped

volumes:
  elasticsearch_data:
```

**실행:**
```bash
# 백그라운드에서 실행
docker-compose up -d

# 중지
docker-compose down
```

## 🔍 추가 리소스

- [Elasticsearch 공식 문서](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Docker 공식 문서](https://docs.docker.com/)
- [Elasticsearch Docker 가이드](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html)

## ❓ 자주 묻는 질문 (FAQ)

**Q: 다른 버전의 Elasticsearch를 사용할 수 있나요?**
A: 네, 가능합니다. 이미지 태그를 변경하세요:
```bash
# Elasticsearch 8.x 사용
docker.elastic.co/elasticsearch/elasticsearch:8.11.0

# Elasticsearch 7.x 사용 
elasticsearch:7.17.0
```

**Q: 데이터가 컨테이너 재시작 후에도 보존되나요?**
A: 기본 설정으로는 데이터가 보존되지 않습니다. 데이터 보존을 위해서는 볼륨을 마운트하세요:
```bash
docker run -d --name es01 -p 9200:9200 \
  -v es_data:/usr/share/elasticsearch/data \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  docker.elastic.co/elasticsearch/elasticsearch:9.0.3
```

**Q: 보안을 활성화하려면 어떻게 하나요?**
A: 개발 단계에서는 보안을 비활성화하는 것을 권장하지만, 프로덕션에서는 보안을 활성화해야 합니다. 자세한 내용은 [Elasticsearch Security 문서](https://www.elastic.co/guide/en/elasticsearch/reference/current/security-minimal-setup.html)를 참조하세요.

---

**📞 문제가 있으시면 팀 채널이나 이슈 트래커에 문의해 주세요!**