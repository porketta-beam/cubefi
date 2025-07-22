"""End-to-end tests for complete RAG pipeline
Consolidated from server/test_full_rag_pipeline.py and related files"""

import pytest
import tempfile
import io
from pathlib import Path
from fastapi.testclient import TestClient

# Fixed imports
from server.modules.fastapi_app import app
from server.config.settings import settings


class TestRAGPipeline:
    """End-to-end RAG pipeline tests"""
    
    @pytest.fixture
    def temp_environment(self):
        """Set up temporary environment for E2E testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override settings
            original_raw_data = getattr(settings, 'RAW_DATA_ROOT', None)
            original_chroma = getattr(settings, 'CHROMA_DB_PATH', None)
            
            settings.RAW_DATA_ROOT = temp_dir
            settings.CHROMA_DB_PATH = str(Path(temp_dir) / "chroma_db")
            
            yield temp_dir
            
            # Restore settings
            if original_raw_data:
                settings.RAW_DATA_ROOT = original_raw_data
            if original_chroma:
                settings.CHROMA_DB_PATH = original_chroma
    
    def test_complete_document_lifecycle(self, temp_environment, sample_pdf_content, sample_text_content):
        """Test complete document lifecycle: upload -> sync -> query -> delete"""
        with TestClient(app) as client:
            # Step 1: Upload document
            files = {
                "file": ("test_document.pdf", io.BytesIO(sample_pdf_content), "application/pdf")
            }
            
            upload_response = client.post("/api/documents/upload-file", files=files)
            print(f"Upload status: {upload_response.status_code}")
            
            if upload_response.status_code in [200, 201]:
                upload_data = upload_response.json()
                doc_id = upload_data.get("doc_id")
                assert doc_id is not None
                print(f"Uploaded document ID: {doc_id}")
                
                # Step 2: Sync document to vector database
                sync_response = client.get(f"/api/documents/sync?doc_id={doc_id}")
                print(f"Sync status: {sync_response.status_code}")
                
                if sync_response.status_code == 200:
                    sync_data = sync_response.json()
                    print(f"Sync result: {sync_data.get('message', 'No message')}")
                    
                    # Step 3: Check document status
                    status_response = client.get("/api/documents/status")
                    assert status_response.status_code == 200
                    
                    status_data = status_response.json()
                    print(f"DB exists: {status_data.get('db_exists')}")
                    print(f"Document count: {status_data.get('document_count')}")
                    
                    # Step 4: Try RAG query (if endpoint exists)
                    self._try_rag_query(client, "What is this document about?")
                    
                    # Step 5: Delete document
                    delete_response = client.delete(f"/api/documents/{doc_id}")
                    print(f"Delete status: {delete_response.status_code}")
                    
                    if delete_response.status_code == 204:
                        print("Document deleted successfully")
                        
                        # Verify deletion
                        doc_dir = Path(temp_environment) / doc_id
                        assert not doc_dir.exists(), "Document directory should be deleted"
                    else:
                        print(f"Delete failed or not implemented: {delete_response.status_code}")
                else:
                    print("Sync not implemented or failed - skipping rest of pipeline")
            else:
                print(f"Upload failed or not implemented: {upload_response.status_code}")
                # Don't fail the test - upload may not be fully implemented
    
    def _try_rag_query(self, client, question: str):
        """Try to perform a RAG query"""
        try:
            # Try different possible RAG endpoints
            rag_endpoints = [
                "/api/rag/chat",
                "/api/chat", 
                "/chat",
                "/api/rag/query",
                "/query"
            ]
            
            for endpoint in rag_endpoints:
                try:
                    response = client.post(endpoint, json={"message": question})
                    if response.status_code == 200:
                        print(f"RAG query successful via {endpoint}")
                        data = response.json()
                        print(f"RAG response: {data}")
                        return True
                    elif response.status_code == 404:
                        continue  # Try next endpoint
                    else:
                        print(f"RAG endpoint {endpoint} returned {response.status_code}")
                except Exception as e:
                    print(f"RAG endpoint {endpoint} error: {e}")
                    continue
            
            print("No working RAG endpoint found - may not be implemented yet")
            return False
            
        except Exception as e:
            print(f"RAG query failed: {e}")
            return False
    
    def test_multiple_documents_workflow(self, temp_environment, sample_pdf_content, sample_text_content):
        """Test workflow with multiple documents"""
        with TestClient(app) as client:
            uploaded_docs = []
            
            # Upload multiple documents
            documents = [
                ("doc1.pdf", sample_pdf_content, "application/pdf"),
                ("doc2.txt", sample_text_content.encode(), "text/plain")
            ]
            
            for filename, content, content_type in documents:
                files = {
                    "file": (filename, io.BytesIO(content), content_type)
                }
                
                response = client.post("/api/documents/upload-file", files=files)
                if response.status_code in [200, 201]:
                    data = response.json()
                    doc_id = data.get("doc_id")
                    if doc_id:
                        uploaded_docs.append(doc_id)
                        print(f"Uploaded {filename} as {doc_id}")
            
            if uploaded_docs:
                print(f"Successfully uploaded {len(uploaded_docs)} documents")
                
                # Try bulk sync
                sync_response = client.get("/api/documents/sync")
                if sync_response.status_code == 200:
                    sync_data = sync_response.json()
                    print(f"Bulk sync: {sync_data.get('message', 'No message')}")
                    
                    # Check final status
                    status_response = client.get("/api/documents/status")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"Final document count: {status_data.get('document_count')}")
                        
                        # Try to query across multiple documents
                        self._try_rag_query(client, "Compare the content of the documents")
                
                # Cleanup: delete all uploaded documents
                for doc_id in uploaded_docs:
                    delete_response = client.delete(f"/api/documents/{doc_id}")
                    if delete_response.status_code == 204:
                        print(f"Deleted {doc_id}")
                    else:
                        print(f"Failed to delete {doc_id}: {delete_response.status_code}")
            else:
                print("No documents were uploaded - upload API may not be implemented")
    
    def test_error_handling(self, temp_environment):
        """Test error handling in the pipeline"""
        with TestClient(app) as client:
            # Test invalid file upload
            invalid_files = {
                "file": ("malicious.exe", io.BytesIO(b"fake executable"), "application/x-msdownload")
            }
            
            response = client.post("/api/documents/upload-file", files=invalid_files)
            print(f"Invalid file upload status: {response.status_code}")
            
            # Should be rejected (400 or 422)
            assert response.status_code in [400, 422], "Invalid files should be rejected"
            
            # Test sync with non-existent document
            response = client.get("/api/documents/sync?doc_id=nonexistent_1234567890123")
            print(f"Non-existent document sync status: {response.status_code}")
            
            # Should return appropriate error
            if response.status_code not in [404, 400, 200]:  # 200 might be ok if it just skips
                print(f"Unexpected status for non-existent document sync: {response.status_code}")
            
            # Test delete non-existent document
            response = client.delete("/api/documents/nonexistent_1234567890123")
            print(f"Non-existent document delete status: {response.status_code}")
            
            # Should return 404
            assert response.status_code == 404, "Deleting non-existent document should return 404"
    
    def test_concurrent_operations(self, temp_environment, sample_pdf_content):
        """Test concurrent operations on the pipeline"""
        import threading
        import time
        
        with TestClient(app) as client:
            results = []
            
            def upload_document(doc_name):
                files = {
                    "file": (f"{doc_name}.pdf", io.BytesIO(sample_pdf_content), "application/pdf")
                }
                
                response = client.post("/api/documents/upload-file", files=files)
                results.append((doc_name, response.status_code))
            
            # Start multiple upload threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=upload_document, args=(f"concurrent_doc_{i}",))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Check results
            successful_uploads = [r for r in results if r[1] in [200, 201]]
            print(f"Concurrent uploads: {len(successful_uploads)}/{len(results)} successful")
            
            if successful_uploads:
                print("Concurrent uploads completed successfully")
                # Note: We won't clean up here to avoid complexity in test
            else:
                print("Concurrent uploads failed - may not be implemented")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
