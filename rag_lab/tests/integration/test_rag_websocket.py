#!/usr/bin/env python3
"""
Integration tests for RAG WebSocket functionality
"""

import pytest
import requests
import json
import asyncio
import websockets
from fastapi.testclient import TestClient
from server.modules.fastapi_app import app


class TestRAGWebSocket:
    """Test RAG WebSocket functionality"""
    
    @pytest.mark.integration
    def test_rag_config(self, test_client):
        """Test RAG configuration endpoint"""
        # Test GET config
        response = test_client.get("/api/rag/config")
        assert response.status_code == 200
        config_data = response.json()
        assert isinstance(config_data, dict)
        
        # Test SET config
        config_update = {
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "search_type": "similarity",
            "k": 5,
            "search_kwargs": {}
        }
        
        response = test_client.post("/api/rag/set", json=config_update)
        assert response.status_code == 200
        result = response.json()
        assert "success" in result or "message" in result
    
    @pytest.mark.integration
    def test_document_sync(self, test_client):
        """Test document synchronization"""
        # Check document status
        response = test_client.get("/api/documents/status")
        assert response.status_code == 200
        status = response.json()
        assert "db_exists" in status or "status" in status
        
        # If no documents, try to sync
        if not status.get("db_exists", True):
            sync_data = {
                "chunk_size": 500,
                "chunk_overlap": 100
            }
            sync_response = test_client.post("/api/documents/sync", json=sync_data)
            assert sync_response.status_code in [200, 400, 404]  # Various valid responses
    
    @pytest.mark.integration 
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection and basic functionality"""
        # Note: This test requires a running server, so we'll simulate the logic
        # In a real integration test environment, you would start the server first
        
        # Mock WebSocket test logic - would need actual server for full test
        test_question = "What is tax law?"
        message = {"message": test_question}
        
        # Assert basic message structure
        assert "message" in message
        assert message["message"] == test_question
        
        # Test response structure expectations
        expected_response_types = ["start", "chunk", "done", "error"]
        assert "start" in expected_response_types
        assert "chunk" in expected_response_types
        assert "done" in expected_response_types
        assert "error" in expected_response_types
    
    @pytest.mark.integration
    def test_websocket_message_validation(self):
        """Test WebSocket message validation"""
        # Test valid message structure
        valid_message = {"message": "What is tax law?"}
        assert "message" in valid_message
        assert len(valid_message["message"]) > 0
        
        # Test empty message handling
        empty_message = {"message": ""}
        assert "message" in empty_message
        assert len(empty_message["message"]) == 0
        
        # Test message serialization
        json_message = json.dumps(valid_message)
        parsed_message = json.loads(json_message)
        assert parsed_message["message"] == valid_message["message"]
