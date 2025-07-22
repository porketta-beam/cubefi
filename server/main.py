#!/usr/bin/env python3
"""
RAG Lab Server - 간단한 FastAPI 서버 런처

FastAPI 백엔드 서버를 uvicorn으로 직접 실행하는 단순한 런처입니다.
웹 실행은 외부에서 별도로 처리되므로 API 서버만 실행합니다.

실행 방법:
    PYTHONPATH=. python main.py
    또는
    python main.py --host 0.0.0.0 --port 8000

옵션:
    --host: 서버 호스트 (기본값: 0.0.0.0)
    --port: 서버 포트 (기본값: 8000)
    --debug: 디버그 모드로 실행
    --reload: 개발 시 자동 리로드
"""

import os
import sys
import argparse
from pathlib import Path

# 현재 디렉토리를 Python path에 추가
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

def setup_environment():
    """환경 설정"""
    # 환경 변수 설정
    os.environ["PYTHONPATH"] = str(current_dir)
    
    # 설정 초기화
    try:
        from config import setup_environment as setup_env
        setup_env()
    except ImportError:
        print("WARNING: config 모듈을 찾을 수 없습니다. 기본 설정으로 실행합니다.")

def main():
    """FastAPI 서버 시작"""
    parser = argparse.ArgumentParser(description="RAG Lab Server - FastAPI 서버")
    parser.add_argument("--host", default="0.0.0.0", help="서버 호스트")
    parser.add_argument("--port", type=int, default=8000, help="서버 포트")
    parser.add_argument("--debug", action="store_true", help="디버그 모드")
    parser.add_argument("--reload", action="store_true", help="자동 리로드")
    
    args = parser.parse_args()
    
    # 환경 변수에서 포트 설정 읽기
    port = int(os.getenv("SERVER_PORT", args.port))
    
    print("RAG Lab Server 시작")
    print("=" * 50)
    print(f"호스트: {args.host}")
    print(f"포트: {port}")
    print(f"디버그 모드: {args.debug}")
    print(f"자동 리로드: {args.reload}")
    print("=" * 50)
    
    # 환경 설정
    setup_environment()
    
    # uvicorn으로 FastAPI 서버 실행
    import uvicorn
    
    try:
        uvicorn.run(
            "modules.fastapi_app:app",
            host=args.host,
            port=port,
            reload=args.reload,
            log_level="debug" if args.debug else "info"
        )
    except KeyboardInterrupt:
        print("\n서버가 중단되었습니다.")
    except Exception as e:
        print(f"ERROR: 서버 시작 오류: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())