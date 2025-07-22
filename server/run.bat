@echo off
:: RAG Lab Server Windows 실행 스크립트
:: 이 배치 파일은 Windows에서 RAG Lab Server를 쉽게 실행할 수 있게 해줍니다.

title RAG Lab Server

echo ================================
echo    RAG Lab Server - Windows
echo ================================
echo.

:: 현재 디렉토리로 이동
cd /d "%~dp0"

:: PYTHONPATH 설정
set PYTHONPATH=%CD%

:: 가상환경 확인 및 실행
if exist "venv\Scripts\python.exe" (
    echo [INFO] 가상환경 사용: venv\Scripts\python.exe
    "venv\Scripts\python.exe" run.py %*
) else (
    echo [INFO] 시스템 Python 사용
    python run.py %*
)

:: 오류 확인
if %ERRORLEVEL% neq 0 (
    echo.
    echo ================================
    echo    실행 중 오류가 발생했습니다!
    echo ================================
    echo.
    echo 해결 방법:
    echo 1. python setup.py 실행
    echo 2. .env 파일에 API 키 설정
    echo 3. 의존성 패키지 설치 확인
    echo.
    goto :end
)

echo.
echo ================================
echo      RAG Lab Server 종료
echo ================================

:end
echo.
echo 아무 키나 누르면 창이 닫힙니다...
pause >nul