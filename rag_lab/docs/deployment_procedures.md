# 서버 전용 배포 절차 가이드

이 문서는 RAG Lab server 모듈을 독립적으로 배포하는 상세한 절차를 설명합니다.

## 📋 배포 전 체크리스트

### 시스템 요구사항
- [ ] Python 3.8 이상
- [ ] 최소 4GB RAM (권장: 8GB)
- [ ] 10GB 이상 디스크 공간
- [ ] 인터넷 연결 (API 호출 및 의존성 설치)
- [ ] 포트 8000, 8501 사용 가능

### 필수 준비 사항
- [ ] OpenAI API 키 확보
- [ ] 서버 접속 권한 확보
- [ ] 방화벽 설정 확인
- [ ] 백업 계획 수립

## 🚀 배포 방법별 상세 절차

### 방법 1: 최소 복사 배포 (권장)

#### 1단계: 소스 준비
```bash
# 개발 환경에서 server 디렉토리 압축
cd rag_lab
tar -czf server-deployment.tar.gz server/

# 또는 ZIP 파일로 압축 (Windows)
powershell Compress-Archive -Path server -DestinationPath server-deployment.zip
```

#### 2단계: 서버 전송
```bash
# SCP를 이용한 전송
scp server-deployment.tar.gz user@target-server:/home/user/

# 또는 FTP, SFTP 등 사용
```

#### 3단계: 서버에서 설치
```bash
# 대상 서버 접속
ssh user@target-server

# 압축 해제
tar -xzf server-deployment.tar.gz
cd server

# 자동 설정 실행
python setup.py
```

#### 4단계: 환경 변수 설정
```bash
# .env 파일 생성
cp .env.sample .env

# 환경 변수 편집
nano .env
# 또는
vim .env
```

최소 필수 설정:
```env
OPENAI_API_KEY=sk-proj-your-actual-api-key-here
DEBUG=false
UVICORN_RELOAD=false
```

#### 5단계: 실행 및 검증
```bash
# 서버 실행
python main.py

# 다른 터미널에서 헬스 체크
curl http://localhost:8000/health

# 웹 인터페이스 확인
curl http://localhost:8501
```

### 방법 2: Docker 컨테이너 배포

#### Dockerfile 생성
```dockerfile
# server/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 디렉토리 생성
RUN mkdir -p logs chroma_db raw_data

# 포트 노출
EXPOSE 8000 8501

# 헬스체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 실행
CMD ["python", "main.py"]
```

#### Docker Compose 설정
```yaml
# docker-compose.yml
version: '3.8'

services:
  rag-server:
    build: .
    ports:
      - "8000:8000"
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DEBUG=false
      - UVICORN_RELOAD=false
    volumes:
      - ./chroma_db:/app/chroma_db
      - ./raw_data:/app/raw_data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### Docker 배포 실행
```bash
# 이미지 빌드
docker build -t rag-lab-server .

# 컨테이너 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

### 방법 3: 시스템 서비스 등록

#### systemd 서비스 파일 생성
```bash
# /etc/systemd/system/rag-lab.service
sudo nano /etc/systemd/system/rag-lab.service
```

```ini
[Unit]
Description=RAG Lab Server
After=network.target

[Service]
Type=simple
User=raglab
Group=raglab
WorkingDirectory=/home/raglab/server
Environment=PATH=/home/raglab/server/venv/bin
ExecStart=/home/raglab/server/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 서비스 등록 및 시작
```bash
# 서비스 등록
sudo systemctl daemon-reload
sudo systemctl enable rag-lab.service

# 서비스 시작
sudo systemctl start rag-lab.service

# 상태 확인
sudo systemctl status rag-lab.service

# 로그 확인
sudo journalctl -u rag-lab.service -f
```

## 🔧 환경별 배포 설정

### 개발 환경 (Development)
```bash
# .env.development
DEBUG=true
LOG_LEVEL=DEBUG
UVICORN_RELOAD=true
CORS_ORIGINS=*
DOCS_ENABLED=true
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=rag_lab_dev
```

### 스테이징 환경 (Staging)
```bash
# .env.staging
DEBUG=false
LOG_LEVEL=INFO
UVICORN_RELOAD=false
CORS_ORIGINS=https://staging.example.com
DOCS_ENABLED=true
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=rag_lab_staging
```

### 프로덕션 환경 (Production)
```bash
# .env.production
DEBUG=false
LOG_LEVEL=WARNING
UVICORN_RELOAD=false
CORS_ORIGINS=https://app.example.com
DOCS_ENABLED=false
LANGSMITH_TRACING=false
API_KEY_HEADER=X-API-Key
API_KEY_VALUE=production-secret-key
```

## 🌐 웹 서버 프록시 설정

### Nginx 설정
```nginx
# /etc/nginx/sites-available/rag-lab
server {
    listen 80;
    server_name your-domain.com;

    # FastAPI 프록시
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Streamlit 프록시
    location /streamlit/ {
        proxy_pass http://127.0.0.1:8501/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 지원
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 정적 파일
    location /static/ {
        alias /home/raglab/server/static/;
    }
}
```

### Apache 설정
```apache
# /etc/apache2/sites-available/rag-lab.conf
<VirtualHost *:80>
    ServerName your-domain.com
    
    # FastAPI 프록시
    ProxyPass /api/ http://127.0.0.1:8000/
    ProxyPassReverse /api/ http://127.0.0.1:8000/
    
    # Streamlit 프록시
    ProxyPass /streamlit/ http://127.0.0.1:8501/
    ProxyPassReverse /streamlit/ http://127.0.0.1:8501/
    
    # WebSocket 지원
    ProxyPass /streamlit/_stcore/stream ws://127.0.0.1:8501/_stcore/stream
    ProxyPassReverse /streamlit/_stcore/stream ws://127.0.0.1:8501/_stcore/stream
</VirtualHost>
```

## 🔍 배포 후 검증 절차

### 1. 기본 기능 테스트
```bash
# 1. 헬스 체크
curl -X GET http://localhost:8000/health
# 예상 응답: {"status": "healthy", "timestamp": "..."}

# 2. API 문서 접근
curl -X GET http://localhost:8000/docs
# 예상: Swagger UI HTML

# 3. 기본 채팅 API 테스트
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "안녕하세요", "session_id": "test"}'

