#!/usr/bin/env python3
"""
Simple test runner for RAG Lab
개인 프로젝트용 간단한 테스트 실행 스크립트
"""

import os
import sys
import subprocess
from pathlib import Path


def run_migration_test():
    """마이그레이션 스크립트 테스트 실행"""
    print("=" * 60)
    print("Running Migration Test")
    print("=" * 60)
    
    script_path = Path(__file__).parent / "backfill_default_config.py"
    
    try:
        # Dry run 테스트
        print("1. Testing dry run...")
        result = subprocess.run([
            sys.executable, str(script_path), "--dry-run"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   + Dry run test passed")
        else:
            print(f"   - Dry run test failed: {result.stderr}")
            return False
            
        print("2. Migration script test completed")
        return True
        
    except subprocess.TimeoutExpired:
        print("   - Migration test timed out")
        return False
    except Exception as e:
        print(f"   - Migration test error: {e}")
        return False


def run_api_tests():
    """API 테스트 실행"""
    print("=" * 60)
    print("Running API Tests")
    print("=" * 60)
    
    test_file = Path(__file__).parent.parent / "tests" / "test_api_endpoints.py"
    
    if not test_file.exists():
        print("   - Test file not found")
        return False
    
    try:
        # pytest 실행
        print("Running pytest...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"
        ], timeout=300)  # 5분 제한
        
        if result.returncode == 0:
            print("   + All API tests passed")
            return True
        else:
            print("   - Some API tests failed")
            return False
            
    except subprocess.TimeoutExpired:
        print("   - API tests timed out")
        return False
    except FileNotFoundError:
        print("   - pytest not found. Install with: pip install pytest pytest-asyncio")
        return False
    except Exception as e:
        print(f"   - API test error: {e}")
        return False


def run_quick_server_test():
    """빠른 서버 시작 테스트"""
    print("=" * 60)
    print("Running Quick Server Test")
    print("=" * 60)
    
    try:
        # 서버가 정상적으로 시작되는지 테스트
        print("Testing server import...")
        result = subprocess.run([
            sys.executable, "-c", "import main; print('Server import successful')"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("   + Server import test passed")
            return True
        else:
            print(f"   - Server import failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   - Server test timed out")
        return False
    except Exception as e:
        print(f"   - Server test error: {e}")
        return False


def main():
    """메인 테스트 실행"""
    print("RAG Lab Test Suite")
    print("개인 프로젝트용 간단한 테스트")
    print()
    
    # 현재 디렉토리를 server로 변경
    server_dir = Path(__file__).parent.parent
    os.chdir(server_dir)
    
    tests_passed = 0
    total_tests = 3
    
    # 1. 서버 임포트 테스트
    if run_quick_server_test():
        tests_passed += 1
    
    # 2. 마이그레이션 테스트
    if run_migration_test():
        tests_passed += 1
    
    # 3. API 테스트 (pytest가 설치된 경우에만)
    try:
        import pytest
        if run_api_tests():
            tests_passed += 1
    except ImportError:
        print("=" * 60)
        print("Skipping API Tests (pytest not installed)")
        print("To run API tests, install: pip install pytest pytest-asyncio")
        print("=" * 60)
        total_tests -= 1
    
    # 결과 요약
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("+ All tests passed! The server is ready to use.")
        print("\nYou can start the server with:")
        print("  python main.py --debug")
        sys.exit(0)
    else:
        print("- Some tests failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()