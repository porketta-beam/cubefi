@echo off
echo ====================================
echo  RAG Lab Elasticsearch 중지 스크립트
echo ====================================
echo.

echo Elasticsearch 컨테이너를 중지합니다...
docker stop es01 2>nul

if %errorlevel% equ 0 (
    echo ✅ Elasticsearch 컨테이너가 중지되었습니다.
) else (
    echo ⚠️  실행 중인 es01 컨테이너를 찾을 수 없습니다.
)

echo.
echo 현재 컨테이너 상태:
docker ps -a | findstr es01

echo.
echo 스크립트 완료. 아무 키나 눌러 종료하세요.
pause >nul