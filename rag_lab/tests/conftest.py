"""
Pytest configuration and shared fixtures for all tests
"""

import pytest
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient
import io

# Ensure proper import paths are set
from tests import *

@pytest.fixture(scope="session")
def project_root():
    """Project root directory"""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def server_root(project_root):
    """Server directory"""
    return project_root / "server"

@pytest.fixture(scope="class")
def test_client():
    """FastAPI test client for API testing"""
    from server.modules.fastapi_app import app
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="class")
def temp_raw_data():
    """Temporary raw_data directory for testing"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set environment variable
        original_env = os.environ.get("RAW_DATA_ROOT")
        os.environ["RAW_DATA_ROOT"] = temp_dir
        yield temp_dir
        # Restore environment
        if original_env:
            os.environ["RAW_DATA_ROOT"] = original_env
        elif "RAW_DATA_ROOT" in os.environ:
            del os.environ["RAW_DATA_ROOT"]

@pytest.fixture
def sample_pdf_content():
    """Sample PDF content for testing"""
    return b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n178\n%%EOF'

@pytest.fixture
def sample_text_content():
    """Sample text content for testing"""
    return "This is a sample text document for testing purposes.\nIt contains multiple lines."

@pytest.fixture
def uploaded_pdf_file(sample_pdf_content):
    """Create an UploadFile object for PDF testing"""
    return ("test.pdf", io.BytesIO(sample_pdf_content), "application/pdf")

@pytest.fixture
def uploaded_text_file(sample_text_content):
    """Create an UploadFile object for text testing"""
    return ("test.txt", io.BytesIO(sample_text_content.encode()), "text/plain")