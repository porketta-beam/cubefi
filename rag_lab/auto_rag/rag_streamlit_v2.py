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
import os

# 프로젝트 루트의 .env 파일 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
env_path = os.path.join(project_root, '.env')

load_dotenv(dotenv_path=env_path, override=True)

# LangSmith 설정 확인
print(f"LangSmith API Key loaded: {'Yes' if os.getenv('LANGSMITH_API_KEY') else 'No'}")
print(f"LangSmith Project: {os.getenv('LANGSMITH_PROJECT', 'Not set')}")

# LangSmith 강제 초기화 (Streamlit 환경에서 필요)
if os.getenv('LANGSMITH_API_KEY'):
    from langsmith import Client
    try:
        langsmith_client = Client()
        print(f"LangSmith client initialized successfully")
    except Exception as e:
        print(f"LangSmith client initialization failed: {e}")

from typing import List, Dict, Any
from mod import (
    ChromaDBManager,
    RawDataSyncManager,
    RAGSystemManager,
    QuestionGenerationManager,
    EvaluationManager,
    ChatInterfaceManager,
    VisualizationUtils,
    WorkflowStatusManager,
    ElasticsearchManager,
    HybridSearchManager
)
# LangChain 네이티브 자동 추적 사용

# Matplotlib 한글 및 음수 깨짐 방지 설정
plt.rcParams['axes.unicode_minus'] = False

# Set page config
st.set_page_config(
    page_title="RAG System with RAGAS Evaluation",
    page_icon="🤖",
    layout="wide"
)

# Document loading and splitting function
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
if 'rag_manager' not in st.session_state:
    st.session_state.rag_manager = RAGSystemManager()
if 'question_manager' not in st.session_state:
    st.session_state.question_manager = QuestionGenerationManager()
if 'evaluation_manager' not in st.session_state:
    st.session_state.evaluation_manager = EvaluationManager()
if 'chat_interface' not in st.session_state:
    st.session_state.chat_interface = ChatInterfaceManager()
if 'workflow_manager' not in st.session_state:
    st.session_state.workflow_manager = WorkflowStatusManager()
if 'elasticsearch_manager' not in st.session_state:
    st.session_state.elasticsearch_manager = ElasticsearchManager()
if 'hybrid_search_manager' not in st.session_state:
    st.session_state.hybrid_search_manager = None  # Initialized later when both managers are ready

st.title("🤖 RAG 시스템 및 RAGAS 평가")
st.markdown("---")

# 탭 이름
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📁 Raw Data 관리", "🔄 Raw Data 동기화", "🔍 하이브리드 검색", "💬 RAG 테스트", "📝 질문 생성하기", "🔍 RAG 평가하기"])

