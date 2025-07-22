"""Document metadata models"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class DocumentMetadata(BaseModel):
    """Document metadata model"""
    original_filename: str = Field(..., description="Original filename when uploaded")
    content_type: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    upload_timestamp: datetime = Field(default_factory=datetime.now, description="When the file was uploaded")
    file_hash: str = Field(..., description="SHA-256 hash of the file content")
    page_count: Optional[int] = Field(default=None, description="Number of pages (PDF only)")
    language: Optional[str] = Field(default=None, description="Detected language")
    extracted_text_preview: Optional[str] = Field(default=None, description="First 1000 characters preview")
    author: Optional[str] = Field(default=None, description="Document author (if available)")
    title: Optional[str] = Field(default=None, description="Document title (if available)")
    encoding: Optional[str] = Field(default=None, description="Text encoding (for text files)")
    has_images: Optional[bool] = Field(default=None, description="Whether document contains images")
    
class UploadSession(BaseModel):
    """Upload session tracking model"""
    upload_id: str = Field(..., description="Unique upload session identifier")
    total_bytes: int = Field(..., ge=0, description="Total bytes to upload")
    received_bytes: int = Field(default=0, ge=0, description="Bytes received so far")
    status: str = Field(default="uploading", description="Upload status")
    started_at: datetime = Field(default_factory=datetime.now, description="Upload start time")
    finished_at: Optional[datetime] = Field(default=None, description="Upload completion time")
    doc_id: Optional[str] = Field(default=None, description="Generated document ID")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")

class DocumentUploadResponse(BaseModel):
    """Response for document upload"""
    message: str
    doc_id: str
    upload_id: str
    status: str = "uploaded"
    processing: bool = False
    estimated_processing_time: Optional[str] = None
    file_size: int
    content_type: str

class FileValidationError(Exception):
    """File validation error"""
    pass

class DocumentCreationError(Exception):
    """Document creation error"""
    pass