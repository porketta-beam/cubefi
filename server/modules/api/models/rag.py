"""RAG API models"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    question: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    search_type: str = "similarity"
    k: int = 3
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "국내주식 양도소득세는 어떻게 계산하나요?",
                "model": "gpt-4o-mini",
                "temperature": 0.0,
                "search_type": "similarity",
                "k": 3
            }
        }
    }

class ChatResponse(BaseModel):
    answer: str
    contexts: List[str]
    model_used: str
    search_params: Dict[str, Any]
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "answer": "국내주식 양도소득세는 2024년부터 다음과 같이 적용됩니다. 개인투자자의 경우 연간 250만원을 초과하는 양도소득에 대해 20% 또는 25%의 세율이 적용됩니다.",
                "contexts": [
                    "소득세법 제94조의5에 따르면...",
                    "2024년 세법 개정으로..."
                ],
                "model_used": "gpt-4o-mini",
                "search_params": {
                    "search_type": "similarity",
                    "k": 3,
                    "temperature": 0.0
                }
            }
        }
    }

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
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "questions": [
                    "국내주식 양도소득세는 언제부터 적용되나요?",
                    "ISA 계좌의 세제 혜택은 무엇인가요?",
                    "해외주식 투자 시 세금은 어떻게 계산하나요?"
                ],
                "model": "gpt-4o-mini",
                "temperature": 0.0,
                "search_type": "similarity",
                "k": 5,
                "use_faithfulness": True,
                "use_answer_relevancy": True,
                "use_context_precision": True,
                "use_context_recall": True
            }
        }
    }

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