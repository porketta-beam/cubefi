"""RAG API models"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    question: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    search_type: str = "similarity"
    k: int = 3

class ChatResponse(BaseModel):
    answer: str
    contexts: List[str]
    model_used: str
    search_params: Dict[str, Any]

class QuestionGenerationRequest(BaseModel):
    model: str = "gpt-4o-mini"
    temperature: float = 0.9
    num_questions: int = 5

class QuestionGenerationResponse(BaseModel):
    questions: List[str]
    model_used: str
    success: bool

class EvaluationRequest(BaseModel):
    questions: List[str]
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    search_type: str = "similarity"
    k: int = 5
    use_faithfulness: bool = True
    use_answer_relevancy: bool = True
    use_context_precision: bool = True
    use_context_recall: bool = True

class EvaluationResponse(BaseModel):
    results: List[Dict[str, Any]]
    average_scores: Dict[str, float]
    model_used: str
    success: bool

class RAGConfigRequest(BaseModel):
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    search_type: str = "similarity"
    k: int = 3
    search_kwargs: Dict[str, Any] = {}

class RAGConfigResponse(BaseModel):
    message: str
    config: Dict[str, Any]
    success: bool