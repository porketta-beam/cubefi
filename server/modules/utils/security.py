"""Security utilities for document operations"""

import os
import re
from pathlib import Path
from typing import Optional
import structlog

logger = structlog.get_logger(__name__)

class PathTraversalGuard:
    """Guards against path traversal attacks"""
    
    @staticmethod
    def validate_document_path(doc_id: str, allowed_root: str) -> bool:
        """
        Validate that document path is within allowed root directory
        
        Args:
            doc_id: Document identifier
            allowed_root: Root directory path that contains documents
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Normalize and resolve paths
            allowed_root_path = Path(allowed_root).resolve()
            doc_path = Path(allowed_root) / doc_id
            resolved_doc_path = doc_path.resolve()
            
            # Check if resolved path is within allowed root
            try:
                resolved_doc_path.relative_to(allowed_root_path)
                return True
            except ValueError:
                logger.warning(
                    "Path traversal attempt detected",
                    doc_id=doc_id,
                    allowed_root=allowed_root,
                    resolved_path=str(resolved_doc_path)
                )
                return False
                
        except Exception as e:
            logger.error(
                "Error validating document path",
                doc_id=doc_id,
                allowed_root=allowed_root,
                error=str(e)
            )
            return False
    
    @staticmethod
    def is_system_path(path: str) -> bool:
        """
        Check if path points to system directories
        
        Args:
            path: Path to check
            
        Returns:
            True if system path, False otherwise
        """
        system_patterns = [
            r'^/etc/',
            r'^/usr/',
            r'^/var/',
            r'^/root/',
            r'^/home/[^/]+/\.',
            r'^C:\\Windows\\',
            r'^C:\\Program Files',
            r'^C:\\Users\\[^\\]+\\AppData',
        ]
        
        for pattern in system_patterns:
            if re.match(pattern, path, re.IGNORECASE):
                return True
        return False

class DocumentSecurityService:
    """Security service for document operations"""
    
    # Valid document ID pattern
    DOC_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+_\d{13}$')
    
    def __init__(self, raw_data_root: str):
        self.raw_data_root = Path(raw_data_root).resolve()
        
    def validate_document_path(self, doc_id: str) -> bool:
        """Validate document path security"""
        return PathTraversalGuard.validate_document_path(doc_id, str(self.raw_data_root))
    
    def validate_document_id(self, doc_id: str) -> bool:
        """
        Validate document ID format
        
        Args:
            doc_id: Document ID to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not doc_id or len(doc_id) > 100:  # Reasonable length limit
            return False
        
        return bool(self.DOC_ID_PATTERN.match(doc_id))
    
    def audit_config_operation(self, operation: str, doc_id: str, user_id: Optional[str] = None, 
                             success: bool = True, error: Optional[str] = None):
        """Audit document configuration operations"""
        logger.info(
            "Document config operation audit",
            operation=operation,
            doc_id=doc_id,
            user_id=user_id,
            success=success,
            error=error,
            audit_event=True
        )
    
    def audit_delete_operation(self, doc_id: str, user_id: Optional[str] = None, 
                             success: bool = True, error: Optional[str] = None,
                             files_deleted: int = 0, vector_removed: bool = False):
        """
        Audit document deletion operations
        
        Args:
            doc_id: Document ID being deleted
            user_id: User performing the deletion
            success: Whether deletion was successful
            error: Error message if failed
            files_deleted: Number of files deleted
            vector_removed: Whether vector embeddings were removed
        """
        logger.info(
            "Document delete operation audit",
            operation="delete_document",
            doc_id=doc_id,
            user_id=user_id or "system",
            success=success,
            error=error,
            files_deleted=files_deleted,
            vector_removed=vector_removed,
            audit_event=True
        )

# Custom security exceptions
class SecurityError(Exception):
    """Base security exception"""
    pass

class DirectoryTraversalError(SecurityError):
    """Directory traversal attempt detected"""
    pass

class InvalidDocumentIdError(SecurityError):
    """Invalid document ID format"""
    pass

class DocumentNotFoundError(Exception):
    """Document not found"""
    pass

class DocumentDeletionError(Exception):
    """Document deletion failed"""
    pass

class PermissionDeniedError(SecurityError):
    """Permission denied for operation"""
    pass