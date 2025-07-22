"""Tests for DocumentService
Consolidated from server/test_document_service.py with fixed imports"""

import os
import sys
import tempfile
from pathlib import Path
import pytest

# Fixed imports
from server.modules.api.services.document_service import DocumentService
from server.config.settings import settings


class TestDocumentService:
    """Test DocumentService functionality"""
    
    @pytest.fixture
    def temp_chroma_path(self):
        """Temporary ChromaDB path for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override settings for test
            original_path = getattr(settings, 'chroma_persist_directory', None)
            settings.chroma_persist_directory = temp_dir
            yield temp_dir
            # Restore original path
            if original_path:
                settings.chroma_persist_directory = original_path
    
    def test_document_service_initialization(self):
        """Test DocumentService can be initialized"""
        service = DocumentService()
        assert service is not None
        assert hasattr(service, 'db_manager')
    
    def test_get_status(self, temp_chroma_path):
        """Test getting service status"""
        service = DocumentService()
        status = service.get_status()
        
        assert isinstance(status, dict)
        assert 'db_exists' in status
        assert 'document_count' in status
        assert isinstance(status['db_exists'], bool)
        assert isinstance(status['document_count'], int)
    
    def test_list_documents(self, temp_chroma_path):
        """Test listing documents"""
        service = DocumentService()
        result = service.list_documents()
        
        assert isinstance(result, dict)
        assert 'files' in result
        assert isinstance(result['files'], list)
    
    def test_delete_database(self, temp_chroma_path):
        """Test database deletion"""
        service = DocumentService()
        result = service.delete_database()
        
        assert isinstance(result, dict)
        assert 'success' in result
        assert isinstance(result['success'], bool)
    
    def test_db_manager_direct_access(self, temp_chroma_path):
        """Test direct access to db_manager"""
        service = DocumentService()
        
        # Test db_manager methods
        db_status = service.db_manager.get_status()
        assert isinstance(db_status, dict)
        assert 'db_exists' in db_status
        assert 'db_loaded' in db_status
        
        # Test loading database if exists
        if db_status["db_exists"] and not db_status["db_loaded"]:
            loaded = service.db_manager.load_existing_db()
            assert isinstance(loaded, bool)
            
            # Check status after loading
            new_status = service.db_manager.get_status()
            assert isinstance(new_status, dict)
            
            # Try to get files
            files = service.db_manager.get_files_in_db()
            assert isinstance(files, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
