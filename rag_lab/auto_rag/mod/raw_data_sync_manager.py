"""Raw Data synchronization management module"""

import os
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from .elasticsearch_manager import ElasticsearchManager


class RawDataSyncManager:
    """Raw Data folder and ChromaDB + Elasticsearch synchronization management class"""
    
    def __init__(self, raw_data_path: str = "./raw_data"):
        self.raw_data_path = raw_data_path
        self.supported_extensions = ['.txt', '.pdf']
        
        # Create raw_data folder if it doesn't exist
        if not os.path.exists(self.raw_data_path):
            os.makedirs(self.raw_data_path)
    
    def scan_raw_data_folder(self) -> List[Dict[str, Any]]:
        """Scan all supported files in raw_data folder"""
        files_info = []
        
        try:
            if not os.path.exists(self.raw_data_path):
                return files_info
            
            for root, dirs, files in os.walk(self.raw_data_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_extension = Path(file).suffix.lower()
                    
                    if file_extension in self.supported_extensions:
                        file_stat = os.stat(file_path)
                        
                        file_info = {
                            'filename': file,
                            'full_path': file_path,
                            'relative_path': os.path.relpath(file_path, self.raw_data_path),
                            'extension': file_extension,
                            'size_bytes': file_stat.st_size,
                            'size_mb': round(file_stat.st_size / (1024 * 1024), 2),
                            'modified_time': file_stat.st_mtime,
                            'modified_date': pd.to_datetime(file_stat.st_mtime, unit='s').strftime('%Y-%m-%d %H:%M:%S')
                        }
                        files_info.append(file_info)
            
            return files_info
            
        except Exception as e:
            st.error(f"raw_data folder scan failed: {str(e)}")
            return []
    
    def compare_with_db(self, db_manager) -> Dict[str, List[str]]:
        """Compare files in raw_data folder with files stored in DB"""
        # raw_data folder file list
        raw_files_info = self.scan_raw_data_folder()
        raw_files = [info['filename'] for info in raw_files_info]
        
        # Files stored in DB
        db_files = db_manager.get_files_in_db()
        
        # Comparison results
        sync_status = {
            'new_files': [],      # New files not in DB
            'existing_files': [], # Files already in DB
            'orphaned_files': [], # Files in DB but not in raw_data
            'all_raw_files': raw_files,
            'all_db_files': db_files
        }
        
        # Classify new and existing files
        for filename in raw_files:
            if filename in db_files:
                sync_status['existing_files'].append(filename)
            else:
                sync_status['new_files'].append(filename)
        
        # Find orphaned files
        for filename in db_files:
            if filename not in raw_files:
                sync_status['orphaned_files'].append(filename)
        
        return sync_status
    
    def sync_with_db(self, db_manager, chunk_size: int = 500, chunk_overlap: int = 100, elasticsearch_manager: Optional[ElasticsearchManager] = None) -> bool:
        """Synchronize new files in raw_data folder to ChromaDB and optionally Elasticsearch"""
        try:
            # Check synchronization status
            sync_status = self.compare_with_db(db_manager)
            new_files = sync_status['new_files']
            
            if not new_files:
                st.info("No new files to synchronize. All files are already stored in DB.")
                return True
            
            # Try to load DB if not loaded
            if db_manager.db is None:
                if db_manager.check_db_exists():
                    if not db_manager.load_existing_db():
                        st.error("Failed to load existing DB.")
                        return False
                else:
                    st.info("No existing DB found. Creating new DB with first file.")
            
            # Elasticsearch 연동 상태 확인
            use_elasticsearch = elasticsearch_manager is not None
            if use_elasticsearch:
                es_available = elasticsearch_manager.check_connection()
                if es_available:
                    st.info("✅ Elasticsearch 연결 확인됨 - 병렬 인덱싱 활성화")
                else:
                    st.warning("⚠️ Elasticsearch 연결 실패 - ChromaDB만 사용")
                    use_elasticsearch = False
            
            # Process each new file
            total_added_docs = 0
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            # OpenAI 임베딩 객체 생성 (Elasticsearch용)
            if use_elasticsearch:
                embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
            
            for filename in new_files:
                file_path = os.path.join(self.raw_data_path, filename)
                
                st.info(f"Processing: {filename}")
                
                # Load file
                file_extension = Path(file_path).suffix.lower()
                if file_extension == '.txt':
                    loader = TextLoader(file_path, encoding='utf-8')
                elif file_extension == '.pdf':
                    loader = PyPDFLoader(file_path)
                else:
                    st.warning(f"Unsupported file format: {file_extension}")
                    continue
                
                documents = loader.load_and_split(text_splitter)
                
                if documents:
                    # ChromaDB 처리
                    if not db_manager.check_db_exists():
                        chroma_success = db_manager.create_new_db(documents)
                    else:
                        chroma_success = db_manager.add_documents(documents)
                    
                    if chroma_success:
                        total_added_docs += len(documents)
                        st.success(f"{filename} → ChromaDB: {len(documents)} chunks added")
                        
                        # Elasticsearch 병렬 인덱싱
                        if use_elasticsearch:
                            try:
                                # 임베딩 생성
                                st.info(f"Creating embeddings for {len(documents)} chunks...")
                                document_texts = [doc.page_content for doc in documents]
                                document_embeddings = embeddings.embed_documents(document_texts)
                                
                                # Elasticsearch에 인덱싱
                                es_success = elasticsearch_manager.index_documents(documents, document_embeddings)
                                if es_success:
                                    st.success(f"{filename} → Elasticsearch: {len(documents)} chunks indexed")
                                else:
                                    st.warning(f"{filename} → Elasticsearch: indexing failed (ChromaDB still successful)")
                            except Exception as e:
                                st.warning(f"{filename} → Elasticsearch error: {str(e)} (ChromaDB still successful)")
                    else:
                        st.error(f"{filename}: ChromaDB addition failed")
                        return False
                else:
                    st.warning(f"{filename}: File loading failed")
            
            # 완료 메시지
            if use_elasticsearch:
                st.success(f"🎉 Synchronization complete! Total {total_added_docs} chunks added to both ChromaDB and Elasticsearch.")
            else:
                st.success(f"Synchronization complete! Total {total_added_docs} chunks added to ChromaDB.")
            return True
            
        except Exception as e:
            st.error(f"Synchronization failed: {str(e)}")
            return False
    
    def compare_with_elasticsearch(self, elasticsearch_manager: ElasticsearchManager) -> Dict[str, List[str]]:
        """Compare files in raw_data folder with files stored in Elasticsearch"""
        # raw_data folder file list
        raw_files_info = self.scan_raw_data_folder()
        raw_files = [info['filename'] for info in raw_files_info]
        
        # Files stored in Elasticsearch
        es_files = elasticsearch_manager.get_files_in_index()
        
        # Comparison results
        sync_status = {
            'new_files': [],      # New files not in Elasticsearch
            'existing_files': [], # Files already in Elasticsearch
            'orphaned_files': [], # Files in Elasticsearch but not in raw_data
            'all_raw_files': raw_files,
            'all_es_files': es_files
        }
        
        # Classify new and existing files
        for filename in raw_files:
            if filename in es_files:
                sync_status['existing_files'].append(filename)
            else:
                sync_status['new_files'].append(filename)
        
        # Find orphaned files
        for filename in es_files:
            if filename not in raw_files:
                sync_status['orphaned_files'].append(filename)
        
        return sync_status
    
    def get_sync_status(self, db_manager, elasticsearch_manager: Optional[ElasticsearchManager] = None) -> Dict[str, Any]:
        """Get comprehensive sync status for both ChromaDB and Elasticsearch"""
        status = {
            'raw_data_files': len(self.scan_raw_data_folder()),
            'chromadb': self.compare_with_db(db_manager),
            'elasticsearch': None
        }
        
        if elasticsearch_manager and elasticsearch_manager.check_connection():
            status['elasticsearch'] = self.compare_with_elasticsearch(elasticsearch_manager)
        
        return status