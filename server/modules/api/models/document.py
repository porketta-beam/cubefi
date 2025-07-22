"""Document API models"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class DocumentUploadRequest(BaseModel):
    filename: str
    content: str
    chunk_size: int = 500
    chunk_overlap: int = 100
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "filename": "tax_law_2024.pdf",
                "content": "소득세법 제94조의5(주식등의 양도소득에 대한 과세특례) 개인이 받은...",
                "chunk_size": 800,
                "chunk_overlap": 200
            }
        }
    }

class DocumentUploadResponse(BaseModel):
    message: str
    filename: str
    document_count: int
    success: bool
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "문서가 성공적으로 업로드되고 벡터 데이터베이스에 저장되었습니다.",
                "filename": "tax_law_2024.pdf",
                "document_count": 45,
                "success": True
            }
        }
    }

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

class DocumentDeleteResponse(BaseModel):
    """Response for document deletion"""
    message: str
    doc_id: str
    success: bool
    files_deleted: int = 0
    vector_removed: bool = False
    backup_created: bool = False

class DocumentDeleteRequest(BaseModel):
    """Request for document deletion"""
    confirm: bool = False
    create_backup: bool = True

class SyncResponse(BaseModel):
    """Response for document synchronization"""
    success: bool
    message: str
    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    processing_time: float = 0.0
    doc_id: Optional[str] = None  # 단일 문서 sync 시
    chunks_created: Optional[int] = None  # 단일 문서 sync 시