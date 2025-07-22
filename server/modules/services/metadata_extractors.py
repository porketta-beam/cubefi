"""Metadata extraction services for different file types"""

import hashlib
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio
import aiofiles
import structlog

from modules.api.models.document_metadata import DocumentMetadata

logger = structlog.get_logger(__name__)

class MetadataExtractor(ABC):
    """Abstract base class for metadata extractors"""
    
    @abstractmethod
    def can_extract(self, content_type: str, file_extension: str) -> bool:
        """Check if this extractor can handle the given file type"""
        pass
    
    @abstractmethod
    async def extract(self, file_path: Path, original_filename: str, content_type: str) -> DocumentMetadata:
        """Extract metadata from the file"""
        pass

class PDFExtractor(MetadataExtractor):
    """PDF metadata extractor"""
    
    def can_extract(self, content_type: str, file_extension: str) -> bool:
        return content_type == "application/pdf" or file_extension.lower() == ".pdf"
    
    async def extract(self, file_path: Path, original_filename: str, content_type: str) -> DocumentMetadata:
        try:
            import PyPDF2
            
            # Calculate file hash and size
            file_hash = await self._calculate_file_hash(file_path)
            file_size = file_path.stat().st_size
            
            # Extract PDF metadata
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
                
            # Use asyncio.to_thread for CPU-bound PDF processing
            pdf_info = await asyncio.to_thread(self._extract_pdf_info, content)
            
            return DocumentMetadata(
                original_filename=original_filename,
                content_type=content_type,
                file_size=file_size,
                file_hash=file_hash,
                page_count=pdf_info.get("page_count"),
                author=pdf_info.get("author"),
                title=pdf_info.get("title"),
                extracted_text_preview=pdf_info.get("text_preview"),
                language=pdf_info.get("language")
            )
            
        except Exception as e:
            logger.error("PDF metadata extraction failed", file_path=str(file_path), error=str(e))
            # Return basic metadata
            return await self._basic_metadata(file_path, original_filename, content_type)
    
    def _extract_pdf_info(self, content: bytes) -> Dict[str, Any]:
        """Extract PDF information from content"""
        try:
            import io
            from PyPDF2 import PdfReader
            
            reader = PdfReader(io.BytesIO(content))
            info = {}
            
            # Basic info
            info["page_count"] = len(reader.pages)
            
            # Metadata
            if reader.metadata:
                info["author"] = reader.metadata.get("/Author")
                info["title"] = reader.metadata.get("/Title")
            
            # Extract text preview from first page
            if reader.pages:
                try:
                    first_page_text = reader.pages[0].extract_text()
                    info["text_preview"] = first_page_text[:1000] if first_page_text else None
                except:
                    info["text_preview"] = None
            
            return info
            
        except Exception as e:
            logger.warning("PDF info extraction failed", error=str(e))
            return {}
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    async def _basic_metadata(self, file_path: Path, original_filename: str, content_type: str) -> DocumentMetadata:
        """Create basic metadata when extraction fails"""
        file_hash = await self._calculate_file_hash(file_path)
        file_size = file_path.stat().st_size
        
        return DocumentMetadata(
            original_filename=original_filename,
            content_type=content_type,
            file_size=file_size,
            file_hash=file_hash
        )

class TextExtractor(MetadataExtractor):
    """Text file metadata extractor"""
    
    def can_extract(self, content_type: str, file_extension: str) -> bool:
        text_types = ["text/plain", "text/markdown", "application/x-markdown"]
        text_extensions = [".txt", ".md", ".markdown"]
        return content_type in text_types or file_extension.lower() in text_extensions
    
    async def extract(self, file_path: Path, original_filename: str, content_type: str) -> DocumentMetadata:
        try:
            # Calculate file hash and size
            file_hash = await self._calculate_file_hash(file_path)
            file_size = file_path.stat().st_size
            
            # Detect encoding and extract text preview
            encoding_info = await self._detect_encoding(file_path)
            text_preview = await self._extract_text_preview(file_path, encoding_info["encoding"])
            
            return DocumentMetadata(
                original_filename=original_filename,
                content_type=content_type,
                file_size=file_size,
                file_hash=file_hash,
                encoding=encoding_info["encoding"],
                language=encoding_info.get("language"),
                extracted_text_preview=text_preview
            )
            
        except Exception as e:
            logger.error("Text metadata extraction failed", file_path=str(file_path), error=str(e))
            # Return basic metadata
            file_hash = await self._calculate_file_hash(file_path)
            file_size = file_path.stat().st_size
            
            return DocumentMetadata(
                original_filename=original_filename,
                content_type=content_type,
                file_size=file_size,
                file_hash=file_hash
            )
    
    async def _detect_encoding(self, file_path: Path) -> Dict[str, str]:
        """Detect file encoding"""
        try:
            import chardet
            
            async with aiofiles.open(file_path, 'rb') as f:
                raw_data = await f.read(10000)  # Sample first 10KB
            
            detection = chardet.detect(raw_data)
            return {
                "encoding": detection.get("encoding", "utf-8"),
                "language": detection.get("language")
            }
        except:
            return {"encoding": "utf-8"}
    
    async def _extract_text_preview(self, file_path: Path, encoding: str) -> Optional[str]:
        """Extract text preview (first 20 lines or 1000 chars)"""
        try:
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                lines = []
                line_count = 0
                char_count = 0
                
                async for line in f:
                    lines.append(line.rstrip())
                    line_count += 1
                    char_count += len(line)
                    
                    if line_count >= 20 or char_count >= 1000:
                        break
                
                return "\n".join(lines)[:1000]
        except:
            return None
    
    async def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

class DocumentMetadataService:
    """Service for extracting document metadata"""
    
    def __init__(self):
        self.extractors = [
            PDFExtractor(),
            TextExtractor()
        ]
    
    def register_extractor(self, extractor: MetadataExtractor):
        """Register a new metadata extractor"""
        self.extractors.append(extractor)
    
    async def extract_metadata(self, file_path: Path, original_filename: str, content_type: str) -> DocumentMetadata:
        """Extract metadata using appropriate extractor"""
        file_extension = file_path.suffix
        
        # Find appropriate extractor
        for extractor in self.extractors:
            if extractor.can_extract(content_type, file_extension):
                return await extractor.extract(file_path, original_filename, content_type)
        
        # Fallback to basic metadata
        logger.warning(
            "No metadata extractor found for file type",
            content_type=content_type,
            file_extension=file_extension
        )
        
        return await self._basic_metadata(file_path, original_filename, content_type)
    
    async def _basic_metadata(self, file_path: Path, original_filename: str, content_type: str) -> DocumentMetadata:
        """Create basic metadata when no specific extractor is available"""
        hash_sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_sha256.update(chunk)
        
        file_hash = hash_sha256.hexdigest()
        file_size = file_path.stat().st_size
        
        return DocumentMetadata(
            original_filename=original_filename,
            content_type=content_type,
            file_size=file_size,
            file_hash=file_hash
        )