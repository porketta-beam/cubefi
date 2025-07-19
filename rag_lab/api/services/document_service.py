"""Document management service"""

import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from auto_rag.mod import ChromaDBManager, RawDataSyncManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DocumentService:
    def __init__(self):
        self.db_manager = ChromaDBManager()
        self.sync_manager = RawDataSyncManager()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current document database status"""
        db_status = self.db_manager.get_status()
        files_in_db = self.db_manager.get_files_in_db() if db_status["db_exists"] else []
        
        return {
            "db_exists": db_status["db_exists"],
            "document_count": db_status["document_count"],
            "db_path": db_status["db_path"],
            "embedding_model": db_status["embedding_model"],
            "files_in_db": files_in_db
        }
    
    def upload_document(self, filename: str, content: str, chunk_size: int = 500, chunk_overlap: int = 100) -> Dict[str, Any]:
        """Upload a document to the vector database"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name
            
            # Add document to database
            success = self.db_manager.add_document(temp_path, filename, chunk_size, chunk_overlap)
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            if success:
                document_count = self.db_manager.get_document_count()
                return {
                    "message": f"Document '{filename}' uploaded successfully",
                    "filename": filename,
                    "document_count": document_count,
                    "success": True
                }
            else:
                return {
                    "message": f"Failed to upload document '{filename}'",
                    "filename": filename,
                    "document_count": 0,
                    "success": False
                }
        except Exception as e:
            return {
                "message": f"Error uploading document: {str(e)}",
                "filename": filename,
                "document_count": 0,
                "success": False
            }
    
    def list_documents(self) -> Dict[str, Any]:
        """List all documents in the database"""
        try:
            db_status = self.db_manager.get_status()
            files_in_db = self.db_manager.get_files_in_db() if db_status["db_exists"] else []
            
            return {
                "files": files_in_db,
                "total_count": len(files_in_db),
                "document_count": db_status["document_count"]
            }
        except Exception as e:
            return {
                "files": [],
                "total_count": 0,
                "document_count": 0
            }
    
    def sync_documents(self, chunk_size: int = 500, chunk_overlap: int = 100) -> Dict[str, Any]:
        """Sync documents from raw_data folder"""
        try:
            # Get sync status before sync
            sync_status = self.sync_manager.compare_with_db(self.db_manager)
            
            # Perform sync
            success = self.sync_manager.sync_with_db(
                db_manager=self.db_manager,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            if success:
                total_documents = self.db_manager.get_document_count()
                return {
                    "message": "Documents synchronized successfully",
                    "new_files": sync_status["new_files"],
                    "existing_files": sync_status["existing_files"],
                    "orphaned_files": sync_status["orphaned_files"],
                    "total_documents": total_documents,
                    "success": True
                }
            else:
                return {
                    "message": "Document synchronization failed",
                    "new_files": [],
                    "existing_files": [],
                    "orphaned_files": [],
                    "total_documents": 0,
                    "success": False
                }
        except Exception as e:
            return {
                "message": f"Error during synchronization: {str(e)}",
                "new_files": [],
                "existing_files": [],
                "orphaned_files": [],
                "total_documents": 0,
                "success": False
            }
    
    def delete_database(self) -> Dict[str, Any]:
        """Delete the vector database"""
        try:
            success = self.db_manager.delete_db()
            return {
                "message": "Database deleted successfully" if success else "Failed to delete database",
                "success": success
            }
        except Exception as e:
            return {
                "message": f"Error deleting database: {str(e)}",
                "success": False
            }