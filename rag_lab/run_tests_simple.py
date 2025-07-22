#!/usr/bin/env python3
"""Simple test runner without Unicode characters"""

import os
import sys
import subprocess
from pathlib import Path

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

def run_tests(test_args=None):
    """Run pytest with basic arguments"""
    if test_args is None:
        test_args = ["tests/unit/", "-v"]
    
    cmd = [sys.executable, "-m", "pytest"] + test_args
    print(f"Running: {' '.join(cmd)}")
    
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{project_root}:{server_root}:{env.get('PYTHONPATH', '')}"
    
    result = subprocess.run(cmd, cwd=project_root, env=env)
    
    if result.returncode == 0:
        print("\nAll tests passed!")
    else:
        print(f"\nTests failed with exit code {result.returncode}")
    
    return result.returncode

if __name__ == "__main__":
    # Default to unit tests
    sys.exit(run_tests())