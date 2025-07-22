"""Exception definitions"""

from .document_exceptions import (
    DocumentError,
    DocumentNotFoundError,
    ConfigurationError,
    DocumentCreationError,
    DocumentDeletionError,
    DocumentProcessingError,
    ValidationError
)

__all__ = [
    'DocumentError',
    'DocumentNotFoundError',
    'ConfigurationError',
    'DocumentCreationError',
    'DocumentDeletionError',
    'DocumentProcessingError',
    'ValidationError'
]