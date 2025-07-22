"""ChromaDB management module"""

import os
import shutil
import streamlit as st
from typing import List, Dict, Any
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma


class ChromaDBManager:
    """ChromaDB management class"""
    
    def __init__(self, db_path: str = "./chroma_db", embedding_model: str = "text-embedding-3-large"):
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
            st.error(f"DB loading failed: {str(e)}")
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
            st.error(f"Document addition failed: {str(e)}")
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
            st.error(f"DB file list query failed: {str(e)}")
            return []
    
    def get_document_metadata(self) -> List[Dict[str, Any]]:
        """Get detailed document metadata with IDs"""
        try:
            if self.db is None:
                return []
            
            collection = self.db._collection
            results = collection.get(include=['metadatas', 'documents'])
            
            documents_info = []
            seen_docs = set()  # 중복 제거용
            
            for i, (doc_id, metadata, content) in enumerate(
                zip(results.get('ids', []), 
                    results.get('metadatas', []), 
                    results.get('documents', []))
            ):
                if metadata and 'source' in metadata:
                    source = metadata['source']
                    filename = os.path.basename(source)
                    
                    # 문서별로 고유 식별자 생성
                    doc_key = (filename, source)
                    if doc_key not in seen_docs:
                        seen_docs.add(doc_key)
                        
                        # 내용 미리보기 (첫 100자)
                        preview = content[:100] + "..." if len(content) > 100 else content
                        
                        documents_info.append({
                            'id': doc_id,
                            'filename': filename,
                            'source': source,
                            'preview': preview,
                            'display_name': f"{filename} ({doc_id[:8]}...)"
                        })
            
            # 파일명으로 정렬
            return sorted(documents_info, key=lambda x: x['filename'])
            
        except Exception as e:
            st.error(f"문서 메타데이터 조회 실패: {str(e)}")
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
            st.error(f"DB deletion failed: {str(e)}")
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