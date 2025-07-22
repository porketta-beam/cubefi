"""RAG system management module"""

from typing import Tuple, List
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

# 환경변수 로드 (프로젝트 루트의 .env 파일)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path, override=True)


class RAGSystemManager:
    """RAG system overall management class"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.0):
        self.model_name = model_name
        self.temperature = temperature
        self.llm = None
        self.retriever = None
        self.chain = None
        
    def set_llm(self, model_name: str, temperature: float = 0.0):
        """Set LLM"""
        self.model_name = model_name
        self.temperature = temperature
        self.llm = ChatOpenAI(model=model_name, temperature=temperature)
        
    def set_retriever(self, db, search_type: str = "similarity", search_kwargs: dict = None):
        """Set retriever"""
        if search_kwargs is None:
            search_kwargs = {"k": 3}
        
        self.retriever = db.as_retriever(
            search_type=search_type,
            search_kwargs=search_kwargs
        )
        
    def get_answer(self, question: str) -> Tuple[str, List[str]]:
        """Get answer and related documents for question"""
        try:
            # LangSmith 환경변수 디버깅 정보
            langsmith_key = os.getenv('LANGSMITH_API_KEY')
            langsmith_project = os.getenv('LANGSMITH_PROJECT')
            print(f"[RAG Debug] LangSmith Key: {'Set' if langsmith_key else 'Not set'}")
            print(f"[RAG Debug] LangSmith Project: {langsmith_project}")
            
            if self.retriever is None or self.llm is None:
                raise ValueError("Retriever or LLM not set.")
            
            # Search related documents (LangChain 자동 추적)
            print(f"[RAG Debug] Starting document retrieval for: {question[:50]}...")
            relevant_docs = self.retriever.invoke(question)
            contexts = [doc.page_content for doc in relevant_docs]
            print(f"[RAG Debug] Retrieved {len(contexts)} documents")
            
            # Generate answer (LangChain 자동 추적)
            context_text = "\n\n".join(contexts)
            prompt_text = f"""Please answer the question based on the following context. Do not guess information not in the context, only answer based on the context.

Context:
{context_text}

Question: {question}

Answer:"""
            
            print(f"[RAG Debug] Starting LLM invocation...")
            response = self.llm.invoke(prompt_text)
            answer = response.content
            print(f"[RAG Debug] LLM response completed")
            
            return answer, contexts
            
        except Exception as e:
            raise Exception(f"Answer generation failed: {str(e)}")