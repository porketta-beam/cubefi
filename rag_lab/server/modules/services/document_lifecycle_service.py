"""Document lifecycle management service"""

import json
import os
import shutil
import tempfile
import time
import uuid
import asyncio
from pathlib import Path
from typing import Optional, BinaryIO, Dict, Any
from slugify import slugify
import aiofiles
import structlog
from fastapi import BackgroundTasks, UploadFile

from modules.api.models.document_config import DocumentConfigModel
from modules.api.models.document_metadata import (
    DocumentMetadata, 
    UploadSession, 
    DocumentUploadResponse,
    FileValidationError,
    DocumentCreationError
)
from modules.services.metadata_extractors import DocumentMetadataService
from modules.services.document_config_service import DocumentConfigService
from modules.utils.security import DocumentSecurityService
from modules.exceptions import ValidationError

logger = structlog.get_logger(__name__)

class DocumentLifecycleService:
    """Service for managing document lifecycle operations"""
    
    # File upload constraints
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
    LARGE_FILE_THRESHOLD = 10 * 1024 * 1024  # 10 MB
    ALLOWED_CONTENT_TYPES = {
        "application/pdf",
        "text/plain", 
        "text/markdown",
        "application/x-markdown",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        # Additional PDF MIME types (sometimes misdetected)
        "application/x-pdf",
        "application/acrobat",
        "applications/vnd.pdf",
        "text/pdf",
        "text/x-pdf",
        # Sometimes files are misdetected as generic binary
        "application/octet-stream",
        "application/x-msdownload"  # Sometimes PDF files get this MIME type
    }
    ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown", ".docx"}
    CHUNK_SIZE = 64 * 1024  # 64 KB chunks for streaming
    
    def __init__(self, raw_data_root: str = "./raw_data"):
        self.raw_data_root = Path(raw_data_root)
        self.raw_data_root.mkdir(exist_ok=True)
        
        self.metadata_service = DocumentMetadataService()
        self.config_service = DocumentConfigService(raw_data_root)
        self.security_service = DocumentSecurityService(raw_data_root)
        
    def _generate_doc_id(self, filename: str) -> str:
        """
        Generate unique document ID
        
        Args:
            filename: Original filename
            
        Returns:
            Document ID in format: slugified_name_timestamp
        """
        # Extract name without extension
        name_without_ext = Path(filename).stem
        
        # Slugify the name (remove special characters, spaces to hyphens)
        try:
            # Try with max_length parameter (python-slugify >= 5.0)
            slugified_name = slugify(name_without_ext, max_length=50)
        except TypeError:
            # Fallback for older versions or different slugify implementations
            slugified_name = slugify(name_without_ext)
            if len(slugified_name) > 50:
                slugified_name = slugified_name[:50].rstrip('-')
        
        # Ensure we have a valid slugified name
        if not slugified_name or not slugified_name.replace('-', '').replace('_', '').isalnum():
            # Fallback to a safe default if slugify produces invalid result
            slugified_name = f"document-{uuid.uuid4().hex[:8]}"
        
        # Generate 13-digit millisecond timestamp
        timestamp = str(int(time.time() * 1000))
        
        # Combine
        doc_id = f"{slugified_name}_{timestamp}"
        
        # Validate format
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+_\d{13}$', doc_id):
            raise ValueError(f"Generated doc_id doesn't match required pattern: {doc_id}")
        
        return doc_id
    
    async def validate_upload_file(self, file: UploadFile) -> None:
        """
        Validate uploaded file
        
        Args:
            file: FastAPI UploadFile object
            
        Raises:
            FileValidationError: If validation fails
        """
        # Check filename
        if not file.filename:
            raise FileValidationError("Filename is required")
        
        if ".." in file.filename:
            raise FileValidationError("Invalid filename: contains directory traversal")
        
        # Check file extension first (more reliable than MIME type)
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in self.ALLOWED_EXTENSIONS:
            raise FileValidationError(
                f"Unsupported file extension: {file_extension}. "
                f"Allowed extensions: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )
        
        # Check content type (more lenient for known extensions)
        if file_extension in {".pdf"} and file.content_type not in self.ALLOWED_CONTENT_TYPES:
            # For PDF files, be more permissive if extension is correct
            # Log the unusual MIME type but allow the upload
            import structlog
            logger = structlog.get_logger(__name__)
            logger.warning(
                "PDF file with unusual MIME type detected",
                filename=file.filename,
                content_type=file.content_type,
                message="Allowing upload based on file extension"
            )
        elif file.content_type not in self.ALLOWED_CONTENT_TYPES:
            raise FileValidationError(
                f"Unsupported content type: {file.content_type}. "
                f"Allowed types: {', '.join(sorted(self.ALLOWED_CONTENT_TYPES))}"
            )
        
        # Additional validation for PDF files by checking file signature
        if file_extension == ".pdf":
            await self._validate_pdf_file(file)
        
        # Check file size (if available)
        if hasattr(file, 'size') and file.size:
            if file.size > self.MAX_FILE_SIZE:
                raise FileValidationError(
                    f"File too large: {file.size} bytes. Maximum allowed: {self.MAX_FILE_SIZE} bytes"
                )
    
    async def _validate_pdf_file(self, file: UploadFile) -> None:
        """
        Validate that a file is actually a PDF by checking its signature
        
        Args:
            file: FastAPI UploadFile object
            
        Raises:
            FileValidationError: If file is not a valid PDF
        """
        # Save current position
        current_pos = file.file.tell() if hasattr(file.file, 'tell') else 0
        
        try:
            # Move to beginning of file
            await file.seek(0)
            
            # Read first few bytes to check PDF signature
            header = await file.read(8)
            
            # PDF files start with %PDF
            if not header.startswith(b'%PDF'):
                raise FileValidationError(
                    "File does not appear to be a valid PDF (invalid file signature)"
                )
                
        except Exception as e:
            if isinstance(e, FileValidationError):
                raise
            raise FileValidationError(f"Failed to validate PDF file: {str(e)}")
        finally:
            # Reset file position
            try:
                await file.seek(current_pos)
            except Exception:
                # If seeking fails, reset to beginning
                await file.seek(0)
    
    async def stream_to_storage(self, upload_file: UploadFile, target_path: Path) -> int:
        """
        Stream upload file to storage with progress tracking
        
        Args:
            upload_file: FastAPI UploadFile object
            target_path: Target file path
            
        Returns:
            Total bytes written
        """
        total_bytes = 0
        
        # Ensure target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            async with aiofiles.open(target_path, 'wb') as target_file:
                # Reset file pointer
                await upload_file.seek(0)
                
                # Stream file in chunks
                while chunk := await upload_file.read(self.CHUNK_SIZE):
                    await target_file.write(chunk)
                    total_bytes += len(chunk)
                    
                    # Check size limit during streaming
                    if total_bytes > self.MAX_FILE_SIZE:
                        # Clean up partial file
                        await target_file.close()
                        target_path.unlink(missing_ok=True)
                        raise FileValidationError(
                            f"File too large: exceeded {self.MAX_FILE_SIZE} bytes during upload"
                        )
                
            # Verify file size matches
            actual_size = target_path.stat().st_size
            if actual_size != total_bytes:
                target_path.unlink(missing_ok=True)
                raise FileValidationError(
                    f"File size mismatch: expected {total_bytes}, got {actual_size}"
                )
                
            return total_bytes
            
        except Exception as e:
            # Clean up on any error
            target_path.unlink(missing_ok=True)
            raise e
    
    async def create_document(
        self, 
        file: UploadFile, 
        background_tasks: Optional[BackgroundTasks] = None
    ) -> DocumentUploadResponse:
        """
        Create a new document from uploaded file
        
        Args:
            file: Uploaded file
            background_tasks: FastAPI background tasks
            
        Returns:
            Upload response with document details
        """
        upload_id = str(uuid.uuid4())
        doc_id = None
        
        try:
            # Validate file
            await self.validate_upload_file(file)
            
            # Generate document ID
            doc_id = self._generate_doc_id(file.filename)
            
            # Validate document path security
            if not self.security_service.validate_document_path(doc_id):
                raise FileValidationError(f"Invalid document path: {doc_id}")
            
            # Create document directory
            doc_dir = self.raw_data_root / doc_id
            doc_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine file extension and target path
            original_extension = Path(file.filename).suffix.lower()
            target_filename = f"original{original_extension}"
            target_path = doc_dir / target_filename
            
            # Stream file to storage
            file_size = await self.stream_to_storage(file, target_path)
            
            # Extract metadata
            # Ensure content_type is not None
            content_type = file.content_type or "application/octet-stream"
            metadata = await self.metadata_service.extract_metadata(
                target_path, 
                file.filename, 
                content_type
            )
            
            # Save metadata.json
            metadata_path = doc_dir / "metadata.json"
            async with aiofiles.open(metadata_path, 'w', encoding='utf-8') as f:
                await f.write(metadata.model_dump_json(indent=2))
            
            # Create default config.json
            default_config = DocumentConfigModel()
            await self.config_service.set_config(doc_id, default_config, user_id="system")
            
            # Determine if this is a large file requiring background processing
            is_large_file = file_size > self.LARGE_FILE_THRESHOLD
            processing = is_large_file
            estimated_time = None
            
            if is_large_file and background_tasks:
                # Schedule background processing
                background_tasks.add_task(
                    self._process_large_file,
                    doc_id,
                    upload_id
                )
                estimated_time = "2-5 minutes"
            
            # Log successful creation
            logger.info(
                "Document created successfully",
                doc_id=doc_id,
                upload_id=upload_id,
                filename=file.filename,
                file_size=file_size,
                content_type=file.content_type,
                processing=processing
            )
            
            return DocumentUploadResponse(
                message=f"Document '{file.filename}' uploaded successfully",
                doc_id=doc_id,
                upload_id=upload_id,
                status="uploaded" if not processing else "processing",
                processing=processing,
                estimated_processing_time=estimated_time,
                file_size=file_size,
                content_type=file.content_type or "application/octet-stream"
            )
            
        except Exception as e:
            # Rollback on error
            if doc_id:
                await self._rollback_creation(doc_id)
            
            import traceback
            tb_str = traceback.format_exc()
            logger.error(
                "Document creation failed",
                upload_id=upload_id,
                doc_id=doc_id,
                filename=file.filename if file and file.filename else "unknown",
                error=str(e),
                error_type=type(e).__name__,
                traceback=tb_str
            )
            
            # Print full traceback to console for debugging
            print("\n" + "="*80)
            print("DETAILED ERROR TRACEBACK:")
            print("="*80)
            print(f"Error Type: {type(e).__name__}")
            print(f"Error Message: {str(e)}")
            print("Full Traceback:")
            print(tb_str)
            print("="*80 + "\n")
            
            if isinstance(e, FileValidationError):
                raise e
            else:
                raise DocumentCreationError(f"Failed to create document: {str(e)}")
    
    async def _rollback_creation(self, doc_id: str) -> None:
        """
        Rollback document creation on error
        
        Args:
            doc_id: Document ID to rollback
        """
        try:
            doc_dir = self.raw_data_root / doc_id
            if doc_dir.exists():
                shutil.rmtree(doc_dir)
                logger.info("Document creation rolled back", doc_id=doc_id)
        except Exception as e:
            logger.error("Failed to rollback document creation", doc_id=doc_id, error=str(e))
    
    async def _process_large_file(self, doc_id: str, upload_id: str) -> None:
        """
        Background processing for large files
        
        Args:
            doc_id: Document ID
            upload_id: Upload session ID
        """
        try:
            logger.info("Starting background processing", doc_id=doc_id, upload_id=upload_id)
            
            # Simulate processing steps
            # In a real implementation, this would:
            # 1. Extract full text
            # 2. Generate preview
            # 3. Index document for search
            
            await asyncio.sleep(5)  # Simulate processing time
            
            logger.info("Background processing completed", doc_id=doc_id, upload_id=upload_id)
            
        except Exception as e:
            logger.error(
                "Background processing failed",
                doc_id=doc_id,
                upload_id=upload_id,
                error=str(e)
            )
    
    async def get_document_info(self, doc_id: str) -> Optional[dict]:
        """
        Get document information
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document information dictionary or None if not found
        """
        doc_dir = self.raw_data_root / doc_id
        if not doc_dir.exists():
            return None
        
        info = {"doc_id": doc_id}
        
        # Load metadata if available
        metadata_path = doc_dir / "metadata.json"
        if metadata_path.exists():
            async with aiofiles.open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_content = await f.read()
                info["metadata"] = json.loads(metadata_content)
        
        # Load config if available
        try:
            config = await self.config_service.get_config(doc_id)
            info["config"] = config.model_dump()
        except:
            pass
        
        return info
    
    async def sync_single_document(self, doc_id: str, force: bool = False) -> Dict[str, Any]:
        """
        단일 문서 동기화
        
        Args:
            doc_id: 문서 ID
            force: 강제 재색인 여부
            
        Returns:
            동기화 결과
        """
        from modules.services.configurable_ingestion_service import ConfigurableIngestionService
        
        try:
            # 문서 존재 확인
            doc_dir = self.raw_data_root / doc_id
            if not doc_dir.exists():
                return {
                    "success": False,
                    "error": f"Document not found: {doc_id}"
                }
            
            # 인제스트 서비스 사용
            ingest_service = ConfigurableIngestionService(str(self.raw_data_root))
            result = await ingest_service.ingest_document(doc_id, force_reindex=force)
            
            logger.info(
                "Single document sync completed",
                doc_id=doc_id,
                success=result.success,
                chunks_created=result.chunks_created,
                skipped=result.skipped
            )
            
            return {
                "success": result.success,
                "doc_id": doc_id,
                "chunks_created": result.chunks_created,
                "skipped": result.skipped,
                "processing_time": result.processing_time,
                "error": result.error_message
            }
            
        except Exception as e:
            logger.error(
                "Single document sync failed",
                doc_id=doc_id,
                error=str(e)
            )
            return {
                "success": False,
                "doc_id": doc_id,
                "error": str(e)
            }
    
    async def sync_all_documents(self, force: bool = False, batch_size: int = 5) -> Dict[str, Any]:
        """
        전체 문서 동기화 (간단한 배치 처리)
        
        Args:
            force: 강제 재색인 여부
            batch_size: 배치 크기
            
        Returns:
            전체 동기화 결과
        """
        from modules.services.configurable_ingestion_service import ConfigurableIngestionService
        import time
        
        start_time = time.time()
        
        try:
            # 인제스트 서비스 초기화
            ingest_service = ConfigurableIngestionService(str(self.raw_data_root))
            
            # 문서 목록 발견
            doc_ids = ingest_service.discover_documents()
            if not doc_ids:
                return {
                    "success": True,
                    "message": "No documents found to sync",
                    "total_processed": 0,
                    "successful": 0,
                    "failed": 0,
                    "skipped": 0,
                    "results": [],
                    "processing_time": time.time() - start_time
                }
            
            logger.info(f"Starting sync for {len(doc_ids)} documents")
            
            # 간단한 배치 처리 (복잡한 병렬 처리는 피함)
            results = []
            successful = 0
            failed = 0
            skipped = 0
            
            for i, doc_id in enumerate(doc_ids):
                try:
                    # 간단한 진행률 로깅
                    if i % batch_size == 0:
                        logger.info(f"Processing batch {i//batch_size + 1}, documents {i+1}-{min(i+batch_size, len(doc_ids))}")
                    
                    result = await ingest_service.ingest_document(doc_id, force_reindex=force)
                    results.append(result)
                    
                    if result.success:
                        if result.skipped:
                            skipped += 1
                        else:
                            successful += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"Failed to process document {doc_id}: {e}")
                    failed += 1
                    results.append({
                        "doc_id": doc_id,
                        "success": False,
                        "error_message": str(e)
                    })
            
            processing_time = time.time() - start_time
            
            logger.info(
                "Batch sync completed",
                total_processed=len(doc_ids),
                successful=successful,
                failed=failed,
                skipped=skipped,
                processing_time=processing_time
            )
            
            return {
                "success": True,
                "message": f"Sync completed: {successful} successful, {failed} failed, {skipped} skipped",
                "total_processed": len(doc_ids),
                "successful": successful,
                "failed": failed,
                "skipped": skipped,
                "results": [result.model_dump() if hasattr(result, 'model_dump') else result for result in results],
                "processing_time": processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                "Batch sync failed",
                error=str(e),
                processing_time=processing_time
            )
            
            return {
                "success": False,
                "message": f"Sync failed: {str(e)}",
                "total_processed": 0,
                "successful": 0,
                "failed": 0,
                "skipped": 0,
                "results": [],
                "processing_time": processing_time
            }