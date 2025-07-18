import streamlit as st
import os
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib
from datasets import Dataset

# Langchain imports
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

# RAGAS imports
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from ragas.evaluation import evaluate

# Load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env', override=True)

from typing import List, Dict, Any

# Matplotlib 한글 및 음수 깨짐 방지 설정
plt.rcParams['axes.unicode_minus'] = False

# Set page config
st.set_page_config(
    page_title="RAG System with RAGAS Evaluation",
    page_icon="🤖",
    layout="wide"
)

# ChromaDB 관리 클래스
class ChromaDBManager:
    """ChromaDB 관리를 위한 클래스"""
    
    def __init__(self, db_path: str = "./chroma_db", embedding_model: str = "text-embedding-3-large"):
        self.db_path = db_path
        self.embedding_model = embedding_model
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.db = None
        
    def check_db_exists(self) -> bool:
        """DB 존재 여부 확인"""
        return os.path.exists(self.db_path) and os.path.isdir(self.db_path) and len(os.listdir(self.db_path)) > 0
    
    def create_new_db(self, documents: list, force_recreate: bool = False) -> bool:
        """새로운 ChromaDB 생성"""
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
            st.error(f"DB 생성 실패: {str(e)}")
            return False
    
    def load_existing_db(self) -> bool:
        """기존 ChromaDB 로드"""
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
            st.error(f"DB 로드 실패: {str(e)}")
            return False
    
    def add_documents(self, documents: list) -> bool:
        """기존 DB에 문서 추가"""
        try:
            if self.db is None:
                if not self.load_existing_db():
                    return False
            
            self.db.add_documents(documents)
            return True
            
        except Exception as e:
            st.error(f"문서 추가 실패: {str(e)}")
            return False
    
    def get_document_count(self) -> int:
        """저장된 문서 개수 반환"""
        try:
            if self.db is None:
                return 0
            return self.db._collection.count()
        except:
            return 0
    
    def get_files_in_db(self) -> List[str]:
        """DB에 저장된 파일명 목록 반환"""
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
            st.error(f"DB 파일 목록 조회 실패: {str(e)}")
            return []
    
    def delete_db(self) -> bool:
        """ChromaDB 완전 삭제"""
        try:
            self.db = None
            import gc
            gc.collect()
            
            if os.path.exists(self.db_path):
                shutil.rmtree(self.db_path)
            
            return True
            
        except Exception as e:
            st.error(f"DB 삭제 실패: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """DB 상태 정보 반환"""
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

# Raw Data 동기화 관리 클래스
class RawDataSyncManager:
    """Raw Data 폴더와 ChromaDB 동기화 관리 클래스"""
    
    def __init__(self, raw_data_path: str = "./raw_data"):
        self.raw_data_path = raw_data_path
        self.supported_extensions = ['.txt', '.pdf']
        
        # raw_data 폴더가 없으면 생성
        if not os.path.exists(self.raw_data_path):
            os.makedirs(self.raw_data_path)
    
    def scan_raw_data_folder(self) -> List[Dict[str, Any]]:
        """raw_data 폴더의 모든 지원 파일 스캔"""
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
            st.error(f"raw_data 폴더 스캔 실패: {str(e)}")
            return []
    
    def compare_with_db(self, db_manager: ChromaDBManager) -> Dict[str, List[str]]:
        """raw_data 폴더의 파일들과 DB에 저장된 파일들을 비교"""
        # raw_data 폴더 파일 목록
        raw_files_info = self.scan_raw_data_folder()
        raw_files = [info['filename'] for info in raw_files_info]
        
        # DB에 저장된 파일 목록
        db_files = db_manager.get_files_in_db()
        
        # 비교 결과
        sync_status = {
            'new_files': [],      # DB에 없는 새 파일들
            'existing_files': [], # DB에 이미 있는 파일들
            'orphaned_files': [], # raw_data에는 없지만 DB에 있는 파일들
            'all_raw_files': raw_files,
            'all_db_files': db_files
        }
        
        # 새 파일과 기존 파일 분류
        for filename in raw_files:
            if filename in db_files:
                sync_status['existing_files'].append(filename)
            else:
                sync_status['new_files'].append(filename)
        
        # 고아 파일 찾기
        for filename in db_files:
            if filename not in raw_files:
                sync_status['orphaned_files'].append(filename)
        
        return sync_status
    
    def sync_with_db(self, db_manager: ChromaDBManager, chunk_size: int = 500, chunk_overlap: int = 100) -> bool:
        """raw_data 폴더의 새 파일들을 DB에 동기화"""
        try:
            # 동기화 상태 확인
            sync_status = self.compare_with_db(db_manager)
            new_files = sync_status['new_files']
            
            if not new_files:
                st.info("동기화할 새 파일이 없습니다. 모든 파일이 이미 DB에 저장되어 있습니다.")
                return True
            
            # DB가 로드되지 않았다면 로드 시도
            if db_manager.db is None:
                if db_manager.check_db_exists():
                    if not db_manager.load_existing_db():
                        st.error("기존 DB 로드에 실패했습니다.")
                        return False
                else:
                    st.info("기존 DB가 없습니다. 첫 번째 파일로 새 DB를 생성합니다.")
            
            # 각 새 파일 처리
            total_added_docs = 0
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            for filename in new_files:
                file_path = os.path.join(self.raw_data_path, filename)
                
                st.info(f"처리 중: {filename}")
                
                # 파일 로드
                file_extension = Path(file_path).suffix.lower()
                if file_extension == '.txt':
                    loader = TextLoader(file_path, encoding='utf-8')
                elif file_extension == '.pdf':
                    loader = PyPDFLoader(file_path)
                else:
                    st.warning(f"지원하지 않는 파일 형식: {file_extension}")
                    continue
                
                documents = loader.load_and_split(text_splitter)
                
                if documents:
                    # DB가 없으면 첫 번째 파일로 생성, 있으면 추가
                    if not db_manager.check_db_exists():
                        success = db_manager.create_new_db(documents)
                    else:
                        success = db_manager.add_documents(documents)
                    
                    if success:
                        total_added_docs += len(documents)
                        st.success(f"{filename}: {len(documents)}개 청크 추가됨")
                    else:
                        st.error(f"{filename}: 추가 실패")
                        return False
                else:
                    st.warning(f"{filename}: 파일 로드 실패")
            
            st.success(f"동기화 완료! 총 {total_added_docs}개 청크가 추가되었습니다.")
            return True
            
        except Exception as e:
            st.error(f"동기화 실패: {str(e)}")
            return False

# 문서 로드 및 분할 함수
def load_and_split_document(file_path: str, chunk_size: int = 500, chunk_overlap: int = 100) -> list:
    """파일을 로드하고 청크로 분할"""
    try:
        file_extension = Path(file_path).suffix.lower()
        
        # 파일 타입에 따른 로더 선택
        if file_extension == '.txt':
            loader = TextLoader(file_path, encoding='utf-8')
        elif file_extension == '.pdf':
            loader = PyPDFLoader(file_path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {file_extension}")
        
        # 텍스트 분할기 설정
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # 문서 로드 및 분할
        documents = loader.load_and_split(text_splitter)
        
        return documents
        
    except Exception as e:
        st.error(f"파일 로드 실패 ({os.path.basename(file_path)}): {str(e)}")
        return []


# Initialize session state
if 'db' not in st.session_state:
    st.session_state.db = None
if 'documents' not in st.session_state:
    st.session_state.documents = None
if 'evaluation_results' not in st.session_state:
    st.session_state.evaluation_results = None
if 'generated_questions' not in st.session_state:
    st.session_state.generated_questions = []
if 'edited_questions' not in st.session_state:
    st.session_state.edited_questions = []
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = ChromaDBManager()
if 'sync_manager' not in st.session_state:
    st.session_state.sync_manager = RawDataSyncManager()

st.title("🤖 RAG 시스템 및 RAGAS 평가")
st.markdown("---")

# 탭 이름
tab1, tab2, tab3, tab4 = st.tabs(["🔄 Raw Data 동기화", "💬 RAG 테스트", "📝 질문 생성하기", "🔍 RAG 평가하기"])

with tab1:
    st.header("Raw Data 동기화")
    
    # 동기화 관리자 가져오기
    sync_manager = st.session_state.sync_manager
    db_manager = st.session_state.db_manager
    
    # VectorDB 상태 표시
    db_status = db_manager.get_status()
    
    st.subheader("📁 VectorDB 상태")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if db_status["db_exists"]:
            st.success("✅ VectorDB 존재")
            st.metric("저장된 문서 수", db_status["document_count"])
        else:
            st.warning("❌ VectorDB 없음")
            st.metric("저장된 문서 수", 0)
    
    with col2:
        st.info(f"📂 저장 경로: {db_status['db_path']}")
        st.info(f"🔤 임베딩 모델: {db_status['embedding_model']}")
    
    with col3:
        if db_status["db_exists"]:
            if st.button("🗑️ VectorDB 삭제", type="secondary"):
                try:
                    with st.spinner("VectorDB를 삭제하는 중입니다..."):
                        # 세션 데이터 초기화
                        st.session_state.documents = None
                        st.session_state.generated_questions = []
                        st.session_state.edited_questions = []
                        st.session_state.evaluation_results = None
                        st.session_state.db = None
                        
                        # DB 삭제
                        success = db_manager.delete_db()
                        
                        if success:
                            st.success("✅ VectorDB가 성공적으로 삭제되었습니다!")
                        else:
                            st.error("❌ VectorDB 삭제에 실패했습니다.")
                            
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"VectorDB 삭제 중 오류 발생: {str(e)}")
    
    st.markdown("---")
    
    st.subheader("📊 동기화 상태")
    
    # 동기화 상태 확인
    if st.button("🔄 동기화 상태 확인"):
        sync_status = sync_manager.compare_with_db(db_manager)
        raw_files_info = sync_manager.scan_raw_data_folder()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("📁 **Raw Data 폴더 상태**")
            st.write(f"- 경로: {sync_manager.raw_data_path}")
            st.write(f"- 총 파일 수: {len(raw_files_info)}개")
            
            if raw_files_info:
                total_size_mb = sum(info['size_mb'] for info in raw_files_info)
                st.write(f"- 총 파일 크기: {total_size_mb:.2f} MB")
                
                # 파일 목록 표시
                st.write("**파일 목록:**")
                for file_info in raw_files_info:
                    st.write(f"  - {file_info['filename']} ({file_info['size_mb']:.2f} MB)")
        
        with col2:
            st.write("🗄️ **ChromaDB 상태**")
            db_status = db_manager.get_status()
            st.write(f"- DB 존재: {'✅' if db_status['db_exists'] else '❌'}")
            st.write(f"- 총 문서 수: {db_status['document_count']}개")
            st.write(f"- 저장된 파일 수: {len(sync_status['all_db_files'])}개")
            
            # 동기화 상태
            st.write("**동기화 상태:**")
            st.write(f"- 새 파일: {len(sync_status['new_files'])}개")
            st.write(f"- 동기화됨: {len(sync_status['existing_files'])}개")
            st.write(f"- 고아 파일: {len(sync_status['orphaned_files'])}개")
            
            # 상세 정보
            if sync_status['new_files']:
                st.write("**추가할 새 파일:**")
                for filename in sync_status['new_files']:
                    st.write(f"  - {filename}")
            
            if sync_status['orphaned_files']:
                st.write("**고아 파일 (raw_data에 없음):**")
                for filename in sync_status['orphaned_files']:
                    st.write(f"  - {filename}")
    
    st.markdown("---")
    
    # 동기화 설정
    st.subheader("⚙️ 동기화 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        sync_chunk_size = st.slider("청크 크기", min_value=100, max_value=2000, value=500, step=50, key="sync_chunk_size")
    
    with col2:
        sync_chunk_overlap = st.slider("청크 중첩", min_value=0, max_value=500, value=100, step=25, key="sync_chunk_overlap")
    
    # 동기화 실행
    if st.button("🚀 동기화 실행", type="primary"):
        with st.spinner("동기화를 실행 중입니다..."):
            success = sync_manager.sync_with_db(
                db_manager=db_manager,
                chunk_size=sync_chunk_size,
                chunk_overlap=sync_chunk_overlap
            )
            
            if success:
                # 세션 상태 업데이트
                st.session_state.db = db_manager.db
                st.rerun()
            else:
                st.error("동기화에 실패했습니다.")
    
    # 추가 정보
    st.info("💡 **사용법:** raw_data 폴더에 .txt 또는 .pdf 파일을 추가한 후 동기화를 실행하세요.")
    st.info(f"📂 **Raw Data 폴더 경로:** {sync_manager.raw_data_path}")
    
    # 기존 DB 관리 기능
    if db_status["db_exists"]:
        st.markdown("---")
        st.subheader("📋 VectorDB 관리")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not db_status["db_loaded"]:
                if st.button("📥 기존 VectorDB 로드", type="primary"):
                    try:
                        with st.spinner("기존 VectorDB를 로드 중입니다..."):
                            success = db_manager.load_existing_db()
                            
                            if success:
                                st.session_state.db = db_manager.db
                                st.success(f"기존 VectorDB를 성공적으로 로드했습니다! (문서 수: {db_status['document_count']})")
                                st.rerun()
                            
                    except Exception as e:
                        st.error(f"VectorDB 로드 중 오류 발생: {str(e)}")
        
        with col2:
            if st.button("📋 저장된 문서 목록 보기"):
                with st.spinner("문서 목록을 불러오는 중입니다..."):
                    files_in_db = db_manager.get_files_in_db()
                    
                    if files_in_db:
                        st.subheader("📚 저장된 파일 목록")
                        st.write(f"총 {len(files_in_db)}개의 파일이 저장되어 있습니다.")
                        st.write(f"총 문서 청크 수: {db_status['document_count']}개")
                        
                        # 파일 목록 표시
                        for i, filename in enumerate(files_in_db, 1):
                            st.write(f"{i}. {filename}")
                    else:
                        st.warning("저장된 파일을 찾을 수 없습니다.")

with tab2:
    st.header("RAG 테스트")
    
    if st.session_state.db is None:
        st.warning("먼저 'Raw Data 동기화' 탭에서 문서를 동기화해 주세요.")
    else:
        # Initialize chat messages
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        
        # RAG Configuration
        st.subheader("RAG 설정")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            chat_model = st.selectbox(
                "Answer Model",
                ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
                index=0,
                key="chat_model"
            )
        
        with col2:
            chat_temperature = st.slider("답변 생성 온도", min_value=0.0, max_value=1.0, value=0.0, step=0.1, key="chat_temp")
        
        with col3:
            search_k = st.slider("검색할 문서 개수", min_value=1, max_value=10, value=3, key="chat_k")
        
        # Clear chat button
        if st.button("채팅 기록 초기화"):
            st.session_state.chat_messages = []
            st.rerun()
        
        # Display chat messages
        st.subheader("채팅")
        
        # Chat container
        chat_container = st.container()
        
        with chat_container:
            for i, message in enumerate(st.session_state.chat_messages):
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.write(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.write(message["content"])
                        if "contexts" in message:
                            with st.expander("참고 문서"):
                                for j, context in enumerate(message["contexts"]):
                                    st.write(f"**문서 {j+1}:**")
                                    st.write(context[:300] + "..." if len(context) > 300 else context)
                                    st.write("---")
        
        # Chat input
        user_question = st.chat_input("질문을 입력하세요...")
        
        if user_question:
            # Add user message to chat
            st.session_state.chat_messages.append({"role": "user", "content": user_question})
            
            try:
                with st.spinner("답변을 생성 중입니다..."):
                    # Create retriever
                    retriever = st.session_state.db.as_retriever(
                        search_type="similarity",
                        search_kwargs={"k": search_k}
                    )
                    
                    # Create LLM instance
                    llm = ChatOpenAI(model=chat_model, temperature=chat_temperature)
                    
                    # Get relevant contexts
                    relevant_docs = retriever.invoke(user_question)
                    contexts = [doc.page_content for doc in relevant_docs]
                    
                    # Create prompt
                    context_text = "\n\n".join(contexts)
                    prompt_text = f"""다음 문맥을 바탕으로 질문에 답변해 주세요. 문맥에 없는 정보는 추측하지 말고, 문맥 내에서만 답변해 주세요.

문맥:
{context_text}

질문: {user_question}

답변:"""
                    
                    # Get answer
                    response = llm.invoke(prompt_text)
                    answer = response.content
                    
                    # Add assistant message to chat
                    st.session_state.chat_messages.append({
                        "role": "assistant", 
                        "content": answer,
                        "contexts": contexts
                    })
                    
                    st.rerun()
                    
            except Exception as e:
                st.error(f"답변 생성 중 오류 발생: {str(e)}")
                # Add error message to chat
                st.session_state.chat_messages.append({
                    "role": "assistant", 
                    "content": f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}"
                })

with tab3:
    st.header("질문 생성하기")
    
    if st.session_state.db is None:
        st.warning("먼저 'Raw Data 동기화' 탭에서 문서를 동기화해 주세요.")
    else:
        # LLM configuration for question generation
        st.subheader("LLM 설정")
        
        col1, col2 = st.columns(2)
        
        with col1:
            question_model = st.selectbox(
                "Question Generation Model",
                ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo"],
                index=0
            )
        
        with col2:
            question_temperature = st.slider("질문 생성 온도", min_value=0.0, max_value=1.0, value=0.9, step=0.1)
        
        # Number of questions
        num_questions = st.slider("생성할 질문 개수", min_value=1, max_value=10, value=5)
        
        # Generate questions
        if st.button("질문 생성", type="primary"):
            try:
                with st.spinner("질문을 생성 중입니다..."):
                    # DB에서 문서 샘플을 가져오기
                    if st.session_state.db is None:
                        st.error("DB가 로드되지 않았습니다. 먼저 동기화를 실행해주세요.")
                    else:
                        # DB에서 샘플 문서들을 가져오기
                        collection = st.session_state.db._collection
                        sample_results = collection.get(limit=min(num_questions * 2, 20), include=['documents'])
                        
                        if not sample_results['documents']:
                            st.error("DB에 문서가 없습니다. 먼저 동기화를 실행해주세요.")
                        else:
                            sample_documents = sample_results['documents']
                            
                            # Create LLM instance
                            llm_for_question = ChatOpenAI(model_name=question_model, temperature=question_temperature)
                            
                            # Generate questions
                            questions = []
                            
                            for i in range(num_questions):
                                # 문서 순환 선택
                                doc_content = sample_documents[i % len(sample_documents)]
                                
                                prompt_text = f"""
다음 문서를 바탕으로 질문을 1개 생성해 주세요.
반드시 질문문장만 출력해 주세요. '질문:'이라는 표현 없이 완전한 한국어 질문 형태로만 작성해 주세요.

문서 내용:
{doc_content[:1000]}...
"""
                                question = llm_for_question.invoke(prompt_text).content
                                questions.append(question)
                            
                            # Store generated questions
                            st.session_state.generated_questions = questions
                            st.session_state.edited_questions = questions.copy()
                            
                            st.success(f"{len(questions)}개의 질문이 생성되었습니다!")
                    
            except Exception as e:
                st.error(f"질문 생성 중 오류 발생: {str(e)}")
        
        # Display and edit questions
        if st.session_state.generated_questions:
            st.subheader("생성된 질문 수정")
            st.write("아래에서 질문을 수정할 수 있습니다:")
            
            # Edit questions
            for i, question in enumerate(st.session_state.generated_questions):
                edited_question = st.text_area(
                    f"질문 {i+1}",
                    value=st.session_state.edited_questions[i] if i < len(st.session_state.edited_questions) else question,
                    key=f"question_{i}"
                )
                
                # Update edited questions in session state
                if len(st.session_state.edited_questions) <= i:
                    st.session_state.edited_questions.append(edited_question)
                else:
                    st.session_state.edited_questions[i] = edited_question
            
            # Add/Remove questions
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("질문 추가"):
                    st.session_state.generated_questions.append("새로운 질문을 입력하세요")
                    st.session_state.edited_questions.append("새로운 질문을 입력하세요")
                    st.rerun()
            
            with col2:
                if st.button("마지막 질문 삭제") and len(st.session_state.generated_questions) > 1:
                    st.session_state.generated_questions.pop()
                    st.session_state.edited_questions.pop()
                    st.rerun()
            
            # Display final questions
            st.subheader("최종 질문 목록")
            for i, question in enumerate(st.session_state.edited_questions):
                st.write(f"{i+1}. {question}")

with tab4:
    st.header("RAG 평가하기")
    
    if st.session_state.db is None:
        st.warning("먼저 'Raw Data 동기화' 탭에서 문서를 동기화해 주세요.")
    elif not st.session_state.edited_questions:
        st.warning("먼저 '질문 생성하기' 탭에서 질문을 생성해 주세요.")
    else:
        # Retriever configuration
        st.subheader("검색기 설정")
        
        col1, col2 = st.columns(2)
        
        with col1:
            search_type = st.selectbox(
                "Search Type",
                ["mmr", "similarity", "similarity_score_threshold"],
                index=0
            )
        
        with col2:
            k = st.slider("검색할 문서 개수 (k)", min_value=1, max_value=20, value=5)
        
        # Additional parameters based on search type
        if search_type == "mmr":
            col1, col2 = st.columns(2)
            with col1:
                lambda_mult = st.slider("람다 가중치", min_value=0.0, max_value=1.0, value=0.25, step=0.05)
            with col2:
                fetch_k = st.slider("Fetch K (검색 후보 수)", min_value=k, max_value=50, value=10)
            
            search_kwargs = {"k": k, "lambda_mult": lambda_mult, "fetch_k": fetch_k}
        
        elif search_type == "similarity_score_threshold":
            score_threshold = st.slider("점수 임계값", min_value=-1.0, max_value=1.0, value=0.5, step=0.1)
            search_kwargs = {"k": k, "score_threshold": score_threshold}
        
        else:
            search_kwargs = {"k": k}
        
        # LLM configuration
        st.subheader("LLM 설정")
        
        answer_model = st.selectbox(
            "Answer Generation Model",
            ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
            index=0
        )
        answer_temperature = st.slider("답변 생성 온도", min_value=0.0, max_value=1.0, value=0.0, step=0.1)
        
        # RAGAS metrics selection
        st.subheader("RAGAS 평가 지표")
        
        col1, col2 = st.columns(2)
        
        with col1:
            use_faithfulness = st.checkbox("정확성(Faithfulness)", value=True)
            use_answer_relevancy = st.checkbox("답변 관련성(Answer Relevancy)", value=True)
        
        with col2:
            use_context_precision = st.checkbox("문맥 정밀도(Context Precision)", value=True)
            use_context_recall = st.checkbox("문맥 재현율(Context Recall)", value=True)
        
        # Display questions to be evaluated
        st.subheader("평가할 질문 목록")
        for i, question in enumerate(st.session_state.edited_questions):
            st.write(f"{i+1}. {question}")
        
        # Evaluate questions
        if st.button("RAG 평가 실행", type="primary"):
            try:
                with st.spinner("질문을 평가 중입니다..."):
                    # Create retriever
                    retriever = st.session_state.db.as_retriever(
                        search_type=search_type,
                        search_kwargs=search_kwargs
                    )
                    
                    # Create LLM instance
                    llm = ChatOpenAI(model=answer_model, temperature=answer_temperature)
                    
                    # Create chain
                    prompt = ChatPromptTemplate.from_template(
                        "Answer the following question based on the context: {context}\nQuestion: {input}"
                    )
                    chain = create_retrieval_chain(
                        retriever=retriever,
                        combine_docs_chain=prompt | llm
                    )
                    
                    # Evaluate with RAGAS
                    st.write("RAGAS로 평가 중...")
                    
                    evaluation_data = {
                        "question": [],
                        "answer": [],
                        "contexts": []
                    }
                    
                    if use_context_precision or use_context_recall:
                        evaluation_data["reference"] = []
                    
                    # Get answers for each question
                    for question in st.session_state.edited_questions:
                        result = chain.invoke({"input": question})
                        answer = result["answer"].content if hasattr(result["answer"], "content") else str(result["answer"])
                        contexts = [doc.page_content for doc in result["context"]]
                        
                        evaluation_data["question"].append(question)
                        evaluation_data["answer"].append(answer)
                        evaluation_data["contexts"].append(contexts)
                        
                        if use_context_precision or use_context_recall:
                            evaluation_data["reference"].append(contexts[0] if contexts else "")
                    
                    # Create evaluation dataset
                    eval_dataset = Dataset.from_dict(evaluation_data)
                    
                    # Select metrics
                    metrics = []
                    if use_faithfulness:
                        metrics.append(faithfulness)
                    if use_answer_relevancy:
                        metrics.append(answer_relevancy)
                    if use_context_precision:
                        metrics.append(context_precision)
                    if use_context_recall:
                        metrics.append(context_recall)
                    
                    # Evaluate
                    results = evaluate(eval_dataset, metrics=metrics)
                    
                    # Create results dataframe
                    results_df = pd.DataFrame({
                        "question": evaluation_data["question"],
                        "answer": evaluation_data["answer"]
                    })
                    
                    for metric in metrics:
                        results_df[metric.name] = results[metric.name]
                    
                    # Store results
                    st.session_state.evaluation_results = results_df
                    
                    st.success("평가가 완료되었습니다!")
                    
            except Exception as e:
                st.error(f"평가 중 오류 발생: {str(e)}")
        
        # Display results
        if st.session_state.evaluation_results is not None:
            st.subheader("평가 결과")
            
            results_df = st.session_state.evaluation_results
            
            # Display dataframe
            st.dataframe(results_df)
            
            # Calculate and display average scores
            metric_columns = [col for col in results_df.columns if col not in ["question", "answer"]]
            if metric_columns:
                avg_scores = results_df[metric_columns].mean()
                
                st.subheader("평균 점수")
                col1, col2 = st.columns(2)
                
                with col1:
                    for i, (metric, score) in enumerate(avg_scores.items()):
                        if i < len(avg_scores) // 2 + len(avg_scores) % 2:
                            st.metric(metric.replace("_", " ").title(), f"{score:.3f}")
                
                with col2:
                    for i, (metric, score) in enumerate(avg_scores.items()):
                        if i >= len(avg_scores) // 2 + len(avg_scores) % 2:
                            st.metric(metric.replace("_", " ").title(), f"{score:.3f}")
                
                # Visualizations
                st.subheader("Visualizations")
                
                # Bar chart for each metric
                for metric in metric_columns:
                    fig, ax = plt.subplots(figsize=(10, 4))
                    sns.barplot(x=results_df.index, y=results_df[metric], ax=ax)
                    ax.set_title(f"질문별 {metric.replace('_', ' ').title()} 점수")
                    ax.set_xlabel("질문 번호")
                    ax.set_ylabel("점수")
                    ax.set_ylim(0, 1)
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig)
                
                # Radar chart for average scores
                if len(metric_columns) > 2:
                    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
                    
                    metrics = avg_scores.index.tolist()
                    scores = avg_scores.values.tolist()
                    
                    # Close the plot
                    scores += scores[:1]
                    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
                    angles += angles[:1]
                    
                    ax.plot(angles, scores, marker='o')
                    ax.fill(angles, scores, alpha=0.25)
                    ax.set_xticks(angles[:-1])
                    ax.set_xticklabels([m.replace('_', ' ').title() for m in metrics])
                    ax.set_ylim(0, 1)
                    ax.set_title("RAGAS 평가 지표 - 평균 점수")
                    
                    st.pyplot(fig)
            
            # Q&A Display
            st.subheader("질문과 답변")
            for i, row in results_df.iterrows():
                with st.expander(f"Q{i+1}: {row['question']}"):
                    st.write("**답변:**")
                    st.write(row['answer'])
                    
                    if metric_columns:
                        st.write("**점수:**")
                        for metric in metric_columns:
                            st.write(f"- {metric.replace('_', ' ').title()}: {row[metric]:.3f}")

# Add sidebar information
st.sidebar.title("ℹ️ 정보")
st.sidebar.markdown("""
### 사용 방법:
1. **Raw Data 동기화 탭**: raw_data 폴더와 자동 동기화
2. **RAG 테스트 탭**: RAG 시스템과 실시간 채팅
3. **질문 생성하기 탭**: 문서 기반 질문 자동 생성
4. **RAG 평가하기 탭**: RAGAS로 정량적 평가

### 동기화 워크플로우:
1. raw_data 폴더에 .txt/.pdf 파일 추가
2. '동기화 상태 확인' 버튼으로 새 파일 확인
3. '동기화 실행' 버튼으로 자동 처리
4. 중복 파일 방지 및 스마트 동기화

### RAGAS 평가 지표:
- **정확성(Faithfulness)**: 답변이 사실에 얼마나 부합하는지
- **답변 관련성(Answer Relevancy)**: 답변이 질문과 얼마나 관련 있는지
- **문맥 정밀도(Context Precision)**: 검색된 문맥이 얼마나 정밀한지
- **문맥 재현율(Context Recall)**: 검색된 문맥이 얼마나 완전한지

### 요구 사항:
- .env 파일에 OpenAI API 키 필요
- 필수 Python 패키지: streamlit, langchain, ragas 등
""")