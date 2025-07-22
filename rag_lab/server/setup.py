#!/usr/bin/env python3
"""
RAG Lab Server 설정 스크립트

가상환경 생성 및 의존성 설치를 자동화합니다.
"""

import subprocess
import sys
import os
from pathlib import Path
import platform
import shutil
import time

def print_step(step, message):
    """단계별 출력 포맷"""
    print(f"\n{'='*60}")
    print(f"STEP {step}: {message}")
    print('='*60)

def remove_venv_safely(venv_dir):
    """Windows에서 안전하게 가상환경 삭제"""
    try:
        # 첫 번째 시도: 일반 삭제
        shutil.rmtree(venv_dir)
        return True
    except PermissionError:
        print("⚠️ 파일이 사용 중입니다. 강제 삭제 시도...")
        try:
            # Windows에서 강제 삭제 시도
            if platform.system() == "Windows":
                subprocess.run(f'rmdir /s /q "{venv_dir}"', shell=True, check=True)
            else:
                subprocess.run(f'rm -rf "{venv_dir}"', shell=True, check=True)
            time.sleep(1)  # 삭제 완료 대기
            return True
        except subprocess.CalledProcessError:
            return False
    except Exception as e:
        print(f"예상치 못한 오류: {e}")
        return False

def check_python_version():
    """Python 버전 확인"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        print(f"현재 버전: {version.major}.{version.minor}.{version.micro}")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} 확인됨")

def create_virtual_environment():
    """가상환경 생성"""
    current_dir = Path(__file__).parent.absolute()
    venv_dir = current_dir / "venv"
    
    if venv_dir.exists():
        print(f"⚠️ 가상환경이 이미 존재합니다: {venv_dir}")
        response = input("다시 생성하시겠습니까? (y/N): ")
        if response.lower() != 'y':
            return venv_dir
        
        # 기존 가상환경 삭제 (Windows 호환성 개선)
        print("🗑️ 기존 가상환경 삭제 중...")
        if not remove_venv_safely(venv_dir):
            print("❌ 가상환경 삭제 실패. 다음을 시도해보세요:")
            print("1. VS Code/Cursor 완전 종료")
            print("2. 터미널에서 'deactivate' 실행")
            print("3. 다시 setup.py 실행")
            sys.exit(1)
    
    print(f"🔨 가상환경 생성 중: {venv_dir}")
    try:
        subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
        print("✅ 가상환경 생성 완료")
        return venv_dir
    except subprocess.CalledProcessError as e:
        print(f"❌ 가상환경 생성 실패: {e}")
        sys.exit(1)

def get_pip_path(venv_dir):
    """플랫폼별 pip 경로 반환"""
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "pip.exe"
    else:
        return venv_dir / "bin" / "pip"

def install_dependencies(venv_dir):
    """의존성 설치"""
    pip_path = get_pip_path(venv_dir)
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt 파일을 찾을 수 없습니다.")
        sys.exit(1)
    
    print("📦 pip 업그레이드 중...")
    try:
        # Python -m pip 방식으로 안전하게 업그레이드
        python_path = venv_dir / ("Scripts" if platform.system() == "Windows" else "bin") / ("python.exe" if platform.system() == "Windows" else "python")
        subprocess.run([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], check=True)
        print("✅ pip 업그레이드 완료")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ pip 업그레이드 실패 (계속 진행): {e}")
    
    print(f"📦 의존성 설치 중: {requirements_file}")
    try:
        # Python -m pip 방식으로 안전하게 설치
        subprocess.run([
            str(python_path), "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True)
        print("✅ 의존성 설치 완료")
    except subprocess.CalledProcessError as e:
        print(f"❌ 의존성 설치 실패: {e}")
        print("💡 해결 방법:")
        print("1. 가상환경을 활성화한 후 수동으로 설치: venv\\Scripts\\activate && pip install -r requirements.txt")
        print("2. 인터넷 연결 상태 확인")
        print("3. 방화벽 또는 프록시 설정 확인")
        sys.exit(1)

def create_env_file():
    """환경변수 파일 생성"""
    env_file = Path(__file__).parent / ".env"
    env_example = Path(__file__).parent / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        print("📝 .env 파일 생성 중...")
        with open(env_example, 'r', encoding='utf-8') as src:
            with open(env_file, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        print("✅ .env 파일 생성 완료 (API 키를 설정해주세요)")
        return True
    elif env_file.exists():
        print("✅ .env 파일이 이미 존재합니다")
        return False
    else:
        print("⚠️ .env.example 파일을 찾을 수 없습니다")
        return False

def display_next_steps(venv_created, env_created):
    """다음 단계 안내"""
    print("\n" + "="*60)
    print("🎉 설정 완료!")
    print("="*60)
    
    if env_created:
        print("\n📝 다음 단계:")
        print("1. .env 파일을 열어 API 키를 설정하세요:")
        print("   - OPENAI_API_KEY=your_openai_api_key_here")
        print("   - LANGSMITH_API_KEY=your_langsmith_api_key_here (선택사항)")
    
    print("\n🚀 실행 방법:")
    if platform.system() == "Windows":
        print("   python run.py")
        print("   또는")
        print("   run.bat")
    else:
        print("   python run.py")
        print("   또는")
        print("   ./run.sh")
    
    print("\n🌐 접속 URL:")
    print("   - FastAPI: http://localhost:8000")
    print("   - Streamlit: http://localhost:8501")
    print("   - API 문서: http://localhost:8000/docs")

def main():
    """메인 실행 함수"""
    print("🤖 RAG Lab Server 설정 시작")
    
    # 1. Python 버전 확인
    print_step(1, "Python 버전 확인")
    check_python_version()
    
    # 2. 가상환경 생성
    print_step(2, "가상환경 생성")
    venv_dir = create_virtual_environment()
    
    # 3. 의존성 설치
    print_step(3, "의존성 설치")
    install_dependencies(venv_dir)
    
    # 4. 환경변수 파일 생성
    print_step(4, "환경변수 파일 생성")
    env_created = create_env_file()
    
    # 5. 다음 단계 안내
    display_next_steps(True, env_created)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 예기치 않은 오류: {e}")
        sys.exit(1)