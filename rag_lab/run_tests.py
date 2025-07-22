#!/usr/bin/env python3
"""
Test runner script for RAG Lab project
Provides different test execution modes with proper environment setup
"""

import os
import sys
import subprocess
from pathlib import Path
import argparse

# Add project root to Python path
project_root = Path(__file__).parent
server_root = project_root / "server"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(server_root) not in sys.path:
    sys.path.insert(0, str(server_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / '.env')


def run_pytest(args_list):
    """Run pytest with given arguments"""
    cmd = ["python", "-m", "pytest"] + args_list
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=project_root)


def main():
    parser = argparse.ArgumentParser(description="RAG Lab Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--fast", action="store_true", help="Run fast tests only (skip slow)")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--file", type=str, help="Run specific test file")
    parser.add_argument("--pattern", type=str, help="Run tests matching pattern")
    parser.add_argument("--markers", type=str, help="Run tests with specific markers")
    parser.add_argument("--parallel", "-n", type=int, help="Run tests in parallel (requires pytest-xdist)")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be run without running")
    
    args = parser.parse_args()
    
    # Build pytest command
    pytest_args = []
    
    # Test selection
    if args.unit:
        pytest_args.extend(["-m", "unit or not (integration or e2e)"])
        pytest_args.append("tests/unit/")
    elif args.integration:
        pytest_args.extend(["-m", "integration or not (unit or e2e)"])
        pytest_args.append("tests/integration/")
    elif args.e2e:
        pytest_args.extend(["-m", "e2e or not (unit or integration)"])
        pytest_args.append("tests/e2e/")
    elif args.all:
        pytest_args.append("tests/")
    elif args.file:
        pytest_args.append(f"tests/{args.file}" if not args.file.startswith("tests/") else args.file)
    else:
        # Default: run unit and integration tests (skip e2e by default)
        pytest_args.extend(["-m", "not e2e"])
        pytest_args.append("tests/")
    
    # Speed options
    if args.fast:
        pytest_args.extend(["-m", "not slow"])
    
    # Pattern matching
    if args.pattern:
        pytest_args.extend(["-k", args.pattern])
    
    # Custom markers
    if args.markers:
        pytest_args.extend(["-m", args.markers])
    
    # Parallel execution
    if args.parallel:
        pytest_args.extend(["-n", str(args.parallel)])
    
    # Coverage
    if args.coverage:
        pytest_args.extend([
            "--cov=server.modules",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-fail-under=70"
        ])
    
    # Verbose output
    if args.verbose:
        pytest_args.append("-vvv")
    
    # Debug mode
    if args.debug:
        pytest_args.extend(["--pdb", "--capture=no"])
    
    # Show command in dry run
    if args.dry_run:
        cmd = ["python", "-m", "pytest"] + pytest_args
        print(f"Would run: {' '.join(cmd)}")
        print(f"Working directory: {project_root}")
        return
    
    # Set up environment
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{project_root}:{server_root}:{env.get('PYTHONPATH', '')}"
    
    # Run tests
    print("=" * 60)
    print("RAG Lab Test Runner")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f"Server root: {server_root}")
    print(f"Python path: {env['PYTHONPATH']}")
    print("=" * 60)
    
    result = run_pytest(pytest_args)
    
    # Print summary
    if result.returncode == 0:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {result.returncode}")
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())