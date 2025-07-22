#!/usr/bin/env python3
"""
RAG Lab Server 독립 실행 스크립트

server 폴더에서 완전히 독립적으로 실행하기 위한 런처입니다.
PYTHONPATH를 자동으로 설정하고 main.py를 실행합니다.
"""

import sys
import os
from pathlib import Path
import platform
import subprocess

# Set UTF-8 encoding for Windows console
if platform.system() == "Windows":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def setup_environment():
    """실행 환경 설정"""
    # 현재 디렉토리를 Python path에 추가
    current_dir = Path(__file__).parent.absolute()
    sys.path.insert(0, str(current_dir))
    
    # 환경변수 설정
    os.environ["PYTHONPATH"] = str(current_dir)
    
    return current_dir

def check_dependencies():
    """필수 의존성 확인"""
    try:
        import fastapi
        import uvicorn
        return True
    except ImportError as e:
        print(f"❌ 필수 패키지가 설치되지 않았습니다: {e}")
        print("\n🔧 해결 방법:")
        print("1. 가상환경이 활성화되어 있는지 확인")
        print("2. python setup.py 실행으로 의존성 설치")
        print("3. pip install -r requirements.txt 수동 실행")
        return False

def check_env_file():
    """환경변수 파일 확인"""
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("⚠️ .env 파일이 없습니다.")
        print("🔧 python setup.py를 실행하거나 .env.example을 복사하세요.")
        return False
    return True

def get_python_executable():
    """현재 Python 실행파일 경로 반환"""
    venv_dir = Path(__file__).parent / "venv"
    
    if venv_dir.exists():
        # 가상환경이 있으면 해당 Python 사용
        if platform.system() == "Windows":
            venv_python = venv_dir / "Scripts" / "python.exe"
        else:
            venv_python = venv_dir / "bin" / "python"
        
        if venv_python.exists():
            return str(venv_python)
    
    # 가상환경이 없으면 현재 Python 사용
    return sys.executable

def main():
    """메인 실행 함수"""
    print("🚀 RAG Lab Server 시작")
    print("-" * 50)
    
    # 1. 환경 설정
    current_dir = setup_environment()
    print(f"📁 작업 디렉토리: {current_dir}")
    
    # 2. 의존성 확인
    if not check_dependencies():
        sys.exit(1)
    
    # 3. 환경변수 파일 확인
    if not check_env_file():
        response = input("계속 진행하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # 4. main.py 실행
    try:
        print("🔄 main.py 실행 중...")
        from main import main as main_func
        return main_func()
        
    except ImportError as e:
        print(f"❌ main.py import 실패: {e}")
        print("\n🔧 대안 실행 방법:")
        
        # 서브프로세스로 실행 시도
        python_exe = get_python_executable()
        main_py = current_dir / "main.py"
        
        if main_py.exists():
            print(f"⚡ 서브프로세스로 실행: {python_exe} {main_py}")
            try:
                result = subprocess.run([
                    python_exe, str(main_py)
                ] + sys.argv[1:], cwd=str(current_dir))
                return result.returncode
            except Exception as e:
                print(f"❌ 서브프로세스 실행 실패: {e}")
        
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ 실행 중 오류: {e}")
        print("\n💡 도움말:")
        print("1. python setup.py로 환경을 다시 설정하세요")
        print("2. .env 파일에 API 키가 올바르게 설정되었는지 확인하세요")
        print("3. requirements.txt의 모든 패키지가 설치되었는지 확인하세요")
        sys.exit(1)

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code or 0)
    except KeyboardInterrupt:
        print("\n\n👋 사용자에 의해 중단되었습니다.")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"\n❌ 예기치 않은 오류: {e}")
        sys.exit(1)