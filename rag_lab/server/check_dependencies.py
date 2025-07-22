#!/usr/bin/env python3
"""
RAG Lab Server 의존성 검증 스크립트

독립 실행에 필요한 모든 요소들을 검증합니다.
"""

import sys
import os
from pathlib import Path
import importlib.util

def print_status(check_name, status, message=""):
    """상태를 색상과 함께 출력"""
    if status:
        print(f"[OK] {check_name}")
        if message:
            print(f"     -> {message}")
    else:
        print(f"[FAIL] {check_name}")
        if message:
            print(f"     -> {message}")

def check_python_version():
    """Python 버전 확인"""
    version = sys.version_info
    is_valid = version.major >= 3 and version.minor >= 8
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    print_status("Python 버전", is_valid, f"현재: {version_str} (요구: 3.8+)")
    return is_valid

def check_path_setup():
    """PYTHONPATH 설정 확인"""
    current_dir = str(Path(__file__).parent.absolute())
    in_path = current_dir in sys.path
    print_status("PYTHONPATH 설정", in_path, f"현재 디렉토리: {current_dir}")
    
    if not in_path:
        sys.path.insert(0, current_dir)
        print("   → PYTHONPATH에 현재 디렉토리 추가됨")
    
    return True

def check_module_import(module_name, description=""):
    """모듈 import 가능 여부 확인"""
    try:
        importlib.import_module(module_name)
        print_status(f"{description or module_name}", True, "import 성공")
        return True
    except ImportError as e:
        print_status(f"{description or module_name}", False, f"import 실패: {e}")
        return False

def check_core_modules():
    """핵심 모듈들 확인"""
    results = []
    
    # 기본 modules 패키지
    results.append(check_module_import("modules", "기본 modules 패키지"))
    
    # config 모듈
    results.append(check_module_import("config", "설정 모듈"))
    
    return all(results)

def check_required_packages():
    """필수 패키지들 확인"""
    packages = [
        ("fastapi", "FastAPI 웹 프레임워크"),
        ("uvicorn", "ASGI 서버"),
        ("streamlit", "Streamlit 웹 앱"),
        ("openai", "OpenAI API 클라이언트"),
        ("langchain", "LangChain 프레임워크"),
        ("chromadb", "ChromaDB 벡터 데이터베이스"),
        ("python-dotenv", "환경변수 관리", "dotenv"),
    ]
    
    results = []
    for package_info in packages:
        if len(package_info) == 3:
            package, description, import_name = package_info
        else:
            package, description = package_info
            import_name = package.replace("-", "_")
        
        results.append(check_module_import(import_name, f"{description} ({package})"))
    
    return all(results)

def check_files_and_directories():
    """필수 파일 및 디렉토리 확인"""
    current_dir = Path(__file__).parent
    
    files_to_check = [
        ("main.py", "메인 실행 파일"),
        ("run.py", "독립 실행 스크립트"),
        ("setup.py", "설정 스크립트"),
        ("requirements.txt", "의존성 목록"),
        (".env.example", "환경변수 예시"),
        ("README.md", "사용 가이드"),
    ]
    
    dirs_to_check = [
        ("modules", "핵심 모듈 디렉토리"),
        ("modules/api", "API 모듈"),
        ("modules/auto_rag", "RAG 시스템 모듈"),
        ("config", "설정 모듈"),
        ("web", "웹 애플리케이션"),
    ]
    
    results = []
    
    print("\n[FILES] 파일 검증:")
    for filename, description in files_to_check:
        file_path = current_dir / filename
        exists = file_path.exists()
        print_status(f"{description} ({filename})", exists, 
                    f"위치: {file_path}" if exists else "파일 없음")
        results.append(exists)
    
    print("\n[DIRS] 디렉토리 검증:")
    for dirname, description in dirs_to_check:
        dir_path = current_dir / dirname
        exists = dir_path.exists() and dir_path.is_dir()
        print_status(f"{description} ({dirname})", exists,
                    f"위치: {dir_path}" if exists else "디렉토리 없음")
        results.append(exists)
    
    return all(results)

def check_environment_file():
    """환경변수 파일 확인"""
    current_dir = Path(__file__).parent
    env_file = current_dir / ".env"
    env_example = current_dir / ".env.example"
    
    has_example = env_example.exists()
    has_env = env_file.exists()
    
    print("\n[ENV] 환경 설정:")
    print_status(".env.example 파일", has_example)
    print_status(".env 파일", has_env, 
                "설정 완료" if has_env else "cp .env.example .env 실행 필요")
    
    return has_example

def check_import_paths():
    """import 경로 정상 동작 확인"""
    print("\n[IMPORT] Import 경로 검증:")
    
    # 상대적 import가 절대 import로 제대로 변경되었는지 확인
    import_tests = [
        ("modules.api.routers.rag", "API RAG 라우터"),
        ("modules.api.routers.documents", "API 문서 라우터"),
        ("modules.api.services.rag_service", "RAG 서비스"),
        ("modules.api.services.document_service", "문서 서비스"),
    ]
    
    results = []
    for module_path, description in import_tests:
        try:
            # 모듈을 실제로 import하지 않고 스펙만 확인
            spec = importlib.util.find_spec(module_path)
            if spec is not None:
                print_status(description, True, f"모듈 경로: {module_path}")
                results.append(True)
            else:
                print_status(description, False, f"모듈을 찾을 수 없음: {module_path}")
                results.append(False)
        except Exception as e:
            print_status(description, False, f"오류: {e}")
            results.append(False)
    
    return all(results)

def main():
    """메인 검증 함수"""
    print("RAG Lab Server 독립성 검증")
    print("=" * 60)
    
    checks = [
        ("Python 버전", check_python_version),
        ("PYTHONPATH 설정", check_path_setup),
        ("파일 및 디렉토리", check_files_and_directories),
        ("환경 설정", check_environment_file),
        ("핵심 모듈", check_core_modules),
        ("Import 경로", check_import_paths),
        ("필수 패키지", check_required_packages),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n[CHECK] {check_name} 검증:")
        try:
            result = check_func()
            if not result:
                all_passed = False
        except Exception as e:
            print_status(check_name, False, f"검증 중 오류: {e}")
            all_passed = False
    
    # 최종 결과
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] 모든 검증 통과! 독립 실행 준비 완료")
        print("\n[RUN] 실행 방법:")
        print("   python run.py")
        print("   또는")
        print("   python setup.py  (의존성 설치 후)")
        print("   python run.py")
    else:
        print("[FAILED] 일부 검증 실패. 위의 오류들을 해결해주세요.")
        print("\n[FIX] 해결 방법:")
        print("1. python setup.py 실행 (가상환경 및 의존성 설치)")
        print("2. .env 파일 설정 (cp .env.example .env 후 API 키 설정)")
        print("3. 누락된 파일들 확인")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())