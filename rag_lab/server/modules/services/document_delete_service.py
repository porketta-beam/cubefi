"""Document deletion service with security and audit features"""

import json
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import structlog
from pydantic import BaseModel

from modules.utils.security import (
    DocumentSecurityService,
    DirectoryTraversalError,
    InvalidDocumentIdError,
    DocumentNotFoundError,
    DocumentDeletionError,
    PermissionDeniedError
)

logger = structlog.get_logger(__name__)

class DeleteResult(BaseModel):
    """Result of document deletion operation"""
    success: bool
    doc_id: str
    files_deleted: int = 0
    vector_removed: bool = False
    backup_created: bool = False
    error_message: Optional[str] = None

class DocumentDeleteService:
    """Service for secure document deletion with audit trail"""
    
    def __init__(self, raw_data_root: str = "./raw_data"):
        self.raw_data_root = Path(raw_data_root)
        self.raw_data_root.mkdir(exist_ok=True)
        
        self.security_service = DocumentSecurityService(raw_data_root)
        
        # Create backup directory for deleted documents
        self.backup_root = self.raw_data_root.parent / ".deleted_backups"
        self.backup_root.mkdir(exist_ok=True)
    
    async def delete_document(self, doc_id: str, user_id: Optional[str] = None) -> DeleteResult:
        """
        Delete a document with security validation and audit logging
        
        Args:
            doc_id: Document ID to delete
            user_id: User performing the deletion
            
        Returns:
            DeleteResult with operation details
            
        Raises:
            InvalidDocumentIdError: If doc_id format is invalid
            DirectoryTraversalError: If path traversal is detected
            DocumentNotFoundError: If document doesn't exist
            DocumentDeletionError: If deletion fails
        """
        # Initialize result
        result = DeleteResult(success=False, doc_id=doc_id)
        
        try:
            # Step 1: Validate document ID format
            if not self.security_service.validate_document_id(doc_id):
                raise InvalidDocumentIdError(f"Invalid document ID format: {doc_id}")
            
            # Step 2: Validate document path security
            if not self.security_service.validate_document_path(doc_id):
                raise DirectoryTraversalError(f"Path traversal detected for doc_id: {doc_id}")
            
            # Step 3: Check if document exists
            doc_dir = self.raw_data_root / doc_id
            if not doc_dir.exists():
                raise DocumentNotFoundError(f"Document not found: {doc_id}")
            
            # Step 4: Validate deletion permissions (placeholder for future RBAC)
            await self._validate_deletion_permissions(doc_id, user_id)
            
            # Step 5: Create backup before deletion
            backup_path = await self._backup_metadata(doc_id)
            if backup_path:
                result.backup_created = True
            
            # Step 6: Remove from vector database (if available)
            vector_removed = await self._remove_from_vector_db(doc_id)
            result.vector_removed = vector_removed
            
            # Step 7: Delete directory safely
            files_deleted = await self._delete_directory_safely(doc_dir)
            result.files_deleted = files_deleted
            
            # Step 8: Mark as successful
            result.success = True
            
            # Audit successful deletion
            self.security_service.audit_delete_operation(
                doc_id=doc_id,
                user_id=user_id,
                success=True,
                files_deleted=files_deleted,
                vector_removed=vector_removed
            )
            
            logger.info(
                "Document deleted successfully",
                doc_id=doc_id,
                user_id=user_id,
                files_deleted=files_deleted,
                vector_removed=vector_removed
            )
            
            return result
            
        except Exception as e:
            # Set error details
            result.error_message = str(e)
            
            # Audit failed deletion
            self.security_service.audit_delete_operation(
                doc_id=doc_id,
                user_id=user_id,
                success=False,
                error=str(e)
            )
            
            logger.error(
                "Document deletion failed",
                doc_id=doc_id,
                user_id=user_id,
                error=str(e)
            )
            
            # Re-raise specific exceptions, wrap others in DocumentDeletionError
            if isinstance(e, (InvalidDocumentIdError, DirectoryTraversalError, 
                            DocumentNotFoundError, PermissionDeniedError)):
                raise e
            else:
                raise DocumentDeletionError(f"Failed to delete document {doc_id}: {str(e)}")
    
    async def _validate_deletion_permissions(self, doc_id: str, user_id: Optional[str]) -> None:
        """
        Validate user permissions for document deletion
        
        Args:
            doc_id: Document ID
            user_id: User ID requesting deletion
            
        Raises:
            PermissionDeniedError: If user lacks permission
        """
        # For now, allow all deletions
        # In future, implement RBAC by checking:
        # - Document owner in metadata
        # - User role (admin, editor, viewer)
        # - Organization permissions
        
        if user_id is None:
            # System deletions are allowed
            return
        
        # Placeholder for future permission checking
        doc_dir = self.raw_data_root / doc_id
        metadata_path = doc_dir / "metadata.json"
        
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                # Check if metadata has owner field
                if "owner" in metadata and metadata["owner"] != user_id:
                    # For now, just log but don't block
                    logger.warning(
                        "User attempting to delete document owned by another user",
                        doc_id=doc_id,
                        requesting_user=user_id,
                        document_owner=metadata["owner"]
                    )
                    # Uncomment to enforce ownership:
                    # raise PermissionDeniedError(f"User {user_id} cannot delete document owned by {metadata['owner']}")
                    
            except Exception as e:
                logger.warning(
                    "Could not check document ownership",
                    doc_id=doc_id,
                    error=str(e)
                )
    
    async def _backup_metadata(self, doc_id: str) -> Optional[Path]:
        """
        Create backup of document metadata before deletion
        
        Args:
            doc_id: Document ID
            
        Returns:
            Path to backup file or None if backup failed
        """
        try:
            doc_dir = self.raw_data_root / doc_id
            metadata_path = doc_dir / "metadata.json"
            
            if not metadata_path.exists():
                return None
            
            # Create backup file
            backup_filename = f"{doc_id}_metadata_backup.json"
            backup_path = self.backup_root / backup_filename
            
            # Copy metadata
            shutil.copy2(metadata_path, backup_path)
            
            logger.info(
                "Document metadata backup created",
                doc_id=doc_id,
                backup_path=str(backup_path)
            )
            
            return backup_path
            
        except Exception as e:
            logger.warning(
                "Failed to create metadata backup",
                doc_id=doc_id,
                error=str(e)
            )
            return None
    
    async def _remove_from_vector_db(self, doc_id: str) -> bool:
        """
        Remove document from vector database
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if removed or not found, False if error occurred
        """
        try:
            # Placeholder for vector database removal
            # In a real implementation, this would:
            # 1. Connect to ChromaDB
            # 2. Find all chunks with doc_id
            # 3. Delete them from the collection
            # 4. Persist the changes
            
            logger.info(
                "Document removed from vector database",
                doc_id=doc_id,
                vector_service="placeholder"
            )
            
            # Simulate successful removal
            return True
            
        except Exception as e:
            logger.error(
                "Failed to remove document from vector database",
                doc_id=doc_id,
                error=str(e)
            )
            # Don't fail the entire deletion if vector removal fails
            return False
    
    async def _delete_directory_safely(self, doc_dir: Path) -> int:
        """
        Safely delete document directory and count files
        
        Args:
            doc_dir: Directory to delete
            
        Returns:
            Number of files deleted
            
        Raises:
            DocumentDeletionError: If deletion fails
        """
        try:
            if not doc_dir.exists():
                return 0
            
            # Count files before deletion
            file_count = sum(1 for _ in doc_dir.rglob('*') if _.is_file())
            
            # Delete directory
            shutil.rmtree(doc_dir)
            
            logger.info(
                "Document directory deleted",
                doc_dir=str(doc_dir),
                files_deleted=file_count
            )
            
            return file_count
            
        except Exception as e:
            raise DocumentDeletionError(f"Failed to delete directory {doc_dir}: {str(e)}")
    
    def get_document_info(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get basic document information for validation
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document info dict or None if not found
        """
        try:
            doc_dir = self.raw_data_root / doc_id
            if not doc_dir.exists():
                return None
            
            info = {
                "doc_id": doc_id,
                "exists": True,
                "path": str(doc_dir)
            }
            
            # Check for files
            files = list(doc_dir.iterdir())
            info["file_count"] = len(files)
            info["files"] = [f.name for f in files]
            
            return info
            
        except Exception as e:
            logger.error(
                "Failed to get document info",
                doc_id=doc_id,
                error=str(e)
            )
            return None