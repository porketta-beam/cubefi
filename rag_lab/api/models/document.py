"""Document API models"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class DocumentUploadRequest(BaseModel):
    filename: str
    content: str
    chunk_size: int = 500
    chunk_overlap: int = 100

class DocumentUploadResponse(BaseModel):
    message: str
    filename: str
    document_count: int
    success: bool

class DocumentListResponse(BaseModel):
    files: List[str]
    total_count: int
    document_count: int

class DocumentSyncRequest(BaseModel):
    chunk_size: int = 500
    chunk_overlap: int = 100

class DocumentSyncResponse(BaseModel):
    message: str
    new_files: List[str]
    existing_files: List[str]
    orphaned_files: List[str]
    total_documents: int
    success: bool

class DocumentStatusResponse(BaseModel):
    db_exists: bool
    document_count: int
    db_path: str
    embedding_model: str
    files_in_db: List[str]