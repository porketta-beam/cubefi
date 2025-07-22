@echo off
REM Windows batch script to run tests

echo.
echo =====================================
echo RAG Lab Test Runner (Windows)
echo =====================================
echo.

REM Set environment variables
set PROJECT_ROOT=%~dp0
set PYTHONPATH=%PROJECT_ROOT%;%PROJECT_ROOT%\server;%PYTHONPATH%

REM Change to project directory
cd /d "%PROJECT_ROOT%"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Load virtual environment if it exists
if exist "server\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call server\venv\Scripts\activate.bat
)

REM Check if pytest is installed
python -c "import pytest" >nul 2>&1
if errorlevel 1 (
    echo WARNING: pytest is not installed. Installing...
    pip install pytest pytest-asyncio
)

REM Run the test runner
python run_tests.py %*

REM Pause if no arguments provided (interactive mode)
if "%~1"=="" (
    echo.
    pause
)