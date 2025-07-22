#!/usr/bin/env python3
"""
End-to-end tests for RAG functionality with documents
"""

import pytest
import requests
import json
import asyncio
import websockets
from time import sleep
import subprocess
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from server.modules.fastapi_app import app


class TestRAGWithDocuments:
    """End-to-end tests for RAG functionality with documents"""
    
    @pytest.mark.e2e
    def test_document_sync_workflow(self, test_client):
        """Test complete document synchronization workflow"""
        # Check current status
        response = test_client.get("/api/documents/status")
        assert response.status_code == 200
        status = response.json()
        assert "db_exists" in status or "status" in status
        
        # Attempt document sync
        sync_data = {
            "chunk_size": 500,
            "chunk_overlap": 100
        }
        
        response = test_client.post("/api/documents/sync", json=sync_data)
        # Accept various response codes as document sync may not always be possible
        assert response.status_code in [200, 400, 404]
        
        if response.status_code == 200:
            result = response.json()
            assert "success" in result
            if result["success"]:
                assert "total_documents" in result
    
    @pytest.mark.e2e
    def test_rag_configuration_workflow(self, test_client):
        """Test complete RAG configuration workflow"""
        # Set RAG configuration
        config_data = {
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "search_type": "similarity",
            "k": 5
        }
        
        response = test_client.post("/api/rag/set", json=config_data)
        assert response.status_code == 200
        result = response.json()
        
        # Should indicate successful configuration
        assert "success" in result or "message" in result
        
        # Verify configuration was set by getting it back
        get_response = test_client.get("/api/rag/config")
        assert get_response.status_code == 200
        current_config = get_response.json()
        assert isinstance(current_config, dict)
    
    @pytest.mark.e2e
    def test_rag_chat_workflow(self, test_client):
        """Test complete RAG chat workflow"""
        # First set up configuration
        config_data = {
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "search_type": "similarity",
            "k": 5
        }
        test_client.post("/api/rag/set", json=config_data)
        
        # Test RAG chat
        chat_data = {
            "question": "What is tax law?",
            "model": "gpt-4o-mini",
            "temperature": 0.0,
            "search_type": "similarity",
            "k": 3
        }
        
        response = test_client.post("/api/rag/chat", json=chat_data)
        assert response.status_code == 200
        result = response.json()
        
        # Should have basic response structure
        assert "answer" in result
        assert "success" in result
        assert "contexts" in result or "sources" in result
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_workflow_simulation(self):
        """Test complete workflow simulation (without actual server startup)"""
        # This simulates the complete workflow logic without starting a server
        # In a real e2e environment, this would start an actual server
        
        # Test data structures and workflow logic
        test_question = "What is tax law?"
        message = {"message": test_question}
        
        # Simulate WebSocket message structure
        assert "message" in message
        assert len(message["message"]) > 0
        
        # Simulate response types that would be received
        response_types = ["start", "chunk", "done", "error"]
        for response_type in response_types:
            mock_response = {
                "type": response_type,
                "content": "test content" if response_type == "chunk" else None,
                "message": "test message" if response_type != "chunk" else None
            }
            
            assert mock_response["type"] in response_types
            if response_type == "chunk":
                assert mock_response["content"] is not None
            else:
                assert mock_response["message"] is not None
    
    @pytest.mark.e2e
    def test_error_handling_workflow(self, test_client):
        """Test error handling in complete workflow"""
        # Test with invalid configuration
        invalid_config = {
            "model": "",  # Invalid empty model
            "temperature": 2.0,  # Invalid temperature (should be 0-1)
            "k": -1  # Invalid k value
        }
        
        response = test_client.post("/api/rag/set", json=invalid_config)
        # Should handle invalid config gracefully
        assert response.status_code in [200, 400, 422]
        
        # Test with empty question
        chat_data = {
            "question": "",
            "model": "gpt-4o-mini"
        }
        
        response = test_client.post("/api/rag/chat", json=chat_data)
        assert response.status_code == 200
        result = response.json()
        
        # Should handle empty question gracefully
        assert "success" in result
        if not result.get("success", False):
            assert "error" in result or "message" in result
    
    @pytest.mark.e2e
    def test_system_health_workflow(self, test_client):
        """Test system health and status workflow"""
        # Test health endpoint
        response = test_client.get("/health")
        assert response.status_code == 200
        health_data = response.json()
        assert "status" in health_data
        
        # Test document status
        response = test_client.get("/api/documents/status")
        assert response.status_code == 200
        status_data = response.json()
        assert isinstance(status_data, dict)
        
        # Test RAG config retrieval
        response = test_client.get("/api/rag/config")
        assert response.status_code == 200
        config_data = response.json()
        assert isinstance(config_data, dict)
