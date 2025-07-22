"""간단한 설정 기반 문서 인제스트 서비스"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import structlog
from pydantic import BaseModel

from modules.api.models.document_config import DocumentConfigModel
from modules.services.document_config_service import DocumentConfigService
from config.settings import settings

logger = structlog.get_logger(__name__)

class IngestionResult(BaseModel):
    """인제스트 작업 결과"""
    doc_id: str
    success: bool
    chunks_created: int = 0
    error_message: Optional[str] = None
    skipped: bool = False
    processing_time: float = 0.0

class SyncResult(BaseModel):
    """동기화 결과"""
    total_processed: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    results: List[IngestionResult] = []
    processing_time: float = 0.0

class ConfigurableIngestionService:
    """설정 기반 문서 인제스트 서비스 (단순한 개인 프로젝트용)"""
    
    def __init__(self, raw_data_root: str = "./raw_data"):
        self.raw_data_root = Path(raw_data_root)
        self.config_service = DocumentConfigService(raw_data_root)
        
    async def ingest_document(self, doc_id: str, force_reindex: bool = False) -> IngestionResult:
        """
        단일 문서 인제스트 (동기식)
        
        Args:
            doc_id: 문서 ID
            force_reindex: 강제 재색인 여부
            
        Returns:
            IngestionResult: 인제스트 결과
        """
        import time
        start_time = time.time()
        
        try:
            doc_dir = self.raw_data_root / doc_id
            if not doc_dir.exists():
                return IngestionResult(
                    doc_id=doc_id,
                    success=False,
                    error_message=f"Document directory not found: {doc_id}"
                )
            
            # 1. config.json 로드
            try:
                config = await self.config_service.get_config(doc_id)
            except Exception as e:
                logger.warning(f"Config load failed for {doc_id}, using defaults: {e}")
                config = DocumentConfigModel()  # 기본값 사용
            
            # 2. 원본 파일 찾기
            original_file = self._find_original_file(doc_dir)
            if not original_file:
                return IngestionResult(
                    doc_id=doc_id,
                    success=False,
                    error_message="Original file not found"
                )
            
            # 3. 재색인 필요 여부 확인 (간단한 수정 시간 기반)
            if not force_reindex and self._should_skip_ingestion(doc_dir, original_file):
                return IngestionResult(
                    doc_id=doc_id,
                    success=True,
                    skipped=True,
                    processing_time=time.time() - start_time
                )
            
            # 4. 실제 인제스트 수행 (기존 document_service 활용)
            chunks_created = self._perform_ingestion(doc_id, original_file, config.chunk)
            
            # 5. 인제스트 메타데이터 저장
            self._save_ingestion_metadata(doc_dir, chunks_created, config)
            
            processing_time = time.time() - start_time
            
            logger.info(
                "Document ingested successfully",
                doc_id=doc_id,
                chunks_created=chunks_created,
                processing_time=processing_time
            )
            
            return IngestionResult(
                doc_id=doc_id,
                success=True,
                chunks_created=chunks_created,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                "Document ingestion failed",
                doc_id=doc_id,
                error=str(e),
                processing_time=processing_time
            )
            
            return IngestionResult(
                doc_id=doc_id,
                success=False,
                error_message=str(e),
                processing_time=processing_time
            )
    
    def _find_original_file(self, doc_dir: Path) -> Optional[Path]:
        """원본 파일 찾기"""
        # 가능한 원본 파일 확장자들
        extensions = ['.pdf', '.txt', '.md', '.docx']
        
        for ext in extensions:
            original_file = doc_dir / f"original{ext}"
            if original_file.exists():
                return original_file
        
        return None
    
    def _should_skip_ingestion(self, doc_dir: Path, original_file: Path) -> bool:
        """
        재색인 필요 여부 확인 (간단한 방법)
        ingestion_metadata.json의 last_ingested와 원본 파일의 수정 시간 비교
        """
        metadata_file = doc_dir / "ingestion_metadata.json"
        if not metadata_file.exists():
            return False
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            last_ingested = metadata.get('last_ingested_timestamp', 0)
            file_modified = original_file.stat().st_mtime
            
            # 파일이 마지막 인제스트 이후 수정되지 않았으면 skip
            return file_modified <= last_ingested
            
        except Exception:
            return False
    
    def _perform_ingestion(self, doc_id: str, original_file: Path, chunk_config) -> int:
        """
        실제 인제스트 수행 (기존 DocumentService 활용)
        
        Returns:
            생성된 청크 수
        """
        try:
            # 기존 DocumentService를 사용하여 실제 벡터 DB 저장
            from modules.api.services.document_service import DocumentService
            
            document_service = DocumentService()
            
            # chunk_config에서 설정값 추출
            chunk_size = chunk_config.chunk_size
            chunk_overlap = int(chunk_size * chunk_config.overlap_ratio)
            
            logger.info(
                "Starting vector DB ingestion",
                doc_id=doc_id,
                file_path=str(original_file),
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            # 개별 문서를 벡터 DB에 직접 추가
            from langchain_community.document_loaders import PyPDFLoader
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            from modules.auto_rag.mod import ChromaDBManager
            
            # PDF 로드
            loader = PyPDFLoader(str(original_file))
            documents = loader.load()
            
            # 텍스트 분할
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            chunks = text_splitter.split_documents(documents)
            
            # 메타데이터에 doc_id 추가
            for chunk in chunks:
                chunk.metadata['doc_id'] = doc_id
                chunk.metadata['source_file'] = str(original_file)
            
            # ChromaDB에 추가
            chroma_path = str(settings.get_chroma_path())
            db_manager = ChromaDBManager(db_path=chroma_path)
            
            # 기존 DB가 있으면 로드, 없으면 새로 생성
            if db_manager.check_db_exists():
                success = db_manager.load_existing_db()
                if not success:
                    raise Exception("Failed to load existing database")
                success = db_manager.add_documents(chunks)
            else:
                success = db_manager.create_new_db(chunks)
            
            if success:
                chunk_count = len(chunks)
                logger.info(
                    "Vector DB ingestion completed",
                    doc_id=doc_id,
                    chunks_created=chunk_count
                )
                return chunk_count
            else:
                raise Exception("Failed to add documents to vector database")
            
        except Exception as e:
            logger.error(f"Ingestion failed for {doc_id}: {e}")
            raise
    
    def _save_ingestion_metadata(self, doc_dir: Path, chunks_created: int, config: DocumentConfigModel):
        """인제스트 메타데이터 저장"""
        import time
        
        metadata = {
            "last_ingested_timestamp": time.time(),
            "chunks_created": chunks_created,
            "chunk_size": config.chunk.chunk_size,
            "overlap_ratio": config.chunk.overlap_ratio,
            "ingestion_version": "1.0"
        }
        
        metadata_file = doc_dir / "ingestion_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    
    def discover_documents(self) -> List[str]:
        """raw_data 디렉터리에서 문서 ID 목록 반환"""
        try:
            if not self.raw_data_root.exists():
                return []
            
            doc_ids = []
            for item in self.raw_data_root.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # 간단한 문서 ID 패턴 확인
                    if '_' in item.name and item.name.split('_')[-1].isdigit():
                        doc_ids.append(item.name)
            
            return sorted(doc_ids)
            
        except Exception as e:
            logger.error(f"Document discovery failed: {e}")
            return []