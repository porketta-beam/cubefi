"""Comprehensive test suite for RAG Lab API endpoints
Migrated from server/tests/test_api_endpoints.py with fixed imports"""

import pytest
import tempfile
import os
import json
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi import UploadFile
import io

# Import using fixed paths
from server.modules.fastapi_app import app
from server.modules.api.models.document_config import DocumentConfigModel
from server.modules.services.document_lifecycle_service import DocumentLifecycleService


class TestAPIEndpoints:
    """API endpoint integration tests"""
    
    def test_health_check(self, test_client):
        """Health check endpoint test"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_upload_pdf_success(self, test_client, temp_raw_data, uploaded_pdf_file):
        """PDF upload success test"""
        files = {"file": uploaded_pdf_file}
        
        response = test_client.post("/api/documents/upload-file", files=files)
        assert response.status_code in [200, 201]
        
        data = response.json()
        assert "doc_id" in data
        assert "test" in data["doc_id"]
        
        # Verify file was actually saved
        doc_id = data["doc_id"]
        doc_dir = Path(temp_raw_data) / doc_id
        assert doc_dir.exists()
        assert (doc_dir / "original.pdf").exists()
        
        return doc_id
    
    def test_upload_text_success(self, test_client, temp_raw_data, uploaded_text_file):
        """Text file upload success test"""
        files = {"file": uploaded_text_file}
        
        response = test_client.post("/api/documents/upload-file", files=files)
        assert response.status_code in [200, 201]
        
        data = response.json()
        assert "doc_id" in data
        doc_id = data["doc_id"]
        
        # Verify file
        doc_dir = Path(temp_raw_data) / doc_id
        assert (doc_dir / "original.txt").exists()
        
        return doc_id
    
    def test_upload_invalid_file_type(self, test_client):
        """Invalid file type upload test"""
        files = {
            "file": ("test.exe", io.BytesIO(b"fake exe content"), "application/x-msdownload")
        }
        
        response = test_client.post("/api/documents/upload-file", files=files)
        assert response.status_code == 400
    
    def test_upload_no_file(self, test_client):
        """Upload request without file test"""
        response = test_client.post("/api/documents/upload-file")
        assert response.status_code == 422  # Validation error
    
    def test_sync_single_document(self, test_client, temp_raw_data, uploaded_pdf_file):
        """Single document sync test"""
        # First upload document
        doc_id = self.test_upload_pdf_success(test_client, temp_raw_data, uploaded_pdf_file)
        
        # Execute sync
        response = test_client.get(f"/api/documents/sync?doc_id={doc_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert doc_id in str(data)
    
    def test_delete_document(self, test_client, temp_raw_data, uploaded_pdf_file):
        """Document deletion test"""
        # First upload document
        doc_id = self.test_upload_pdf_success(test_client, temp_raw_data, uploaded_pdf_file)
        
        # Delete document
        response = test_client.delete(f"/api/documents/{doc_id}")
        assert response.status_code == 204
        
        # Verify file was actually deleted
        doc_dir = Path(temp_raw_data) / doc_id
        assert not doc_dir.exists()
    
    def test_delete_nonexistent_document(self, test_client):
        """Nonexistent document deletion test"""
        response = test_client.delete("/api/documents/nonexistent_1234567890123")
        assert response.status_code == 404
    
    def test_document_status(self, test_client):
        """Document status endpoint test"""
        response = test_client.get("/api/documents/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "db_exists" in data
        assert "document_count" in data
    
    def test_document_list(self, test_client):
        """Document list endpoint test"""
        response = test_client.get("/api/documents/list")
        assert response.status_code == 200
        
        data = response.json()
        assert "files" in data


class TestDocumentLifecycleService:
    """DocumentLifecycleService unit tests"""
    
    @pytest.fixture
    def temp_service(self):
        """Service with temporary directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            service = DocumentLifecycleService(temp_dir)
            yield service, temp_dir
    
    def test_generate_doc_id_english(self, temp_service):
        """English filename document ID generation test"""
        service, _ = temp_service
        
        doc_id = service._generate_doc_id("test_document.pdf")
        assert doc_id.startswith("test-document_")
        assert len(doc_id.split("_")[-1]) == 13  # 13-digit timestamp
    
    def test_generate_doc_id_korean(self, temp_service):
        """Korean filename document ID generation test"""
        service, _ = temp_service
        
        doc_id = service._generate_doc_id("테스트 문서.pdf")
        assert "_" in doc_id
        assert len(doc_id.split("_")[-1]) == 13
    
    def test_generate_doc_id_special_chars(self, temp_service):
        """Special characters filename document ID generation test"""
        service, _ = temp_service
        
        doc_id = service._generate_doc_id("test@#$%^&*()document.pdf")
        # Should be sanitized to alphanumeric plus dash/underscore
        clean_id = doc_id.replace("-", "").replace("_", "").replace(doc_id.split("_")[-1], "")
        assert clean_id.isalnum()


if __name__ == "__main__":
    # Run pytest
    pytest.main([__file__, "-v"])
