"""RAG configuration service for managing settings"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from auto_rag.mod import ChromaDBManager, RAGSystemManager
# LangChain 네이티브 자동 추적 사용
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

@dataclass
class RAGConfig:
    """RAG configuration data class"""
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    search_type: str = "similarity"
    k: int = 3
    search_kwargs: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.search_kwargs is None:
            self.search_kwargs = {}

class RAGConfigService:
    """RAG configuration management service"""
    
    def __init__(self):
        self.config = RAGConfig()
        self.db_manager = ChromaDBManager()
        self.rag_manager = RAGSystemManager()
        self._setup_rag_system()
    
    def _setup_rag_system(self):
        """Setup RAG system with current configuration"""
        # Setup LLM
        self.rag_manager.set_llm(self.config.model, self.config.temperature)
        
        # Setup retriever if database exists
        db_status = self.db_manager.get_status()
        if db_status["db_exists"]:
            if not db_status["db_loaded"]:
                self.db_manager.load_existing_db()
            
            # Prepare search kwargs
            search_kwargs = {"k": self.config.k}
            search_kwargs.update(self.config.search_kwargs)
            
            self.rag_manager.set_retriever(
                self.db_manager.db, 
                self.config.search_type, 
                search_kwargs
            )
    
    def update_config(self, **kwargs) -> Dict[str, Any]:
        """Update RAG configuration"""
        try:
            # Update configuration
            for key, value in kwargs.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            # Re-setup RAG system
            self._setup_rag_system()
            
            return {
                "message": "RAG configuration updated successfully",
                "config": self.get_config(),
                "success": True
            }
        except Exception as e:
            return {
                "message": f"Error updating configuration: {str(e)}",
                "success": False
            }
    
    def get_config(self) -> Dict[str, Any]:
        """Get current RAG configuration"""
        return {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "search_type": self.config.search_type,
            "k": self.config.k,
            "search_kwargs": self.config.search_kwargs
        }
    
    def get_rag_manager(self) -> RAGSystemManager:
        """Get configured RAG manager"""
        return self.rag_manager
    
    def create_rag_chain_stream(self, history: list):
        """Create RAG chain for streaming responses"""
        # LangChain 자동 추적 사용
        from langchain_core.prompts import ChatPromptTemplate
        
        # Check if RAG system is ready
        db_status = self.db_manager.get_status()
        if not db_status["db_exists"]:
            raise Exception("❌ No vector database found. Please upload documents first using /api/documents/sync or /api/documents/upload")
        
        # Check if database has documents
        if db_status["document_count"] == 0:
            raise Exception("❌ Vector database is empty. Please upload documents first using /api/documents/sync or /api/documents/upload")
        
        # Ensure database is loaded
        if not db_status["db_loaded"]:
            try:
                self.db_manager.load_existing_db()
                self._setup_rag_system()
            except Exception as e:
                raise Exception(f"❌ Failed to load vector database: {str(e)}")
        
        # Create prompt template for RAG
        prompt = ChatPromptTemplate.from_template(
            """You are a helpful assistant. Use the following context to answer the user's question.
            If the context doesn't contain relevant information, say so clearly.
            
            Context: {context}
            
            Chat History: {history}
            Question: {input}
            
            Answer:"""
        )
        
        # Get retriever
        retriever = self.rag_manager.retriever
        if not retriever:
            raise Exception("❌ Document retriever not configured. Please check vector database status.")
        
        # Get LLM
        llm = self.rag_manager.llm
        if not llm:
            raise Exception("❌ Language model not configured. Please check RAG configuration.")
        
        # Get current question
        current_question = history[-1]["content"] if history else ""
        if not current_question.strip():
            raise Exception("❌ Empty question received. Please provide a valid question.")
        
        # Retrieve relevant documents (LangChain 자동 추적)
        try:
            docs = retriever.get_relevant_documents(current_question)
            if not docs:
                raise Exception("❌ No relevant documents found for your question. Please check if documents are properly uploaded.")
            
            context = "\n\n".join([doc.page_content for doc in docs])
            if not context.strip():
                raise Exception("❌ Retrieved documents are empty. Please check document content.")
                
        except Exception as e:
            if "❌" in str(e):
                raise e
            else:
                raise Exception(f"❌ Error retrieving relevant documents: {str(e)}")
        
        # Create chain (LangChain 자동 추적)
        chain = prompt | llm
        
        # Return streaming generator (LangChain 자동 추적)
        return chain.stream({
            "input": current_question,
            "history": history,
            "context": context
        })

# Global RAG configuration service instance
rag_config_service = RAGConfigService()