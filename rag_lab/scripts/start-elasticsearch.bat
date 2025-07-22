@echo off
echo ====================================
echo  RAG Lab Elasticsearch 시작 스크립트
echo ====================================
echo.

echo [1/4] 기존 컨테이너 확인 중...
docker ps -a | findstr es01 >nul 2>&1
if %errorlevel% equ 0 (
    echo 기존 es01 컨테이너가 발견되었습니다. 제거 중...
    docker rm -f es01 >nul 2>&1
    echo 기존 컨테이너가 제거되었습니다.
)

echo.
echo [2/4] Elasticsearch 컨테이너 시작 중...
docker run -d --name es01 -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" docker.elastic.co/elasticsearch/elasticsearch:9.0.3

if %errorlevel% neq 0 (
    echo ERROR: 컨테이너 시작에 실패했습니다.
    echo Docker Desktop이 실행 중인지 확인해주세요.
    pause
    exit /b 1
)

echo 컨테이너가 시작되었습니다!

echo.
echo [3/4] Elasticsearch 초기화 대기 중... (30초)
timeout /t 30 /nobreak >nul

echo.
echo [4/4] 연결 테스트 중...
curl -X GET "localhost:9200/_cluster/health?pretty" 2>nul | findstr "green\|yellow" >nul 2>&1

if %errorlevel% equ 0 (
    echo.
    echo ✅ SUCCESS: Elasticsearch가 성공적으로 시작되었습니다!
    echo 🌐 접속 URL: http://localhost:9200
    echo 📊 Health Check: http://localhost:9200/_cluster/health
    echo.
    echo 이제 Streamlit에서 Elasticsearch 연동을 활성화할 수 있습니다.
) else (
    echo.
    echo ⚠️  WARNING: Elasticsearch가 아직 완전히 시작되지 않았을 수 있습니다.
    echo 1-2분 후에 다시 확인해보세요.
    echo 상태 확인: curl -X GET "localhost:9200/_cluster/health?pretty"
)

echo.
echo 컨테이너 상태:
docker ps | findstr es01

echo.
echo 스크립트 완료. 아무 키나 눌러 종료하세요.
pause >nul