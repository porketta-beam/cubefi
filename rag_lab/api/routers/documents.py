"""Document management API routes"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
from api.models.document import (
    DocumentUploadRequest, DocumentUploadResponse, 
    DocumentListResponse, DocumentSyncRequest, DocumentSyncResponse,
    DocumentStatusResponse
)
from api.services.document_service import DocumentService

router = APIRouter(prefix="/api/documents", tags=["documents"])
document_service = DocumentService()

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

@router.post("/upload-file", response_model=DocumentUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    chunk_size: int = Form(500),
    chunk_overlap: int = Form(100)
):
    """Upload a file to the vector database"""
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

@router.post("/sync", response_model=DocumentSyncResponse)
async def sync_documents(request: DocumentSyncRequest):
    """Sync documents from raw_data folder"""
    try:
        result = document_service.sync_documents(
            request.chunk_size,
            request.chunk_overlap
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return DocumentSyncResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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