#!/usr/bin/env python3
"""
Integration tests for empty VectorDB exception handling
"""

import pytest
import requests
import json
import asyncio
import websockets
from time import sleep
from fastapi.testclient import TestClient
from server.modules.fastapi_app import app


class TestEmptyVectorDB:
    """Test API endpoints with empty VectorDB"""
    
    @pytest.mark.integration
    def test_empty_vectordb_rag_chat(self, test_client):
        """Test RAG chat with empty VectorDB"""
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
        
        # Should handle empty VectorDB gracefully
        assert "answer" in result
        assert "success" in result
    
    @pytest.mark.integration
    def test_empty_vectordb_generate_questions(self, test_client):
        """Test question generation with empty VectorDB"""
        question_data = {
            "model": "gpt-4o-mini",
            "temperature": 0.9,
            "num_questions": 3
        }
        
        response = test_client.post("/api/rag/generate-questions", json=question_data)
        assert response.status_code == 200
        result = response.json()
        
        # Should handle empty VectorDB gracefully
        assert "questions" in result or "error" in result
        assert "success" in result
    
    @pytest.mark.integration
    def test_empty_vectordb_evaluate(self, test_client):
        """Test evaluation with empty VectorDB"""
        eval_data = {
            "questions": ["What is tax law?", "How do I calculate tax?"],
            "model": "gpt-4o-mini",
            "temperature": 0.0,
            "search_type": "similarity",
            "k": 5
        }
        
        response = test_client.post("/api/rag/evaluate", json=eval_data)
        assert response.status_code == 200
        result = response.json()
        
        # Should handle empty VectorDB gracefully
        assert "results" in result or "error" in result
        assert "success" in result
    
    @pytest.mark.integration
    def test_input_validation_empty_question(self, test_client):
        """Test input validation with empty question"""
        chat_data = {
            "question": "",
            "model": "gpt-4o-mini"
        }
        
        response = test_client.post("/api/rag/chat", json=chat_data)
        assert response.status_code == 200
        result = response.json()
        
        # Should handle empty question gracefully
        assert "answer" in result or "error" in result
        assert "success" in result
    
    @pytest.mark.integration
    def test_input_validation_invalid_num_questions(self, test_client):
        """Test input validation with invalid number of questions"""
        question_data = {
            "model": "gpt-4o-mini",
            "num_questions": 0
        }
        
        response = test_client.post("/api/rag/generate-questions", json=question_data)
        assert response.status_code == 200
        result = response.json()
        
        # Should handle invalid input gracefully
        assert "success" in result
        if not result["success"]:
            assert "error" in result
    
    @pytest.mark.integration
    def test_input_validation_no_questions(self, test_client):
        """Test evaluation with no questions"""
        eval_data = {
            "questions": [],
            "model": "gpt-4o-mini"
        }
        
        response = test_client.post("/api/rag/evaluate", json=eval_data)
        assert response.status_code == 200
        result = response.json()
        
        # Should handle empty questions list gracefully
        assert "success" in result
        if not result["success"]:
            assert "error" in result
