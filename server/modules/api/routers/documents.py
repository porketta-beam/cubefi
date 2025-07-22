"""Document management API routes"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Path
from typing import Optional
from modules.api.models.document import (
    DocumentUploadRequest, DocumentUploadResponse, 
    DocumentListResponse, DocumentSyncRequest, DocumentSyncResponse,
    DocumentStatusResponse, DocumentDeleteResponse, SyncResponse
)
from modules.api.models.document_metadata import (
    DocumentUploadResponse as NewDocumentUploadResponse,
    FileValidationError,
    DocumentCreationError
)
from modules.api.services.document_service import DocumentService
from modules.services.document_lifecycle_service import DocumentLifecycleService
from modules.services.document_delete_service import DocumentDeleteService
from modules.utils.security import (
    DirectoryTraversalError,
    InvalidDocumentIdError,
    DocumentNotFoundError,
    DocumentDeletionError,
    PermissionDeniedError
)
from config.settings import settings

router = APIRouter(prefix="/api/documents", tags=["documents"])
document_service = DocumentService()
lifecycle_service = DocumentLifecycleService()
delete_service = DocumentDeleteService()

@router.get("/status", response_model=DocumentStatusResponse)
async def get_document_status():
    """Get current document database status"""
    try:
        status = document_service.get_status()
        return DocumentStatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list", response_model=DocumentListResponse)
async def list_documents():
    """List all documents in the database"""
    try:
        result = document_service.list_documents()
        return DocumentListResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 진짜 채팅처럼 텍스트로 문서를 올리는 방법.
# 쓸 일 없을 듯?
# @router.post("/upload", response_model=DocumentUploadResponse)
# async def upload_document(request: DocumentUploadRequest):
#     """Upload a document to the vector database"""
#     try:
#         result = document_service.upload_document(
#             request.filename,
#             request.content,
#             request.chunk_size,
#             request.chunk_overlap
#         )
        
#         if not result["success"]:
#             raise HTTPException(status_code=400, detail=result["message"])
        
#         return DocumentUploadResponse(**result)
#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-file", response_model=NewDocumentUploadResponse, status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Upload a file and create document with metadata"""
    try:
        result = await lifecycle_service.create_document(file, background_tasks)
        return result
        
    except FileValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DocumentCreationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Legacy upload endpoint (kept for backward compatibility)
