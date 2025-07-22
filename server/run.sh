#!/bin/bash
# RAG Lab Server Linux/Mac 실행 스크립트
# 이 셸 스크립트는 Linux/Mac에서 RAG Lab Server를 쉽게 실행할 수 있게 해줍니다.

set -e  # 오류 발생 시 즉시 종료

echo "==============================="
echo "   RAG Lab Server - Unix/Linux"
echo "==============================="
echo

# 스크립트 디렉토리로 이동
cd "$(dirname "$0")"

# PYTHONPATH 설정
export PYTHONPATH="$(pwd)"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 정보 출력 함수
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# 성공 출력 함수
success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# 경고 출력 함수
warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 오류 출력 함수
error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 가상환경 확인 및 실행
if [ -f "venv/bin/python" ]; then
    info "가상환경 사용: venv/bin/python"
    PYTHON_CMD="./venv/bin/python"
elif [ -f "venv/bin/python3" ]; then
    info "가상환경 사용: venv/bin/python3"
    PYTHON_CMD="./venv/bin/python3"
else
    info "시스템 Python 사용"
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        error "Python을 찾을 수 없습니다!"
        exit 1
    fi
fi

# Python 버전 확인
info "Python 버전 확인 중..."
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
info "Python $PYTHON_VERSION 사용"

# 실행
info "RAG Lab Server 시작 중..."
if $PYTHON_CMD run.py "$@"; then
    success "RAG Lab Server가 정상적으로 종료되었습니다"
    exit 0
else
    error "RAG Lab Server 실행 중 오류가 발생했습니다!"
    echo
    echo "=============================="
    echo "      오류 해결 방법"
    echo "=============================="
    echo
    echo "1. 설정 스크립트 실행:"
    echo "   $PYTHON_CMD setup.py"
    echo
    echo "2. .env 파일 확인:"
    echo "   cp .env.example .env"
    echo "   # .env 파일에 API 키 설정"
    echo
    echo "3. 의존성 수동 설치:"
    echo "   pip install -r requirements.txt"
    echo
    echo "4. 권한 문제 해결:"
    echo "   chmod +x run.sh"
    echo
    exit 1
fi