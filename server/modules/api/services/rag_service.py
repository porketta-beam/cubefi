"""RAG system service"""

from typing import List, Dict, Any, Tuple
from ...auto_rag.mod import (
    ChromaDBManager, 
    RAGSystemManager, 
    QuestionGenerationManager,
    EvaluationManager
)
from config.settings import settings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RAGService:
    def __init__(self):
        # ChromaDBManager에 설정된 경로 전달
        chroma_path = str(settings.get_chroma_path())
        self.db_manager = ChromaDBManager(db_path=chroma_path)
        self.rag_manager = RAGSystemManager()
        self.question_manager = QuestionGenerationManager()
        self.evaluation_manager = EvaluationManager()
    
    def chat(self, question: str, model: str = "gpt-4o-mini", temperature: float = 0.0, 
             search_type: str = "similarity", k: int = 3) -> Dict[str, Any]:
        """Get answer to a question using RAG"""
        try:
            # Validate input
            if not question.strip():
                return {
                    "answer": "ERROR: Empty question received. Please provide a valid question.",
                    "contexts": [],
                    "model_used": model,
                    "search_params": {},
                    "success": False
                }
            
            # Check database status
            db_status = self.db_manager.get_status()
            if not db_status["db_exists"]:
                return {
                    "answer": "ERROR: No vector database found. Please upload documents first using /api/documents/sync or /api/documents/upload",
                    "contexts": [],
                    "model_used": model,
                    "search_params": {},
                    "success": False
                }
            
            # Load database if it exists but isn't loaded
            if not db_status["db_loaded"]:
                if not self.db_manager.load_existing_db():
                    return {
                        "answer": "ERROR: Failed to load vector database. Please check the database integrity.",
                        "contexts": [],
                        "model_used": model,
                        "search_params": {},
                        "success": False
                    }
                # Refresh status after loading
                db_status = self.db_manager.get_status()
            
            # Check if database has documents
            if db_status["document_count"] == 0:
                return {
                    "answer": "ERROR: Vector database is empty. Please upload documents first using /api/documents/sync or /api/documents/upload",
                    "contexts": [],
                    "model_used": model,
                    "search_params": {},
                    "success": False
                }
            
            
            # Setup RAG manager
            self.rag_manager.set_llm(model, temperature)
            search_kwargs = {"k": k}
            self.rag_manager.set_retriever(self.db_manager.db, search_type, search_kwargs)
            
            # Get answer
            answer, contexts = self.rag_manager.get_answer(question)
            
            # Validate answer
            if not answer.strip():
                return {
                    "answer": "ERROR: Empty answer generated. Please try rephrasing your question.",
                    "contexts": contexts,
                    "model_used": model,
                    "search_params": {
                        "search_type": search_type,
                        "k": k,
                        "temperature": temperature
                    },
                    "success": False
                }
            
            return {
                "answer": answer,
                "contexts": contexts,
                "model_used": model,
                "search_params": {
                    "search_type": search_type,
                    "k": k,
                    "temperature": temperature
                },
                "success": True
            }
        except Exception as e:
            return {
                "answer": f"❌ Error generating answer: {str(e)}",
                "contexts": [],
                "model_used": model,
                "search_params": {},
                "success": False
            }
    
    def generate_questions(self, model: str = "gpt-4o-mini", temperature: float = 0.9, 
                         num_questions: int = 5) -> Dict[str, Any]:
        """Generate questions from documents"""
        try:
            # Validate input
            if num_questions <= 0:
                return {
                    "questions": [],
                    "model_used": model,
                    "success": False,
                    "error": "❌ Number of questions must be greater than 0."
                }
            
            # Check database status
            db_status = self.db_manager.get_status()
            if not db_status["db_exists"]:
                return {
                    "questions": [],
                    "model_used": model,
                    "success": False,
                    "error": "❌ No vector database found. Please upload documents first using /api/documents/sync or /api/documents/upload"
                }
            
            # Check if database has documents
            if db_status["document_count"] == 0:
                return {
                    "questions": [],
                    "model_used": model,
                    "success": False,
                    "error": "❌ Vector database is empty. Please upload documents first using /api/documents/sync or /api/documents/upload"
                }
            
            # Load database if not already loaded
            if not db_status["db_loaded"]:
                try:
                    self.db_manager.load_existing_db()
                except Exception as e:
                    return {
                        "questions": [],
                        "model_used": model,
                        "success": False,
                        "error": f"❌ Failed to load vector database: {str(e)}"
                    }
            
            # Setup question manager
            self.question_manager.set_llm(model, temperature)
            
            # Generate questions
            questions = self.question_manager.generate_questions(self.db_manager.db, num_questions)
            
            # Validate generated questions
            if not questions:
                return {
                    "questions": [],
                    "model_used": model,
                    "success": False,
                    "error": "❌ No questions could be generated from the documents. Please check if documents contain sufficient text content."
                }
            
            # Filter out empty questions
            valid_questions = [q for q in questions if q.strip()]
            if not valid_questions:
                return {
                    "questions": [],
                    "model_used": model,
                    "success": False,
                    "error": "❌ Generated questions are empty. Please check document content quality."
                }
            
            return {
                "questions": valid_questions,
                "model_used": model,
                "success": True
            }
        except Exception as e:
            return {
                "questions": [],
                "model_used": model,
                "success": False,
                "error": f"❌ Error generating questions: {str(e)}"
            }
    
    def evaluate_rag(self, questions: List[str], model: str = "gpt-4o-mini", 
                    temperature: float = 0.0, search_type: str = "similarity", k: int = 5,
                    use_faithfulness: bool = True, use_answer_relevancy: bool = True,
                    use_context_precision: bool = True, use_context_recall: bool = True) -> Dict[str, Any]:
        """Evaluate RAG system using RAGAS"""
        try:
            # Validate input
            if not questions:
                return {
                    "results": [],
                    "average_scores": {},
                    "model_used": model,
                    "success": False,
                    "error": "❌ No questions provided for evaluation."
                }
            
            # Filter out empty questions
            valid_questions = [q for q in questions if q.strip()]
            if not valid_questions:
                return {
                    "results": [],
                    "average_scores": {},
                    "model_used": model,
                    "success": False,
                    "error": "❌ All provided questions are empty."
                }
            
            # Check database status
            db_status = self.db_manager.get_status()
            if not db_status["db_exists"]:
                return {
                    "results": [],
                    "average_scores": {},
                    "model_used": model,
                    "success": False,
                    "error": "❌ No vector database found. Please upload documents first using /api/documents/sync or /api/documents/upload"
                }
            
            # Check if database has documents
            if db_status["document_count"] == 0:
                return {
                    "results": [],
                    "average_scores": {},
                    "model_used": model,
                    "success": False,
                    "error": "❌ Vector database is empty. Please upload documents first using /api/documents/sync or /api/documents/upload"
                }
            
            # Load database if not already loaded
            if not db_status["db_loaded"]:
                try:
                    self.db_manager.load_existing_db()
                except Exception as e:
                    return {
                        "results": [],
                        "average_scores": {},
                        "model_used": model,
                        "success": False,
                        "error": f"❌ Failed to load vector database: {str(e)}"
                    }
            
            # Validate that at least one metric is selected
            if not any([use_faithfulness, use_answer_relevancy, use_context_precision, use_context_recall]):
                return {
                    "results": [],
                    "average_scores": {},
                    "model_used": model,
                    "success": False,
                    "error": "❌ At least one evaluation metric must be selected."
                }
            
            # Setup RAG manager
            self.rag_manager.set_llm(model, temperature)
            search_kwargs = {"k": k}
            self.rag_manager.set_retriever(self.db_manager.db, search_type, search_kwargs)
            
            # Setup evaluation metrics
            metrics_config = {
                'use_faithfulness': use_faithfulness,
                'use_answer_relevancy': use_answer_relevancy,
                'use_context_precision': use_context_precision,
                'use_context_recall': use_context_recall
            }
            
            # Run evaluation
            results_df = self.evaluation_manager.evaluate_rag_system(
                valid_questions,
                self.db_manager.db,
                self.rag_manager,
                metrics_config
            )
            
            # Validate results
            if results_df.empty:
                return {
                    "results": [],
                    "average_scores": {},
                    "model_used": model,
                    "success": False,
                    "error": "❌ No evaluation results generated. Please check question quality and document content."
                }
            
            # Convert DataFrame to list of dictionaries
            results = results_df.to_dict('records')
            
            # Get average scores
            average_scores = self.evaluation_manager.get_average_scores()
            
            return {
                "results": results,
                "average_scores": average_scores,
                "model_used": model,
                "success": True
            }
        except Exception as e:
            return {
                "results": [],
                "average_scores": {},
                "model_used": model,
                "success": False,
                "error": f"❌ Error during evaluation: {str(e)}"
            }