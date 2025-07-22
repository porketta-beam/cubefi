"""Document configuration models"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime

class DocumentChunkOptions(BaseModel):
    """Document chunking configuration options"""
    chunk_size: int = Field(default=512, ge=100, le=2000, description="Size of text chunks for processing")
    overlap_ratio: float = Field(default=0.1, ge=0.0, le=0.5, description="Overlap ratio between chunks")
    
    @field_validator('overlap_ratio')
    @classmethod
    def validate_overlap_ratio(cls, v, info):
        """Validate overlap ratio is reasonable"""
        if 'chunk_size' in info.data:
            chunk_size = info.data['chunk_size']
            overlap_size = int(chunk_size * v)
            if overlap_size >= chunk_size:
                raise ValueError("Overlap size cannot be greater than or equal to chunk size")
        return v

class DocumentConfigModel(BaseModel):
    """Complete document configuration model"""
    model_config = ConfigDict(extra="forbid")
    
    chunk: DocumentChunkOptions = Field(default_factory=DocumentChunkOptions)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional document metadata")
    
class DocumentConfigUpdate(BaseModel):
    """Document configuration update request"""
    chunk_size: Optional[int] = Field(default=None, ge=100, le=2000)
    chunk_overlap: Optional[int] = Field(default=None, ge=0, le=1000)
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "chunk_size": 800,
                "chunk_overlap": 200,
                "metadata": {
                    "author": "국세청",
                    "category": "세법",
                    "version": "2024"
                }
            }
        }
    }

class ConfigUpdateResponse(BaseModel):
    """Response for configuration update"""
    status: str = "updated"
    version: str
    warnings: list[str] = []
    doc_id: str
    
class ConfigValidationError(BaseModel):
    """Configuration validation error details"""
    field: str
    message: str
    code: str

class ConfigValidationResponse(BaseModel):
    """Configuration validation response"""
    valid: bool
    errors: list[ConfigValidationError] = []
    warnings: list[str] = []