with tab1:
    st.header("📁 Raw Data 관리")
    
    # Raw Data 폴더 관리 기능
    sync_manager = st.session_state.sync_manager
    raw_data_path = sync_manager.raw_data_path
    
    st.subheader("📂 폴더 정보")
    st.info(f"**Raw Data 폴더 경로:** {raw_data_path}")
    
    # 폴더가 없으면 생성
    if not os.path.exists(raw_data_path):
        os.makedirs(raw_data_path)
        st.success("✅ Raw Data 폴더가 생성되었습니다.")
    
    # 파일 목록 가져오기
    def get_file_list():
        """raw_data 폴더의 파일 목록을 가져옴"""
        if not os.path.exists(raw_data_path):
            return []
        
        files = []
        for filename in os.listdir(raw_data_path):
            file_path = os.path.join(raw_data_path, filename)
            if os.path.isfile(file_path):
                file_stat = os.stat(file_path)
                file_size_mb = file_stat.st_size / (1024 * 1024)
                files.append({
                    'filename': filename,
                    'size_mb': file_size_mb,
                    'modified_time': file_stat.st_mtime,
                    'file_path': file_path
                })
        return sorted(files, key=lambda x: x['modified_time'], reverse=True)
    
    # 파일 목록 표시
    st.subheader("📋 파일 목록")
    
    files = get_file_list()
    
    if files:
        # 파일 정보를 DataFrame으로 변환
        import datetime
        file_data = []
        for file_info in files:
            modified_time = datetime.datetime.fromtimestamp(file_info['modified_time'])
            file_data.append({
                '파일명': file_info['filename'],
                '크기 (MB)': f"{file_info['size_mb']:.2f}",
                '수정일': modified_time.strftime('%Y-%m-%d %H:%M:%S'),
                '형식': os.path.splitext(file_info['filename'])[1].upper()
            })
        
        df = pd.DataFrame(file_data)
        st.dataframe(df, use_container_width=True)
        
        # 전체 통계
        total_files = len(files)
        total_size = sum(f['size_mb'] for f in files)
        st.info(f"📊 **총 {total_files}개 파일, 전체 크기: {total_size:.2f} MB**")
        
    else:
        st.warning("📁 폴더에 파일이 없습니다.")
    
    st.markdown("---")
    
    # 파일 업로드 섹션
    st.subheader("📤 파일 업로드")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**단일 파일 업로드**")
        uploaded_file = st.file_uploader(
            "파일을 선택하세요",
            type=['txt', 'pdf'],
            key="single_upload"
        )
        
        if uploaded_file is not None:
            if st.button("💾 단일 파일 저장", key="save_single"):
                try:
                    file_path = os.path.join(raw_data_path, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.success(f"✅ '{uploaded_file.name}' 파일이 저장되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 파일 저장 중 오류 발생: {str(e)}")
    
    with col2:
        st.write("**다중 파일 업로드**")
        uploaded_files = st.file_uploader(
            "여러 파일을 선택하세요",
            type=['txt', 'pdf'],
            accept_multiple_files=True,
            key="multiple_upload"
        )
        
        if uploaded_files:
            if st.button("💾 다중 파일 저장", key="save_multiple"):
                try:
                    saved_count = 0
                    for uploaded_file in uploaded_files:
                        file_path = os.path.join(raw_data_path, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        saved_count += 1
                    
                    st.success(f"✅ {saved_count}개 파일이 저장되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 파일 저장 중 오류 발생: {str(e)}")
    
    st.markdown("---")
    
    # 파일 삭제 섹션
    st.subheader("🗑️ 파일 삭제")
    
    if files:
        st.write("삭제할 파일을 선택하세요:")
        
        # 파일 선택 체크박스
        selected_files = []
        for file_info in files:
            if st.checkbox(
                f"{file_info['filename']} ({file_info['size_mb']:.2f} MB)",
                key=f"delete_{file_info['filename']}"
            ):
                selected_files.append(file_info)
        
        if selected_files:
            st.warning(f"⚠️ **{len(selected_files)}개 파일이 선택되었습니다.**")
            
            # 선택된 파일 목록 표시
            st.write("**선택된 파일:**")
            for file_info in selected_files:
                st.write(f"- {file_info['filename']} ({file_info['size_mb']:.2f} MB)")
            
            # 삭제 확인 및 실행
            if st.button("🗑️ 선택된 파일 삭제", type="secondary"):
                try:
                    deleted_count = 0
                    for file_info in selected_files:
                        os.remove(file_info['file_path'])
                        deleted_count += 1
                    
                    st.success(f"✅ {deleted_count}개 파일이 삭제되었습니다!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ 파일 삭제 중 오류 발생: {str(e)}")
        else:
            st.info("📝 삭제할 파일을 선택해주세요.")
    else:
        st.info("📁 삭제할 파일이 없습니다.")
    
    st.markdown("---")
    
    # 사용법 안내
    st.subheader("💡 사용법")
    st.info("""
    **지원 파일 형식:**
    - 📄 텍스트 파일 (.txt)
    - 📕 PDF 파일 (.pdf)
    
    **파일 크기 제한:**
    - 단일 파일: 최대 200MB
    - 전체 폴더: 최대 1GB
    
    **주의사항:**
    - 파일 삭제는 되돌릴 수 없습니다
    - 파일명에 특수문자 사용을 피해주세요
    """)

with tab2:
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
    
    # Elasticsearch 연동 옵션
    st.subheader("🔍 Elasticsearch 연동")
    
    col1, col2 = st.columns(2)
    
    with col1:
        enable_elasticsearch = st.checkbox(
            "Elasticsearch 병렬 인덱싱 활성화", 
            value=False,
            help="ChromaDB와 함께 Elasticsearch에도 동시에 인덱싱합니다. 하이브리드 검색을 위해 필요합니다."
        )
    
    with col2:
        if enable_elasticsearch:
            elasticsearch_manager = st.session_state.elasticsearch_manager
            es_connection_ok = elasticsearch_manager.check_connection()
            
            if es_connection_ok:
                st.success("✅ Elasticsearch 연결 확인")
                doc_count = elasticsearch_manager.get_document_count()
                st.info(f"현재 문서 수: {doc_count}")
            else:
                st.warning("⚠️ Elasticsearch 연결 실패")
                st.info("Docker로 Elasticsearch를 실행해주세요")
    
    # 동기화 실행
    if st.button("🚀 동기화 실행", type="primary"):
        # Update workflow status to in_progress
        workflow_manager = st.session_state.workflow_manager
        workflow_manager.update_step_status("embedding", "in_progress", 0)
        
        with st.spinner("동기화를 실행 중입니다..."):
            # Check sync status first
            sync_status = sync_manager.compare_with_db(db_manager)
            new_files_count = len(sync_status['new_files'])
            
            workflow_manager.update_step_status("embedding", "in_progress", 25, {
                "new_files": new_files_count,
                "document_count": db_manager.get_document_count()
            })
            
            # Elasticsearch 매니저 준비
            elasticsearch_mgr = None
            if enable_elasticsearch:
                elasticsearch_mgr = st.session_state.elasticsearch_manager
                if not elasticsearch_mgr.check_connection():
                    st.warning("Elasticsearch 연결이 실패했습니다. ChromaDB만 사용합니다.")
                    elasticsearch_mgr = None
            
            success = sync_manager.sync_with_db(
                db_manager=db_manager,
                chunk_size=sync_chunk_size,
                chunk_overlap=sync_chunk_overlap,
                elasticsearch_manager=elasticsearch_mgr
            )
            
            if success:
                # 세션 상태 업데이트
                st.session_state.db = db_manager.db
                final_doc_count = db_manager.get_document_count()
                
                # Update workflow status to completed
                workflow_manager.update_step_status("embedding", "completed", 100, {
                    "document_count": final_doc_count,
                    "new_files": new_files_count
                })
                
                st.rerun()
            else:
                # Update workflow status to error
                workflow_manager.update_step_status("embedding", "error", 0, error="동기화에 실패했습니다.")
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

with tab3:
    st.header("🔍 하이브리드 검색")
    
    # Initialize hybrid search manager
    db_manager = st.session_state.db_manager
    elasticsearch_manager = st.session_state.elasticsearch_manager
    
    if st.session_state.hybrid_search_manager is None and st.session_state.db is not None:
        st.session_state.hybrid_search_manager = HybridSearchManager(
            chroma_manager=db_manager,
            elasticsearch_manager=elasticsearch_manager
        )
    
    hybrid_search_manager = st.session_state.hybrid_search_manager
    
    if st.session_state.db is None:
        st.warning("먼저 'Raw Data 동기화' 탭에서 문서를 동기화해 주세요.")
    else:
        # Search system status
        st.subheader("🔍 검색 시스템 상태")
        
        if hybrid_search_manager:
            search_status = hybrid_search_manager.get_search_status()
            availability = search_status['availability']
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Vector 검색", "✅ 사용 가능" if availability['vector_search'] else "❌ 사용 불가")
                if availability['vector_search']:
                    chroma_status = search_status['chromadb_status']
                    st.info(f"문서 수: {chroma_status['document_count']}")
            
            with col2:
                st.metric("BM25 검색", "✅ 사용 가능" if availability['bm25_search'] else "❌ 사용 불가")
                if availability['bm25_search']:
                    es_status = search_status['elasticsearch_status']
                    st.info(f"문서 수: {es_status['document_count']}")
                else:
                    st.warning("Elasticsearch 연결 필요")
            
            with col3:
                st.metric("하이브리드 검색", "✅ 사용 가능" if availability['hybrid_search'] else "❌ 사용 불가")
                if availability['hybrid_search']:
                    st.success("BM25 + Vector 융합 검색")
                else:
                    st.warning("ChromaDB와 Elasticsearch 모두 필요")
        
        st.markdown("---")
        
        # Search configuration
        st.subheader("⚙️ 검색 설정")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_type = st.selectbox(
                "검색 방법",
                ["hybrid", "vector", "bm25"],
                index=0,
                help="hybrid: BM25+Vector 융합, vector: 의미 검색, bm25: 키워드 검색"
            )
        
        with col2:
            search_k = st.slider("검색 결과 수", min_value=1, max_value=20, value=5)
        
        with col3:
            if search_type == "hybrid":
                rrf_k = st.slider("RRF 상수", min_value=10, max_value=100, value=60, 
                                help="Reciprocal Rank Fusion 상수 (낮을수록 상위 결과 강조)")
        
        # Search interface
        st.subheader("🔍 검색 테스트")
        
        search_query = st.text_input("검색어를 입력하세요:", placeholder="예: 법인세율이 얼마인가요?")
        
        if st.button("🔍 검색 실행", type="primary") and search_query:
            if hybrid_search_manager:
                try:
                    with st.spinner("검색 중..."):
                        # Execute search
                        if search_type == "hybrid":
                            results, search_info = hybrid_search_manager.search(
                                search_query, search_type, search_k, rrf_k
                            )
                        else:
                            results, search_info = hybrid_search_manager.search(
                                search_query, search_type, search_k
                            )
                        
                        # Display search info
                        st.subheader("📊 검색 결과 정보")
                        info_col1, info_col2 = st.columns(2)
                        
                        with info_col1:
                            st.metric("검색 방법", search_info.get('search_type', search_type))
                            st.metric("총 결과 수", len(results))
                        
                        with info_col2:
                            if 'search_methods_used' in search_info:
                                methods = ", ".join(search_info['search_methods_used'])
                                st.metric("사용된 방법", methods)
                            if search_type == "hybrid" and 'rrf_k' in search_info:
                                st.metric("RRF 상수", search_info['rrf_k'])
                        
                        # Display results
                        if results:
                            st.subheader("🎯 검색 결과")
                            
                            for i, result in enumerate(results):
                                with st.expander(f"결과 {i+1}: {result['filename']} (점수: {result['score']:.3f})"):
                                    # Result metadata
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write(f"**파일명:** {result['filename']}")
                                        st.write(f"**검색 유형:** {result['search_type']}")
                                    with col2:
                                        st.write(f"**점수:** {result['score']:.3f}")
                                        if 'hybrid_rank' in result:
                                            st.write(f"**하이브리드 순위:** {result['hybrid_rank']}")
                                    
                                    # Show ranking details for hybrid search
                                    if search_type == "hybrid" and 'rrf_score' in result:
                                        st.write("**상세 점수:**")
                                        score_col1, score_col2, score_col3 = st.columns(3)
                                        with score_col1:
                                            if result.get('vector_rank'):
                                                st.write(f"Vector 순위: {result['vector_rank']}")
                                        with score_col2:
                                            if result.get('bm25_rank'):
                                                st.write(f"BM25 순위: {result['bm25_rank']}")
                                        with score_col3:
                                            st.write(f"RRF 점수: {result['rrf_score']:.4f}")
                                    
                                    # Content
                                    st.write("**내용:**")
                                    st.write(result['content'])
                        else:
                            st.warning("검색 결과가 없습니다.")
                            
                except Exception as e:
                    st.error(f"검색 중 오류 발생: {str(e)}")
            else:
                st.error("하이브리드 검색 매니저가 초기화되지 않았습니다.")
        
        # Search comparison tool
        if hybrid_search_manager and search_query:
            st.markdown("---")
            st.subheader("📊 검색 방법 비교")
            
            if st.button("🔍 모든 검색 방법 비교", type="secondary"):
                try:
                    with st.spinner("모든 검색 방법으로 검색 중..."):
                        # Execute all search types
                        vector_results, vector_info = hybrid_search_manager.search(search_query, "vector", search_k)
                        bm25_results, bm25_info = hybrid_search_manager.search(search_query, "bm25", search_k)
                        hybrid_results, hybrid_info = hybrid_search_manager.search(search_query, "hybrid", search_k, 60)
                        
                        # Display comparison
                        st.write("**검색 결과 수 비교:**")
                        comp_col1, comp_col2, comp_col3 = st.columns(3)
                        
                        with comp_col1:
                            st.metric("Vector 검색", len(vector_results))
                        with comp_col2:
                            st.metric("BM25 검색", len(bm25_results))
                        with comp_col3:
                            st.metric("하이브리드 검색", len(hybrid_results))
                        
                        # Show top results from each method
                        st.write("**각 검색 방법의 상위 3개 결과:**")
                        
                        for search_name, results in [("Vector", vector_results[:3]), ("BM25", bm25_results[:3]), ("Hybrid", hybrid_results[:3])]:
                            st.write(f"**{search_name} 검색:**")
                            for i, result in enumerate(results, 1):
                                st.write(f"{i}. {result['filename']} (점수: {result['score']:.3f})")
                                st.write(f"   {result['content'][:100]}...")
                            st.write("")
                        
                except Exception as e:
                    st.error(f"검색 비교 중 오류 발생: {str(e)}")

with tab4:
    st.header("RAG 테스트")
    
    if st.session_state.db is None:
        st.warning("먼저 'Raw Data 동기화' 탭에서 문서를 동기화해 주세요.")
    else:
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
        
        # RAG 매니저 설정
        rag_manager = st.session_state.rag_manager
        rag_manager.set_llm(chat_model, chat_temperature)
        rag_manager.set_retriever(st.session_state.db, "similarity", {"k": search_k})
        
        # 채팅 인터페이스 매니저
        chat_interface = st.session_state.chat_interface
        
        # Clear chat button and LangSmith dashboard
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("채팅 기록 초기화"):
                chat_interface.clear_messages()
                st.rerun()
        
        with col2:
            # LangSmith dashboard link
            langsmith_project = os.getenv("LANGSMITH_PROJECT", "rag_lab_project")
            langsmith_url = f"https://smith.langchain.com/projects/{langsmith_project}"
            st.markdown(f"[🔍 LangSmith 대시보드 열기]({langsmith_url})", unsafe_allow_html=True)
        
        # Display chat messages
        st.subheader("채팅")
        
        # Chat container
        chat_container = st.container()
        
        with chat_container:
            chat_interface.display_messages()
        
        # Chat input
        user_question = st.chat_input("질문을 입력하세요...")
        
        if user_question:
            # Add user message to chat
            chat_interface.add_message("user", user_question)
            
            try:
                with st.spinner("답변을 생성 중입니다..."):
                    # Get answer using RAG manager (LangChain 자동 추적)
                    answer, contexts = rag_manager.get_answer(user_question)
                    
                    # Add assistant message to chat
                    chat_interface.add_message("assistant", answer, contexts)
                    
                    st.rerun()
                    
            except Exception as e:
                st.error(f"답변 생성 중 오류 발생: {str(e)}")
                # Add error message to chat
                chat_interface.add_message("assistant", f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}")

with tab4:
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
        
        # 질문 생성 매니저 설정
        question_manager = st.session_state.question_manager
        question_manager.set_llm(question_model, question_temperature)
        
        # Generate questions
        if st.button("질문 생성", type="primary"):
            try:
                # Update workflow status to in_progress
                workflow_manager = st.session_state.workflow_manager
                workflow_manager.update_step_status("question_generation", "in_progress", 0)
                
                with st.spinner("질문을 생성 중입니다..."):
                    if st.session_state.db is None:
                        workflow_manager.update_step_status("question_generation", "error", 0, 
                                                          error="DB가 로드되지 않았습니다. 먼저 동기화를 실행해주세요.")
                        st.error("DB가 로드되지 않았습니다. 먼저 동기화를 실행해주세요.")
                    else:
                        # Update progress
                        workflow_manager.update_step_status("question_generation", "in_progress", 25, {
                            "model_used": question_model,
                            "target_count": num_questions
                        })
                        
                        # Generate questions using manager
                        questions = question_manager.generate_questions(st.session_state.db, num_questions)
                        
                        # Store generated questions
                        st.session_state.generated_questions = questions
                        st.session_state.edited_questions = questions.copy()
                        
                        # Update workflow status to completed
                        workflow_manager.update_step_status("question_generation", "completed", 100, {
                            "question_count": len(questions),
                            "model_used": question_model
                        })
                        
                        st.success(f"{len(questions)}개의 질문이 생성되었습니다!")
                    
            except Exception as e:
                workflow_manager.update_step_status("question_generation", "error", 0, 
                                                  error=str(e))
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
                    question_manager.add_question("새로운 질문을 입력하세요")
                    st.session_state.generated_questions = question_manager.get_questions()
                    st.session_state.edited_questions = question_manager.get_questions()
                    st.rerun()
            
            with col2:
                if st.button("마지막 질문 삭제") and len(st.session_state.generated_questions) > 1:
                    question_manager.remove_question(len(question_manager.get_questions()) - 1)
                    st.session_state.generated_questions = question_manager.get_questions()
                    st.session_state.edited_questions = question_manager.get_questions()
                    st.rerun()
            
            # Display final questions
            st.subheader("최종 질문 목록")
            for i, question in enumerate(st.session_state.edited_questions):
                st.write(f"{i+1}. {question}")

with tab5:
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
        
        # 평가 매니저 설정
        evaluation_manager = st.session_state.evaluation_manager
        rag_manager = st.session_state.rag_manager
        
        # RAG 매니저 설정
        rag_manager.set_llm(answer_model, answer_temperature)
        rag_manager.set_retriever(st.session_state.db, search_type, search_kwargs)
        
        # Evaluate questions
        if st.button("RAG 평가 실행", type="primary"):
            try:
                # Update workflow status to in_progress
                workflow_manager = st.session_state.workflow_manager
                workflow_manager.update_step_status("evaluation", "in_progress", 0)
                
                with st.spinner("질문을 평가 중입니다..."):
                    st.write("RAGAS로 평가 중...")
                    
                    # Update progress
                    workflow_manager.update_step_status("evaluation", "in_progress", 10, {
                        "total_questions": len(st.session_state.edited_questions),
                        "model_used": answer_model
                    })
                    
                    # 평가 메트릭 설정
                    metrics_config = {
                        'use_faithfulness': use_faithfulness,
                        'use_answer_relevancy': use_answer_relevancy,
                        'use_context_precision': use_context_precision,
                        'use_context_recall': use_context_recall
                    }
                    
                    # Progress update
                    workflow_manager.update_step_status("evaluation", "in_progress", 30)
                    
                    # 평가 실행
                    results_df = evaluation_manager.evaluate_rag_system(
                        st.session_state.edited_questions,
                        st.session_state.db,
                        rag_manager,
                        metrics_config
                    )
                    
                    # Store results
                    st.session_state.evaluation_results = results_df
                    
                    # Get average scores for workflow status
                    avg_scores = evaluation_manager.get_average_scores()
                    
                    # Update workflow status to completed
                    workflow_manager.update_step_status("evaluation", "completed", 100, {
                        "total_questions": len(st.session_state.edited_questions),
                        "model_used": answer_model,
                        "average_scores": avg_scores
                    })
                    
                    st.success("평가가 완료되었습니다!")
                    
            except Exception as e:
                workflow_manager.update_step_status("evaluation", "error", 0, 
                                                  error=str(e))
                st.error(f"평가 중 오류 발생: {str(e)}")
        
        # Display results
        if st.session_state.evaluation_results is not None:
            st.subheader("평가 결과")
            
            results_df = st.session_state.evaluation_results
            
            # Display dataframe
            st.dataframe(results_df)
            
            # Calculate and display average scores
            avg_scores = evaluation_manager.get_average_scores()
            
            if avg_scores:
                st.subheader("평균 점수")
                col1, col2 = st.columns(2)
                
                avg_scores_items = list(avg_scores.items())
                with col1:
                    for i, (metric, score) in enumerate(avg_scores_items):
                        if i < len(avg_scores_items) // 2 + len(avg_scores_items) % 2:
                            st.metric(metric.replace("_", " ").title(), f"{score:.3f}")
                
                with col2:
                    for i, (metric, score) in enumerate(avg_scores_items):
                        if i >= len(avg_scores_items) // 2 + len(avg_scores_items) % 2:
                            st.metric(metric.replace("_", " ").title(), f"{score:.3f}")
                
                # Visualizations
                st.subheader("Visualizations")
                
                # Bar chart for each metric
                metric_columns = [col for col in results_df.columns if col not in ["question", "answer"]]
                for metric in metric_columns:
                    fig = VisualizationUtils.create_metric_bar_chart(results_df, metric)
                    st.pyplot(fig)
                
                # Radar chart for average scores
                radar_fig = VisualizationUtils.create_radar_chart(avg_scores)
                if radar_fig:
                    st.pyplot(radar_fig)
            
            # Q&A Display
            st.subheader("질문과 답변")
            for i, row in results_df.iterrows():
                with st.expander(f"Q{i+1}: {row['question']}"):
                    st.write("**답변:**")
                    st.write(row['answer'])
                    
                    if avg_scores:
                        st.write("**점수:**")
                        for metric in avg_scores.keys():
                            if metric in row:
                                st.write(f"- {metric.replace('_', ' ').title()}: {row[metric]:.3f}")

# Workflow Status Sidebar
def display_workflow_sidebar():
    """Display workflow status in sidebar"""
    workflow_manager = st.session_state.workflow_manager
    
    st.sidebar.title("🔄 RAG Workflow Status")
    st.sidebar.markdown("---")
    
    # Overall progress
    overall_progress = workflow_manager.get_overall_progress()
    st.sidebar.progress(overall_progress / 100)
    st.sidebar.text(f"Overall Progress: {overall_progress:.1f}%")
    
    # Current status
    workflow_status = workflow_manager.get_workflow_status()
    status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅"}.get(workflow_status, "❓")
    st.sidebar.text(f"Status: {status_emoji} {workflow_status.title()}")
    
    st.sidebar.markdown("---")
    
    # Individual steps
    st.sidebar.subheader("📋 Workflow Steps")
    
    # Step 1: Document Embedding
    embedding_info = workflow_manager.get_step_display_info("embedding")
    with st.sidebar.expander(f"{embedding_info['emoji']} Document Embedding", expanded=True):
        st.text(f"Status: {embedding_info['status'].title()}")
        if embedding_info['progress'] > 0:
            st.progress(embedding_info['progress'] / 100)
        st.text(f"Updated: {embedding_info['last_updated']}")
        
        if embedding_info['details']:
            if 'document_count' in embedding_info['details']:
                st.text(f"Documents: {embedding_info['details']['document_count']}")
            if 'new_files' in embedding_info['details']:
                st.text(f"New files: {embedding_info['details']['new_files']}")
        
        if embedding_info['error']:
            st.error(f"Error: {embedding_info['error']}")
    
    # Step 2: Question Generation
    question_info = workflow_manager.get_step_display_info("question_generation")
    with st.sidebar.expander(f"{question_info['emoji']} Question Generation"):
        st.text(f"Status: {question_info['status'].title()}")
        if question_info['progress'] > 0:
            st.progress(question_info['progress'] / 100)
        st.text(f"Updated: {question_info['last_updated']}")
        
        if question_info['details']:
            if 'question_count' in question_info['details']:
                st.text(f"Questions: {question_info['details']['question_count']}")
            if 'model_used' in question_info['details']:
                st.text(f"Model: {question_info['details']['model_used']}")
        
        if question_info['error']:
            st.error(f"Error: {question_info['error']}")
    
    # Step 3: Question Evaluation
    evaluation_info = workflow_manager.get_step_display_info("evaluation")
    with st.sidebar.expander(f"{evaluation_info['emoji']} Question Evaluation"):
        st.text(f"Status: {evaluation_info['status'].title()}")
        if evaluation_info['progress'] > 0:
            st.progress(evaluation_info['progress'] / 100)
        st.text(f"Updated: {evaluation_info['last_updated']}")
        
        if evaluation_info['details']:
            if 'average_scores' in evaluation_info['details']:
                st.text("Average Scores:")
                for metric, score in evaluation_info['details']['average_scores'].items():
                    st.text(f"  {metric}: {score:.3f}")
        
        if evaluation_info['error']:
            st.error(f"Error: {evaluation_info['error']}")
    
    st.sidebar.markdown("---")
    
    # Quick Actions
    st.sidebar.subheader("🚀 Quick Actions")
    
    # Next step suggestion
    next_step = workflow_manager.get_next_step()
    if next_step:
        step_names = {
            "embedding": "Document Sync",
            "question_generation": "Question Generation", 
            "evaluation": "Evaluation"
        }
        st.sidebar.info(f"Next: {step_names.get(next_step, next_step)}")
    
    # Reset workflow button
    if st.sidebar.button("🔄 Reset Workflow"):
        workflow_manager.reset_workflow()
        st.rerun()
    
    # Workflow completion celebration
    if workflow_manager.workflow_completed:
        st.sidebar.success("🎉 Workflow Completed!")
        completion_time = workflow_manager.completion_time
        start_time = workflow_manager.start_time
        if completion_time and start_time:
            duration = completion_time - start_time
            st.sidebar.text(f"Duration: {duration:.1f} seconds")

# Display sidebar
display_workflow_sidebar()