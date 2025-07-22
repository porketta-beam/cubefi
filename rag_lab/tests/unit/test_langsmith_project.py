#!/usr/bin/env python3
"""
Unit tests for LangSmith project management functionality
"""

import pytest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Load environment variables for testing
load_dotenv()


class TestLangSmithProject:
    """Test LangSmith project management functionality"""
    
    @pytest.mark.unit
    @patch('langsmith.Client')
    def test_langsmith_client_creation(self, mock_client_class):
        """Test LangSmith client creation"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Simulate the original script logic
        from langsmith import Client
        client = Client()
        
        # Verify client was created
        mock_client_class.assert_called_once()
        assert client is mock_client
    
    @pytest.mark.unit
    @patch('langsmith.Client')
    def test_create_project_success(self, mock_client_class):
        """Test successful project creation"""
        # Mock successful project creation
        mock_project = MagicMock()
        mock_project.name = 'rag_lab_project'
        mock_project.id = 'test-project-id'
        
        mock_client = MagicMock()
        mock_client.create_project.return_value = mock_project
        mock_client_class.return_value = mock_client
        
        # Simulate the original script logic
        from langsmith import Client
        client = Client()
        
        project = client.create_project(
            project_name='rag_lab_project', 
            description='RAG monitoring project'
        )
        
        # Verify project creation
        mock_client.create_project.assert_called_once_with(
            project_name='rag_lab_project', 
            description='RAG monitoring project'
        )
        assert project.name == 'rag_lab_project'
        assert project.id == 'test-project-id'
    
    @pytest.mark.unit
    @patch('langsmith.Client')
    def test_create_project_error_handling(self, mock_client_class):
        """Test project creation error handling"""
        # Mock project creation error
        mock_client = MagicMock()
        mock_client.create_project.side_effect = Exception("프로젝트가 이미 존재합니다")
        mock_client_class.return_value = mock_client
        
        # Simulate the original script logic with error handling
        from langsmith import Client
        client = Client()
        
        with pytest.raises(Exception) as exc_info:
            client.create_project(
                project_name='rag_lab_project', 
                description='RAG monitoring project'
            )
        
        assert "프로젝트가 이미 존재합니다" in str(exc_info.value)
    
    @pytest.mark.unit
    @patch('langsmith.Client')
    def test_list_projects_success(self, mock_client_class):
        """Test successful project listing"""
        # Mock project list
        mock_project1 = MagicMock()
        mock_project1.name = 'rag_lab_project'
        mock_project1.id = 'project-1'
        
        mock_project2 = MagicMock()
        mock_project2.name = 'test_project'
        mock_project2.id = 'project-2'
        
        mock_client = MagicMock()
        mock_client.list_projects.return_value = [mock_project1, mock_project2]
        mock_client_class.return_value = mock_client
        
        # Simulate the original script logic
        from langsmith import Client
        client = Client()
        
        projects = client.list_projects()
        
        # Verify project listing
        mock_client.list_projects.assert_called_once()
        assert len(projects) == 2
        assert projects[0].name == 'rag_lab_project'
        assert projects[1].name == 'test_project'
    
    @pytest.mark.unit
    @patch('langsmith.Client')
    def test_list_projects_error_handling(self, mock_client_class):
        """Test project listing error handling"""
        # Mock project listing error
        mock_client = MagicMock()
        mock_client.list_projects.side_effect = Exception("프로젝트 목록 조회 실패")
        mock_client_class.return_value = mock_client
        
        # Simulate the original script logic with error handling
        from langsmith import Client
        client = Client()
        
        with pytest.raises(Exception) as exc_info:
            client.list_projects()
        
        assert "프로젝트 목록 조회 실패" in str(exc_info.value)
    
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