@router.post("/upload-file-legacy", response_model=DocumentUploadResponse)
async def upload_file_legacy(
    file: UploadFile = File(...),
    chunk_size: int = Form(500),
    chunk_overlap: int = Form(100)
):
    """Legacy upload endpoint - will be deprecated"""
    try:
        # Read file content
        content = await file.read()
        
        # Handle different file types
        if file.content_type == "text/plain":
            file_content = content.decode('utf-8')
        elif file.content_type == "application/pdf":
            # For PDF files, we'll need to use the existing PDF loader
            # This is a simplified approach - in production, you'd want to handle PDF parsing
            raise HTTPException(status_code=400, detail="PDF upload via API not supported yet. Use sync instead.")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
        
        result = document_service.upload_document(
            file.filename,
            file_content,
            chunk_size,
            chunk_overlap
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return DocumentUploadResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sync", response_model=SyncResponse)
async def sync_documents(
    doc_id: Optional[str] = None,
    force: bool = False,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Sync all documents by recreating the vector database from scratch
    
    Args:
        doc_id: Optional document ID for single document sync
        force: Force re-indexing even if document hasn't changed
        background_tasks: FastAPI background tasks for large operations
        
    Returns:
        SyncResponse with sync results
    """
    try:
        # 기존 벡터 DB 삭제
        print("Deleting existing vector database...")
        delete_result = document_service.delete_database()
        if not delete_result["success"]:
            print(f"Warning: Failed to delete existing database: {delete_result['message']}")
        
        # 대용량 임계값 (간단하게 10개 문서 이상이면 백그라운드)
        BACKGROUND_SYNC_THRESHOLD = 10
        
        if doc_id:
            # 단일 문서 동기화
            result = await lifecycle_service.sync_single_document(doc_id, force)
            
            if not result["success"]:
                raise HTTPException(
                    status_code=404 if "not found" in result.get("error", "").lower() else 400,
                    detail=result.get("error", "Sync failed")
                )
            
            return SyncResponse(
                success=True,
                message=f"Document '{doc_id}' synchronized successfully",
                total_processed=1,
                successful=1 if not result.get("skipped") else 0,
                skipped=1 if result.get("skipped") else 0,
                processing_time=result.get("processing_time", 0.0),
                doc_id=doc_id,
                chunks_created=result.get("chunks_created")
            )
        else:
            # 전체 문서 동기화 - 먼저 문서 수 확인
            from modules.services.configurable_ingestion_service import ConfigurableIngestionService
            ingest_service = ConfigurableIngestionService()
            doc_count = len(ingest_service.discover_documents())
            
            if doc_count > BACKGROUND_SYNC_THRESHOLD:
                # 백그라운드에서 처리
                background_tasks.add_task(
                    _background_sync_all,
                    force=force
                )
                
                return SyncResponse(
                    success=True,
                    message=f"Background sync started for {doc_count} documents",
                    total_processed=doc_count,
                    processing_time=0.0
                )
            else:
                # 즉시 처리
                result = await lifecycle_service.sync_all_documents(force)
                
                if not result["success"]:
                    raise HTTPException(status_code=500, detail=result.get("message", "Sync failed"))
                
                return SyncResponse(
                    success=True,
                    message=result["message"],
                    total_processed=result["total_processed"],
                    successful=result["successful"],
                    failed=result["failed"],
                    skipped=result["skipped"],
                    processing_time=result["processing_time"]
                )
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync operation failed: {str(e)}")

async def _background_sync_all(force: bool = False):
    """백그라운드 전체 동기화"""
    import structlog
    logger = structlog.get_logger(__name__)
    
    try:
        logger.info("Starting background sync for all documents", force=force)
        result = await lifecycle_service.sync_all_documents(force)
        logger.info(
            "Background sync completed",
            success=result["success"],
            total_processed=result["total_processed"],
            successful=result["successful"],
            failed=result["failed"]
        )
    except Exception as e:
        logger.error("Background sync failed", error=str(e))

@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: str = Path(..., regex=r"^[a-zA-Z0-9_-]+_\d{13}$", description="Document ID to delete")
):
    """
    Delete a specific document and all its associated data
    
    Args:
        doc_id: Document ID matching pattern: name_timestamp
        
    Returns:
        204 No Content on successful deletion
        
    Raises:
        400: Invalid document ID format or path traversal attempt
        404: Document not found
        500: Internal server error during deletion
    """
    try:
        # Perform deletion with audit logging
        result = await delete_service.delete_document(doc_id, user_id="api_user")
        
        if not result.success:
            raise HTTPException(
                status_code=500, 
                detail=result.error_message or "Failed to delete document"
            )
        
        # Return 204 No Content for successful deletion (no response body)
        return
        
    except InvalidDocumentIdError as e:
        raise HTTPException(status_code=400, detail=f"Invalid document ID: {str(e)}")
    except DirectoryTraversalError as e:
        raise HTTPException(status_code=400, detail=f"Security violation: {str(e)}")
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except DocumentDeletionError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error during deletion: {str(e)}")

@router.post("/add", response_model=SyncResponse)
async def add_document_to_vector_db(
    doc_id: str,
    chunk_size: int = 512,
    chunk_overlap: int = 51,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Add a single document to the existing vector database
    
    Args:
        doc_id: Document ID to add to vector database
        chunk_size: Size of text chunks for processing
        chunk_overlap: Overlap between chunks
        background_tasks: FastAPI background tasks for processing
        
    Returns:
        SyncResponse with addition results
    """
    try:
        from modules.services.configurable_ingestion_service import ConfigurableIngestionService
        from pathlib import Path
        
        # 문서가 존재하는지 확인
        raw_data_path = settings.get_raw_data_path()
        doc_dir = raw_data_path / doc_id
        
        if not doc_dir.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"Document directory not found: {doc_id}"
            )
        
        pdf_file = doc_dir / "original.pdf"
        if not pdf_file.exists():
            raise HTTPException(
                status_code=404, 
                detail=f"PDF file not found for document: {doc_id}"
            )
        
        # ConfigurableIngestionService를 사용하여 단일 문서 추가
        ingest_service = ConfigurableIngestionService()
        
        # 간단한 chunk config 객체 생성
        class SimpleChunkConfig:
            def __init__(self, chunk_size, overlap_ratio):
                self.chunk_size = chunk_size
                self.overlap_ratio = overlap_ratio
        
        chunk_config = SimpleChunkConfig(
            chunk_size=chunk_size,
            overlap_ratio=chunk_overlap / chunk_size
        )
        
        try:
            chunks_created = ingest_service._perform_ingestion(doc_id, pdf_file, chunk_config)
            
            return SyncResponse(
                success=True,
                message=f"Document '{doc_id}' added successfully to vector database",
                total_processed=1,
                successful=1,
                failed=0,
                skipped=0,
                processing_time=0.0,
                doc_id=doc_id,
                chunks_created=chunks_created
            )
            
        except Exception as e:
            return SyncResponse(
                success=False,
                message=f"Failed to add document '{doc_id}': {str(e)}",
                total_processed=1,
                successful=0,
                failed=1,
                skipped=0,
                processing_time=0.0,
                doc_id=doc_id,
                chunks_created=0
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Add operation failed: {str(e)}")

@router.delete("/database")
async def delete_database():
    """Delete the vector database"""
    try:
        result = document_service.delete_database()
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return {"message": result["message"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))