# 4. Streamlit 웹앱 접근
curl -X GET http://localhost:8501
# 예상: Streamlit 앱 HTML
```

### 2. 문서 업로드 테스트
```bash
# 테스트 PDF 생성
echo "테스트 문서 내용" > test.txt
# PDF로 변환 또는 실제 PDF 파일 사용

# 문서 업로드 테스트
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@test.pdf"
```

### 3. 성능 테스트
```bash
# 부하 테스트 (선택적)
# Apache Benchmark 사용
ab -n 100 -c 10 http://localhost:8000/health

# 또는 wrk 사용
wrk -t4 -c100 -d30s http://localhost:8000/health
```

### 4. 로그 확인
```bash
# 서버 로그 확인
tail -f logs/server.log

# 시스템 로그 확인 (systemd 사용 시)
sudo journalctl -u rag-lab.service -f

# Docker 로그 확인 (Docker 사용 시)
docker-compose logs -f
```

## 🔄 업데이트 및 롤백 절차

### 업데이트 절차
```bash
# 1. 현재 버전 백업
cp -r server server-backup-$(date +%Y%m%d)

# 2. 새 버전 배포
# (위의 배포 절차 반복)

# 3. 설정 파일 복사
cp server-backup-*/env server/.env

# 4. 데이터베이스 마이그레이션 (필요시)
python migrate_data.py

# 5. 서비스 재시작
sudo systemctl restart rag-lab.service
```

### 롤백 절차
```bash
# 1. 서비스 중지
sudo systemctl stop rag-lab.service

# 2. 백업 버전으로 복원
rm -rf server
mv server-backup-20240120 server

# 3. 서비스 재시작
sudo systemctl start rag-lab.service

# 4. 검증
curl http://localhost:8000/health
```

## 📊 모니터링 및 알림 설정

### 기본 모니터링 스크립트
```bash
#!/bin/bash
# monitor-rag-lab.sh

LOG_FILE="/var/log/rag-lab-monitor.log"
HEALTH_URL="http://localhost:8000/health"
ALERT_EMAIL="admin@example.com"

# 헬스 체크
if curl -f $HEALTH_URL > /dev/null 2>&1; then
    echo "$(date): Service healthy" >> $LOG_FILE
else
    echo "$(date): Service down - sending alert" >> $LOG_FILE
    echo "RAG Lab service is down" | mail -s "Alert: RAG Lab Down" $ALERT_EMAIL
    
    # 자동 재시작 시도
    sudo systemctl restart rag-lab.service
fi

# 디스크 사용량 확인
DISK_USAGE=$(df /home/raglab | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): High disk usage: ${DISK_USAGE}%" >> $LOG_FILE
    echo "Disk usage is at ${DISK_USAGE}%" | mail -s "Alert: High Disk Usage" $ALERT_EMAIL
fi
```

### Crontab 설정
```bash
# 모니터링 스크립트를 5분마다 실행
crontab -e

# 다음 라인 추가
*/5 * * * * /home/raglab/monitor-rag-lab.sh
```

## 🔐 보안 강화 절차

### 1. 시스템 보안
```bash
# 전용 사용자 생성
sudo useradd -m -s /bin/bash raglab

# 권한 설정
sudo chown -R raglab:raglab /home/raglab/server
sudo chmod 750 /home/raglab/server
sudo chmod 600 /home/raglab/server/.env
```

### 2. 방화벽 설정
```bash
# UFW 사용 (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw deny 8000  # 직접 접근 차단 (Nginx 프록시 사용)
sudo ufw deny 8501
sudo ufw enable
```

### 3. SSL 인증서 설정
```bash
# Let's Encrypt 인증서 발급
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## 🚨 트러블슈팅 가이드

### 자주 발생하는 문제

#### 1. 포트 충돌
**증상**: `Address already in use` 오류
**해결**:
```bash
# 포트 사용 프로세스 확인
sudo netstat -tlnp | grep :8000
sudo lsof -i :8000

# 프로세스 종료
sudo kill -9 [PID]

# 또는 다른 포트 사용
export SERVER_PORT=8080
```

#### 2. 메모리 부족
**증상**: 서버 응답 없음, OOM 에러
**해결**:
```bash
# 메모리 사용량 확인
free -m
ps aux --sort=-%mem | head

# 스왑 추가
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 3. 의존성 충돌
**증상**: Import 에러, 모듈 로드 실패
**해결**:
```bash
# 가상환경 재생성
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. ChromaDB 오류
**증상**: 벡터 검색 실패, DB 연결 오류
**해결**:
```bash
# ChromaDB 재초기화
rm -rf chroma_db
# 서버 재시작하면 자동 재생성
```

### 로그 분석
```bash
# 오류 패턴 확인
grep -i error logs/server.log
grep -i "500\|502\|503" logs/server.log

# 성능 이슈 확인
grep -i "slow\|timeout" logs/server.log

# 사용량 패턴 확인
grep "POST /api/chat" logs/server.log | wc -l
```

이 가이드를 따라 RAG Lab server 모듈을 안전하고 효율적으로 배포할 수 있습니다.