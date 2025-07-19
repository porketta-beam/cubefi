"""RAG system API routes"""

from fastapi import APIRouter, HTTPException
from typing import Dict
from api.models.rag import (
    ChatRequest, ChatResponse,
    QuestionGenerationRequest, QuestionGenerationResponse,
    EvaluationRequest, EvaluationResponse,
    RAGConfigRequest, RAGConfigResponse
)
from api.services.rag_service import RAGService
from api.services.rag_config_service import rag_config_service

router = APIRouter(prefix="/api/rag", tags=["rag"])
rag_service = RAGService()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Get answer to a question using RAG"""
    try:
        result = rag_service.chat(
            question=request.question,
            model=request.model,
            temperature=request.temperature,
            search_type=request.search_type,
            k=request.k
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["answer"])
        
        return ChatResponse(
            answer=result["answer"],
            contexts=result["contexts"],
            model_used=result["model_used"],
            search_params=result["search_params"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-questions", response_model=QuestionGenerationResponse)
async def generate_questions(request: QuestionGenerationRequest):
    """Generate questions from documents"""
    try:
        result = rag_service.generate_questions(
            model=request.model,
            temperature=request.temperature,
            num_questions=request.num_questions
        )
        
        if not result["success"]:
            error_msg = result.get("error", "Unknown error occurred")
            raise HTTPException(status_code=400, detail=error_msg)
        
        return QuestionGenerationResponse(
            questions=result["questions"],
            model_used=result["model_used"],
            success=result["success"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_rag(request: EvaluationRequest):
    """Evaluate RAG system using RAGAS"""
    try:
        result = rag_service.evaluate_rag(
            questions=request.questions,
            model=request.model,
            temperature=request.temperature,
            search_type=request.search_type,
            k=request.k,
            use_faithfulness=request.use_faithfulness,
            use_answer_relevancy=request.use_answer_relevancy,
            use_context_precision=request.use_context_precision,
            use_context_recall=request.use_context_recall
        )
        
        if not result["success"]:
            error_msg = result.get("error", "Unknown error occurred")
            raise HTTPException(status_code=400, detail=error_msg)
        
        return EvaluationResponse(
            results=result["results"],
            average_scores=result["average_scores"],
            model_used=result["model_used"],
            success=result["success"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/set", response_model=RAGConfigResponse)
async def set_rag_config(request: RAGConfigRequest):
    """Set RAG configuration for WebSocket chat"""
    try:
        result = rag_config_service.update_config(
            model=request.model,
            temperature=request.temperature,
            search_type=request.search_type,
            k=request.k,
            search_kwargs=request.search_kwargs
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
        
        return RAGConfigResponse(
            message=result["message"],
            config=result["config"],
            success=result["success"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config", response_model=Dict)
async def get_rag_config():
    """Get current RAG configuration"""
    try:
        config = rag_config_service.get_config()
        return {"config": config, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))