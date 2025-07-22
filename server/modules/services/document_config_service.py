"""Document configuration service"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import structlog
import aiofiles

from modules.api.models.document_config import DocumentConfigModel, DocumentChunkOptions
from modules.exceptions import DocumentNotFoundError, ConfigurationError
from modules.utils.security import DocumentSecurityService, DirectoryTraversalError
from modules.validators.chunk_validator import ChunkConfigValidator

logger = structlog.get_logger(__name__)

class DocumentConfigService:
    """Service for managing document configurations"""
    
    def __init__(self, raw_data_root: str = "./raw_data"):
        self.raw_data_root = Path(raw_data_root)
        self.security_service = DocumentSecurityService(raw_data_root)
        
    async def get_config(self, doc_id: str, env: str = "default") -> DocumentConfigModel:
        """
        Get document configuration
        
        Args:
            doc_id: Document identifier
            env: Environment (default, staging, production)
            
        Returns:
            Document configuration
            
        Raises:
            DocumentNotFoundError: If document doesn't exist
            DirectoryTraversalError: If doc_id contains path traversal
        """
        # Validate document ID and path
        if not ChunkConfigValidator.validate_doc_id(doc_id):
            raise DirectoryTraversalError(f"Invalid document ID format: {doc_id}")
            
        if not self.security_service.validate_document_path(doc_id):
            raise DirectoryTraversalError(f"Invalid document path: {doc_id}")
        
        doc_dir = self.raw_data_root / doc_id
        if not doc_dir.exists():
            raise DocumentNotFoundError(doc_id)
        
        # Try environment-specific config first
        env_config_path = doc_dir / f"config_{env}.json"
        config_path = doc_dir / "config.json"
        
        config_file = env_config_path if env_config_path.exists() else config_path
        
        if config_file.exists():
            try:
                async with aiofiles.open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.loads(await f.read())
                
                # Remove metadata for validation
                if "_metadata" in config_data:
                    del config_data["_metadata"]
                
                return DocumentConfigModel.model_validate(config_data)
            except Exception as e:
                logger.error(
                    "Failed to load document config",
                    doc_id=doc_id,
                    config_path=str(config_file),
                    error=str(e)
                )
                # Return default config if loading fails
                return DocumentConfigModel()
        else:
            # Return default configuration
            return DocumentConfigModel()
    
    async def set_config(self, doc_id: str, config: DocumentConfigModel, user_id: Optional[str] = None) -> str:
        """
        Set document configuration with atomic update
        
        Args:
            doc_id: Document identifier
            config: New configuration
            user_id: User making the change
            
        Returns:
            Configuration version
            
        Raises:
            DocumentNotFoundError: If document doesn't exist
            ConfigurationError: If configuration is invalid
            DirectoryTraversalError: If doc_id contains path traversal
        """
        # Validate document ID and path
        if not ChunkConfigValidator.validate_doc_id(doc_id):
            raise DirectoryTraversalError(f"Invalid document ID format: {doc_id}")
            
        if not self.security_service.validate_document_path(doc_id):
            raise DirectoryTraversalError(f"Invalid document path: {doc_id}")
        
        doc_dir = self.raw_data_root / doc_id
        if not doc_dir.exists():
            raise DocumentNotFoundError(doc_id)
        
        # Validate configuration
        is_valid, errors, warnings = ChunkConfigValidator.validate_config(config)
        if not is_valid:
            error_messages = [f"{error.field}: {error.message}" for error in errors]
            raise ConfigurationError(
                f"Configuration validation failed: {'; '.join(error_messages)}",
                {"errors": errors, "warnings": warnings}
            )
        
        config_path = doc_dir / "config.json"
        backup_path = None
        
        try:
            # Create backup if config exists
            if config_path.exists():
                backup_dir = doc_dir / "_history"
                backup_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"config_{timestamp}.json"
                
                async with aiofiles.open(config_path, 'r', encoding='utf-8') as src:
                    content = await src.read()
                async with aiofiles.open(backup_path, 'w', encoding='utf-8') as dst:
                    await dst.write(content)
            
            # Write new config atomically
            config_data = config.model_dump()
            version = datetime.now().strftime("%Y%m%d.%H%M%S")
            config_data["_metadata"] = {
                "version": version,
                "updated_at": datetime.now().isoformat(),
                "updated_by": user_id
            }
            
            # Use temporary file for atomic write
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode='w', 
                    suffix='.json', 
                    dir=doc_dir, 
                    delete=False,
                    encoding='utf-8'
                ) as temp_file:
                    json.dump(config_data, temp_file, indent=2, ensure_ascii=False)
                    temp_path = temp_file.name
                
                # Atomic replace
                os.replace(temp_path, config_path)
                
                # Log success
                self.security_service.audit_config_operation(
                    "update_config", doc_id, user_id, success=True
                )
                
                logger.info(
                    "Document config updated successfully",
                    doc_id=doc_id,
                    version=version,
                    user_id=user_id,
                    warnings=warnings
                )
                
                return version
                
            except Exception as e:
                # Clean up temp file if it exists
                if temp_path and os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise e
                
        except Exception as e:
            # Restore from backup if operation failed
            if backup_path and backup_path.exists() and config_path.exists():
                try:
                    async with aiofiles.open(backup_path, 'r', encoding='utf-8') as src:
                        content = await src.read()
                    async with aiofiles.open(config_path, 'w', encoding='utf-8') as dst:
                        await dst.write(content)
                    logger.info("Config restored from backup", doc_id=doc_id)
                except Exception as restore_error:
                    logger.error(
                        "Failed to restore config from backup",
                        doc_id=doc_id,
                        error=str(restore_error)
                    )
            
            # Log failure
            self.security_service.audit_config_operation(
                "update_config", doc_id, user_id, success=False, error=str(e)
            )
            
            logger.error(
                "Failed to update document config",
                doc_id=doc_id,
                error=str(e)
            )
            
            raise ConfigurationError(f"Failed to update configuration: {str(e)}")
    
    async def delete_config(self, doc_id: str) -> bool:
        """
        Delete document configuration
        
        Args:
            doc_id: Document identifier
            
        Returns:
            True if deleted successfully
        """
        if not self.security_service.validate_document_path(doc_id):
            raise DirectoryTraversalError(f"Invalid document path: {doc_id}")
        
        doc_dir = self.raw_data_root / doc_id
        config_path = doc_dir / "config.json"
        
        if config_path.exists():
            try:
                config_path.unlink()
                logger.info("Document config deleted", doc_id=doc_id)
                return True
            except Exception as e:
                logger.error("Failed to delete config", doc_id=doc_id, error=str(e))
                return False
        
        return True  # Already doesn't exist