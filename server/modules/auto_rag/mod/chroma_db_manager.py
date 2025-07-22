"""ChromaDB management module"""

import os
import shutil
from typing import List, Dict, Any
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma

# Streamlit은 조건부 import (웹 인터페이스에서만 사용)
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False
    st = None


class ChromaDBManager:
    """ChromaDB management class"""
    
    def __init__(self, db_path: str = "../../chroma_db", embedding_model: str = "text-embedding-3-large"):
        self.db_path = db_path
        self.embedding_model = embedding_model
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.db = None
        
    def check_db_exists(self) -> bool:
        """Check if DB exists"""
        return os.path.exists(self.db_path) and os.path.isdir(self.db_path) and len(os.listdir(self.db_path)) > 0
    
    def create_new_db(self, documents: list, force_recreate: bool = False) -> bool:
        """Create new ChromaDB"""
        try:
            if force_recreate and self.check_db_exists():
                self.delete_db()
            
            self.db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                collection_name="rag_collection",
                persist_directory=self.db_path
            )
            
            return True
            
        except Exception as e:
            if HAS_STREAMLIT and st:
                st.error(f"DB creation failed: {str(e)}")
            return False
    
    def load_existing_db(self) -> bool:
        """Load existing ChromaDB"""
        try:
            if not self.check_db_exists():
                return False
            
            self.db = Chroma(
                persist_directory=self.db_path,
                embedding_function=self.embeddings,
                collection_name="rag_collection"
            )
            
            return True
            
        except Exception as e:
            if HAS_STREAMLIT and st: st.error(f"DB loading failed: {str(e)}")
            return False
    
    def add_documents(self, documents: list) -> bool:
        """Add documents to existing DB"""
        try:
            if self.db is None:
                if not self.load_existing_db():
                    return False
            
            self.db.add_documents(documents)
            return True
            
        except Exception as e:
            if HAS_STREAMLIT and st: st.error(f"Document addition failed: {str(e)}")
            return False
    
    def get_document_count(self) -> int:
        """Get number of stored documents"""
        try:
            if self.db is None:
                return 0
            return self.db._collection.count()
        except:
            return 0
    
    def get_files_in_db(self) -> List[str]:
        """Get list of filenames stored in DB"""
        try:
            if self.db is None:
                return []
            
            collection = self.db._collection
            results = collection.get(include=['metadatas'])
            
            files_in_db = set()
            for metadata in results['metadatas']:
                if metadata and 'source' in metadata:
                    source = metadata['source']
                    filename = os.path.basename(source)
                    files_in_db.add(filename)
            
            return list(files_in_db)
            
        except Exception as e:
            if HAS_STREAMLIT and st: st.error(f"DB file list query failed: {str(e)}")
            return []
    
    def delete_db(self) -> bool:
        """Delete ChromaDB completely"""
        try:
            self.db = None
            import gc
            gc.collect()
            
            if os.path.exists(self.db_path):
                shutil.rmtree(self.db_path)
            
            return True
            
        except Exception as e:
            if HAS_STREAMLIT and st: st.error(f"DB deletion failed: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get DB status information"""
        exists = self.check_db_exists()
        loaded = self.db is not None
        count = self.get_document_count() if loaded else 0
        
        return {
            'db_exists': exists,
            'db_loaded': loaded,
            'document_count': count,
            'db_path': self.db_path,
            'embedding_model': self.embedding_model
        }