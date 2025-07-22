"""Chunk configuration validation utilities"""

import re
from typing import List, Tuple
from pydantic import ValidationError
from modules.api.models.document_config import DocumentConfigModel, ConfigValidationError

class ChunkConfigValidator:
    """Validator for chunk configuration parameters"""
    
    MIN_CHUNK_SIZE = 100
    MAX_CHUNK_SIZE = 2000
    MAX_OVERLAP_RATIO = 0.5
    RECOMMENDED_MIN_CHUNK_SIZE = 200
    RECOMMENDED_MAX_CHUNK_SIZE = 1000
    RECOMMENDED_OVERLAP_RATIO = 0.2
    
    @classmethod
    def validate_config(cls, config: DocumentConfigModel) -> Tuple[bool, List[ConfigValidationError], List[str]]:
        """
        Validate document configuration
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        chunk_size = config.chunk.chunk_size
        overlap_ratio = config.chunk.overlap_ratio
        
        # Validate chunk size
        if chunk_size < cls.MIN_CHUNK_SIZE:
            errors.append(ConfigValidationError(
                field="chunk_size",
                message=f"Chunk size must be at least {cls.MIN_CHUNK_SIZE}",
                code="CHUNK_SIZE_TOO_SMALL"
            ))
        elif chunk_size > cls.MAX_CHUNK_SIZE:
            errors.append(ConfigValidationError(
                field="chunk_size",
                message=f"Chunk size must not exceed {cls.MAX_CHUNK_SIZE}",
                code="CHUNK_SIZE_TOO_LARGE"
            ))
        
        # Validate overlap ratio
        if overlap_ratio > cls.MAX_OVERLAP_RATIO:
            errors.append(ConfigValidationError(
                field="overlap_ratio",
                message=f"Overlap ratio must not exceed {cls.MAX_OVERLAP_RATIO}",
                code="OVERLAP_RATIO_TOO_LARGE"
            ))
        
        # Calculate overlap size and validate
        overlap_size = int(chunk_size * overlap_ratio)
        if overlap_size >= chunk_size:
            errors.append(ConfigValidationError(
                field="overlap_ratio",
                message="Overlap size cannot be greater than or equal to chunk size",
                code="OVERLAP_SIZE_INVALID"
            ))
        
        # Generate warnings for suboptimal configurations
        if chunk_size < cls.RECOMMENDED_MIN_CHUNK_SIZE:
            warnings.append(f"Chunk size {chunk_size} is below recommended minimum {cls.RECOMMENDED_MIN_CHUNK_SIZE}")
        elif chunk_size > cls.RECOMMENDED_MAX_CHUNK_SIZE:
            warnings.append(f"Chunk size {chunk_size} is above recommended maximum {cls.RECOMMENDED_MAX_CHUNK_SIZE}")
        
        if overlap_ratio < 0.05:
            warnings.append("Very low overlap ratio may result in poor context continuity")
        elif overlap_ratio > cls.RECOMMENDED_OVERLAP_RATIO:
            warnings.append(f"Overlap ratio {overlap_ratio} is above recommended maximum {cls.RECOMMENDED_OVERLAP_RATIO}")
        
        return len(errors) == 0, errors, warnings
    
    @classmethod
    def validate_doc_id(cls, doc_id: str) -> bool:
        """
        Validate document ID format
        
        Args:
            doc_id: Document identifier
            
        Returns:
            True if valid, False otherwise
        """
        # Pattern: alphanumeric, underscore, hyphen, followed by timestamp
        pattern = r'^[a-zA-Z0-9_-]+_\d{13}$'
        return bool(re.match(pattern, doc_id))
    
    @classmethod
    def sanitize_doc_id(cls, doc_id: str) -> str:
        """
        Sanitize document ID to prevent path traversal
        
        Args:
            doc_id: Document identifier
            
        Returns:
            Sanitized document ID
        """
        # Remove any path separators and dangerous characters
        sanitized = re.sub(r'[^\w\-_]', '', doc_id)
        return sanitized[:100]  # Limit length