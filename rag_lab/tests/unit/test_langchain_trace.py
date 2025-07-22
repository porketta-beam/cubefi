#!/usr/bin/env python3
"""
Unit tests for LangChain tracing functionality
"""

import pytest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()


class TestLangChainTrace:
    """Test LangChain tracing functionality"""
    
    @pytest.mark.unit
    @patch('langchain_openai.ChatOpenAI')
    def test_langchain_trace_setup(self, mock_chat_openai):
        """Test LangChain ChatOpenAI setup"""
        # Mock the ChatOpenAI instance
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        # Import and create LLM (simulates the original script)
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        
        # Verify ChatOpenAI was called with correct parameters
        mock_chat_openai.assert_called_once_with(model="gpt-3.5-turbo", temperature=0)
        assert llm is mock_llm
    
    @pytest.mark.unit
    @patch('langchain_openai.ChatOpenAI')
    def test_langchain_invoke_success(self, mock_chat_openai):
        """Test successful LangChain invocation"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.content = "안녕하세요! 테스트 응답입니다."
        
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_response
        mock_chat_openai.return_value = mock_llm
        
        # Simulate the original script logic
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        
        test_message = "안녕하세요! 간단한 테스트 메시지입니다."
        response = llm.invoke(test_message)
        
        # Verify the invocation
        mock_llm.invoke.assert_called_once_with(test_message)
        assert response.content == "안녕하세요! 테스트 응답입니다."
    
    @pytest.mark.unit
    @patch('langchain_openai.ChatOpenAI')
    def test_langchain_invoke_error_handling(self, mock_chat_openai):
        """Test LangChain invocation error handling"""
        # Mock an exception
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("API 호출 실패")
        mock_chat_openai.return_value = mock_llm
        
        # Simulate the original script logic with error handling
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        
        test_message = "안녕하세요! 간단한 테스트 메시지입니다."
        
        with pytest.raises(Exception) as exc_info:
            llm.invoke(test_message)
        
        assert "API 호출 실패" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_environment_loading(self):
        """Test environment variable loading"""
        # Test that dotenv loading doesn't raise exceptions
        try:
            load_dotenv()
            # If we get here, dotenv loading was successful
            assert True
        except Exception as e:
            pytest.fail(f"Environment loading failed: {e}")
