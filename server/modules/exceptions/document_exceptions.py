"""Document-related custom exceptions"""

class DocumentError(Exception):
    """Base exception for document operations"""
    pass

class DocumentNotFoundError(DocumentError):
    """Document not found error"""
    def __init__(self, doc_id: str):
        self.doc_id = doc_id
        super().__init__(f"Document not found: {doc_id}")

class ConfigurationError(DocumentError):
    """Configuration validation or processing error"""
    def __init__(self, message: str, details: dict = None):
        self.details = details or {}
        super().__init__(message)

class DocumentCreationError(DocumentError):
    """Document creation failed"""
    pass

class DocumentDeletionError(DocumentError):
    """Document deletion failed"""
    pass

class DocumentProcessingError(DocumentError):
    """Document processing failed"""
    pass

class ValidationError(DocumentError):
    """Validation failed"""
    def __init__(self, message: str, errors: list = None):
        self.errors = errors or []
        super().__init__(message)