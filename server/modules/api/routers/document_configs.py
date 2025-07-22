"""Document configuration API routes"""

from fastapi import APIRouter, HTTPException, Depends, Path, Header
from typing import Optional
import structlog

from modules.api.models.document_config import (
    DocumentConfigModel, 
    DocumentConfigUpdate, 
    ConfigUpdateResponse,
    ConfigValidationResponse
)
from modules.services.document_config_service import DocumentConfigService
from modules.validators.chunk_validator import ChunkConfigValidator
from modules.exceptions import (
    DocumentNotFoundError, 
    ConfigurationError
)
from modules.utils.security import DirectoryTraversalError

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/config/documents", tags=["document-configs"])

def get_config_service() -> DocumentConfigService:
    """Dependency injection for config service"""
    return DocumentConfigService()

@router.get("/{doc_id}", response_model=DocumentConfigModel)
async def get_document_config(
    doc_id: str = Path(..., regex=r"^[a-zA-Z0-9_-]+_\d{13}$"),
    env: str = "default",
    config_service: DocumentConfigService = Depends(get_config_service)
):
    """Get document configuration"""
    try:
        config = await config_service.get_config(doc_id, env)
        return config
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")
    except DirectoryTraversalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to get document config", doc_id=doc_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{doc_id}", response_model=ConfigUpdateResponse)
async def update_document_config(
    config_update: DocumentConfigUpdate,
    doc_id: str = Path(..., regex=r"^[a-zA-Z0-9_-]+_\d{13}$"),
    x_user_id: Optional[str] = Header(None),
    config_service: DocumentConfigService = Depends(get_config_service)
):
    """Update document configuration"""
    try:
        # Get current config
        current_config = await config_service.get_config(doc_id)
        
        # Apply updates
        update_data = config_update.model_dump(exclude_none=True)
        
        # Handle legacy chunk_size and chunk_overlap fields
        if 'chunk_size' in update_data or 'chunk_overlap' in update_data:
            chunk_data = current_config.chunk.model_dump()
            
            if 'chunk_size' in update_data:
                chunk_data['chunk_size'] = update_data['chunk_size']
            
            if 'chunk_overlap' in update_data:
                # Convert chunk_overlap to overlap_ratio
                chunk_size = chunk_data.get('chunk_size', current_config.chunk.chunk_size)
                chunk_data['overlap_ratio'] = update_data['chunk_overlap'] / chunk_size
            
            current_config.chunk = DocumentConfigModel.model_validate({
                'chunk': chunk_data
            }).chunk
        
        if 'metadata' in update_data:
            current_config.metadata = update_data['metadata']
        
        # Validate updated config
        is_valid, errors, warnings = ChunkConfigValidator.validate_config(current_config)
        if not is_valid:
            error_details = {
                "errors": [error.model_dump() for error in errors],
                "warnings": warnings
            }
            raise HTTPException(
                status_code=422, 
                detail=error_details
            )
        
        # Save config
        version = await config_service.set_config(doc_id, current_config, x_user_id)
        
        return ConfigUpdateResponse(
            status="updated",
            version=version,
            warnings=warnings,
            doc_id=doc_id
        )
        
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")
    except DirectoryTraversalError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConfigurationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Failed to update document config", doc_id=doc_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{doc_id}/validate", response_model=ConfigValidationResponse)
async def validate_document_config(
    config: DocumentConfigModel,
    doc_id: str = Path(..., regex=r"^[a-zA-Z0-9_-]+_\d{13}$")
):
    """Validate document configuration without saving"""
    try:
        is_valid, errors, warnings = ChunkConfigValidator.validate_config(config)
        
        return ConfigValidationResponse(
            valid=is_valid,
            errors=[error.model_dump() for error in errors],
            warnings=warnings
        )
        
    except Exception as e:
        logger.error("Failed to validate document config", doc_id=doc_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")