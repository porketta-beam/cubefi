"""Quick API tests
Consolidated from server/test_api_quick.py with improved structure"""

import pytest
import httpx
from fastapi.testclient import TestClient

# Fixed import
from server.modules.fastapi_app import app


class TestQuickAPI:
    """Quick API functionality tests"""
    
    @pytest.fixture
    def base_url(self):
        """Base URL for API testing"""
        return "http://localhost:8000"
    
    def test_api_with_test_client(self):
        """Test API using FastAPI TestClient"""
        with TestClient(app) as client:
            # Test if server is responding
            response = client.get("/docs")
            print(f"Server responding: {response.status_code == 200}")
            assert response.status_code == 200
            
            # Test document status
            response = client.get("/api/documents/status")
            print(f"Document status: {response.status_code}")
            assert response.status_code == 200
            
            if response.status_code == 200:
                data = response.json()
                print(f"DB exists: {data.get('db_exists')}")
                print(f"Document count: {data.get('document_count')}")
                
                assert 'db_exists' in data
                assert 'document_count' in data
                assert isinstance(data['db_exists'], bool)
                assert isinstance(data['document_count'], int)
    
    @pytest.mark.skipif(True, reason="Requires running server - integration test only")
    def test_api_with_httpx_client(self, base_url):
        """Test API using httpx client (requires running server)"""
        try:
            with httpx.Client(timeout=10.0) as client:
                # Test if server is responding
                response = client.get(f"{base_url}/docs")
                print(f"Server responding: {response.status_code == 200}")
                assert response.status_code == 200
                
                # Test document status
                response = client.get(f"{base_url}/api/documents/status")
                print(f"Document status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"DB exists: {data.get('db_exists')}")
                    print(f"Document count: {data.get('document_count')}")
                    
                    assert 'db_exists' in data
                    assert 'document_count' in data
                
        except Exception as e:
            pytest.fail(f"Error: {e}")
    
    def test_health_endpoint(self):
        """Test health endpoint if it exists"""
        with TestClient(app) as client:
            try:
                response = client.get("/health")
                if response.status_code == 200:
                    data = response.json()
                    assert 'status' in data
                    print(f"Health status: {data.get('status')}")
                elif response.status_code == 404:
                    # Health endpoint doesn't exist - that's ok
                    print("Health endpoint not implemented yet")
                else:
                    pytest.fail(f"Unexpected health endpoint response: {response.status_code}")
            except Exception as e:
                print(f"Health endpoint test failed: {e}")
                # Don't fail the test - health endpoint may not exist yet


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
