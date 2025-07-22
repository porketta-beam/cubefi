"""
Centralized test module for RAG Lab project
Consolidates all test code from server/ and root level test files
"""

import os
import sys
from pathlib import Path

# Add project root and server to Python path for imports
project_root = Path(__file__).parent.parent
server_root = project_root / "server"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(server_root) not in sys.path:
    sys.path.insert(0, str(server_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(project_root / '.env')