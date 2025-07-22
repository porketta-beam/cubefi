import streamlit as st
import os
import shutil
import time
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import koreanize_matplotlib
import plotly.graph_objects as go
import plotly.express as px
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
from mod.search_parameter_optimizer import SearchParameterOptimizer
from mod.weight_optimization_experiment import get_weight_experiment
from mod.weight_visualization import get_visualization_manager
# UI modules import
from ui.evaluation_charts import create_quality_analysis_dashboard, QualityMetrics, SearchResultAnalyzer
# LangChain 네이티브 자동 추적 사용

# Matplotlib 한글 및 음수 깨짐 방지 설정
plt.rcParams['axes.unicode_minus'] = False

# Set page config
st.set_page_config(
    page_title="RAG System with RAGAS Evaluation",
    page_icon="🤖",
    layout="wide"
)

# Database connection management functions
def get_db_connection_status():
    """Get comprehensive database connection status"""
    status = {
        'chroma_connected': False,
        'chroma_doc_count': 0,
        'elasticsearch_connected': False,
        'elasticsearch_doc_count': 0,
        'hybrid_search_available': False,
        'db_manager_available': False
    }
    
    # ChromaDB 상태 확인
    if hasattr(st.session_state, 'db_manager') and st.session_state.db_manager:
        status['db_manager_available'] = True
        db_manager = st.session_state.db_manager
        
        # DB 로드 상태 확인 (load_existing_db 호출 여부와 관계없이)
        if db_manager.db is not None:
            status['chroma_connected'] = True
            status['chroma_doc_count'] = db_manager.get_document_count()
            # 세션 상태 동기화
            st.session_state.db = db_manager.db
        elif db_manager.check_db_exists():
            # DB 파일은 존재하지만 로드되지 않은 경우 자동 로드 시도
            try:
                if db_manager.load_existing_db():
                    status['chroma_connected'] = True
                    status['chroma_doc_count'] = db_manager.get_document_count()
                    st.session_state.db = db_manager.db
            except:
                pass
    
    # Elasticsearch 상태 확인
    if hasattr(st.session_state, 'elasticsearch_manager') and st.session_state.elasticsearch_manager:
        es_manager = st.session_state.elasticsearch_manager
        try:
            if es_manager.check_connection():
                status['elasticsearch_connected'] = True
                if es_manager.check_index_exists():
                    # 문서 수 직접 조회
                    doc_count = es_manager.get_document_count()
                    status['elasticsearch_doc_count'] = doc_count
                    
                    # 추가 통계 정보
                    es_stats = es_manager.get_index_stats()
                    if es_stats and es_stats.get('document_count', 0) != doc_count:
                        # 두 방법으로 조회한 결과가 다른 경우 더 정확한 값 사용
                        status['elasticsearch_doc_count'] = max(doc_count, es_stats.get('document_count', 0))
                else:
                    status['elasticsearch_doc_count'] = 0
        except Exception as e:
            # 연결 오류가 아닌 다른 오류는 경고만 표시
            if "connection" not in str(e).lower():
                st.warning(f"Elasticsearch 상태 확인 중 오류: {str(e)}")
            status['elasticsearch_connected'] = False
    
    # Hybrid search 가용성 확인
    if hasattr(st.session_state, 'hybrid_search_manager') and st.session_state.hybrid_search_manager:
        hybrid_manager = st.session_state.hybrid_search_manager
        availability = hybrid_manager.check_search_availability()
        status['hybrid_search_available'] = availability.get('hybrid_search', False)
    
    return status

def ensure_db_connection():
    """Ensure database connections are properly initialized and synchronized"""
    status = get_db_connection_status()
    
    # ChromaDB 연결 보장
    if not status['chroma_connected'] and status['db_manager_available']:
        db_manager = st.session_state.db_manager
        if db_manager.check_db_exists() and db_manager.db is None:
            try:
                db_manager.load_existing_db()
                st.session_state.db = db_manager.db
            except:
                pass
    
    return get_db_connection_status()

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

# Sidebar - DB 상태 모니터링
with st.sidebar:
    st.header("📊 시스템 상태")
    
    # DB 연결 상태 확인
    db_status = ensure_db_connection()
    
    # ChromaDB 상태
    st.subheader("🗄️ ChromaDB")
    if db_status['chroma_connected']:
        st.success(f"✅ 연결됨 ({db_status['chroma_doc_count']}개 청크)")
    else:
        st.error("❌ 연결 안됨")
        if db_status['db_manager_available']:
            db_manager = st.session_state.db_manager
            if db_manager.check_db_exists():
                st.info("💡 DB 파일 존재, '동기화' 탭에서 로드 가능")
            else:
                st.info("💡 '동기화' 탭에서 DB 생성 필요")
    
    # Elasticsearch 상태
    st.subheader("🔍 Elasticsearch")
    if db_status['elasticsearch_connected']:
        st.success(f"✅ 연결됨 ({db_status['elasticsearch_doc_count']}개 청크)")
    else:
        st.error("❌ 연결 안됨")
        st.info("💡 Elasticsearch 서버 확인 필요")
    
    # Hybrid Search 상태
    st.subheader("🔄 하이브리드 검색")
    if db_status['hybrid_search_available']:
        st.success("✅ 사용 가능")
    else:
        st.error("❌ 사용 불가")
        missing = []
        if not db_status['chroma_connected']:
            missing.append("ChromaDB")
        if not db_status['elasticsearch_connected']:
            missing.append("Elasticsearch")
        if missing:
            st.info(f"💡 {', '.join(missing)} 연결 필요")
    
    # 새로고침 버튼
    if st.button("🔄 상태 새로고침", help="데이터베이스 연결 상태를 다시 확인합니다"):
        st.rerun()
    
    st.markdown("---")
    
    # 빠른 액션
    st.subheader("⚡ 빠른 액션")
    if not db_status['chroma_connected']:
        if st.button("📥 ChromaDB 로드", help="기존 ChromaDB를 로드합니다"):
            try:
                if st.session_state.db_manager.load_existing_db():
                    st.success("ChromaDB 로드 완료!")
                    st.rerun()
                else:
                    st.error("ChromaDB 로드 실패")
            except Exception as e:
                st.error(f"오류: {str(e)}")

st.title("🤖 RAG 시스템 및 RAGAS 평가")
st.markdown("---")

# 탭 이름
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📁 문서 관리", 
    "🔄 문서 청킹 및 인덱싱", 
    "🔍 하이브리드 검색", 
    "📊 품질 분석", 
    "⚖️ 가중치 최적화",
    "💬 RAG 테스트", 
    "📝 질문 생성하기", 
    "🔍 RAG 평가하기"
])

with tab1:
    st.header("📁 문서 관리")
    
    # 원본 문서 폴더 관리 기능
    sync_manager = st.session_state.sync_manager
    raw_data_path = sync_manager.raw_data_path
    
    st.subheader("📂 폴더 정보")
    st.info(f"**원본 문서 폴더 경로:** {raw_data_path}")
    
    # 폴더가 없으면 생성
    if not os.path.exists(raw_data_path):
        os.makedirs(raw_data_path)
        st.success("✅ 원본 문서 폴더가 생성되었습니다.")
    
    # 원본 문서 목록 가져오기
    def get_file_list():
        """raw_data 폴더의 원본 문서 목록을 가져옴"""
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
    
    # 원본 문서 목록 표시
    st.subheader("📋 원본 문서 목록")
    
    files = get_file_list()
    
    if files:
        # 문서 정보를 DataFrame으로 변환
        import datetime
        file_data = []
        for file_info in files:
            modified_time = datetime.datetime.fromtimestamp(file_info['modified_time'])
            file_data.append({
                '문서명': file_info['filename'],
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
    st.header("🔄 문서 청킹 및 인덱싱")
    
    # 동기화 관리자 가져오기
    sync_manager = st.session_state.sync_manager
    db_manager = st.session_state.db_manager
    
    # VectorDB 상태 표시
    db_status = db_manager.get_status()
    
    st.subheader("📁 청크 인덱싱 상태")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if db_status["db_exists"]:
            st.success("✅ VectorDB 존재")
            st.metric("인덱싱된 청크 수", db_status["document_count"])
        else:
            st.warning("❌ VectorDB 없음")
            st.metric("인덱싱된 청크 수", 0)
    
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
    
    st.subheader("📊 문서-청크 동기화 상태")
    
    # 동기화 상태 확인
    if st.button("🔄 동기화 상태 확인"):
        sync_status = sync_manager.compare_with_db(db_manager)
        raw_files_info = sync_manager.scan_raw_data_folder()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("📁 **원본 문서 폴더 상태**")
            st.write(f"- 경로: {sync_manager.raw_data_path}")
            st.write(f"- 총 문서 수: {len(raw_files_info)}개")
            
            if raw_files_info:
                total_size_mb = sum(info['size_mb'] for info in raw_files_info)
                st.write(f"- 총 문서 크기: {total_size_mb:.2f} MB")
                
                # 문서 목록 표시
                st.write("**문서 목록:**")
                for file_info in raw_files_info:
                    st.write(f"  - {file_info['filename']} ({file_info['size_mb']:.2f} MB)")
        
        with col2:
            st.write("🗄️ **ChromaDB 상태**")
            db_status = db_manager.get_status()
            st.write(f"- DB 존재: {'✅' if db_status['db_exists'] else '❌'}")
            st.write(f"- 인덱싱된 청크 수: {db_status['document_count']}개")
            st.write(f"- 저장된 문서 수: {len(sync_status['all_db_files'])}개")
            
            # 동기화 상태
            st.write("**동기화 상태:**")
            st.write(f"- 새 문서: {len(sync_status['new_files'])}개")
            st.write(f"- 동기화됨: {len(sync_status['existing_files'])}개")
            st.write(f"- 고아 청크: {len(sync_status['orphaned_files'])}개")
            
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
    st.info(f"📂 **문서 폴더 경로:** {sync_manager.raw_data_path}")
    
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
                                # 세션 상태 동기화
                                st.session_state.db = db_manager.db
                                
                                # 문서 수 다시 계산
                                doc_count = db_manager.get_document_count()
                                
                                st.success(f"✅ 기존 VectorDB를 성공적으로 로드했습니다! (문서 수: {doc_count})")
                                
                                # 상태 새로고침을 위해 rerun
                                st.rerun()
                            else:
                                st.error("❌ VectorDB 로드에 실패했습니다. DB 파일이 손상되었을 수 있습니다.")
                            
                    except Exception as e:
                        st.error(f"❌ VectorDB 로드 중 오류 발생: {str(e)}")
        
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
    
    # Initialize SearchParameterOptimizer
    if not hasattr(st.session_state, 'search_optimizer') or st.session_state.search_optimizer is None:
        if st.session_state.hybrid_search_manager is not None:
            st.session_state.search_optimizer = SearchParameterOptimizer()
    
    hybrid_search_manager = st.session_state.hybrid_search_manager
    
    if st.session_state.db is None:
        st.warning("먼저 '문서 청킹 및 인덱싱' 탭에서 문서를 동기화해 주세요.")
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
        
        # Weight optimization controls for hybrid search
        if search_type == "hybrid" and hybrid_search_manager:
            st.markdown("---")
            st.subheader("⚖️ 검색 가중치 최적화")
            
            # Get current optimizer settings
            optimizer = hybrid_search_manager.parameter_optimizer
            current_weights = optimizer.current_weights
            
            # Weight mode selection
            weight_mode = st.radio(
                "가중치 조정 모드",
                ["auto", "manual"],
                index=0 if current_weights['mode'] == 'auto' else 1,
                help="auto: 쿼리에 따라 자동 최적화, manual: 수동 조정",
                horizontal=True
            )
            
            if weight_mode == "manual":
                st.write("**수동 가중치 조정:**")
                
                # Weight control sliders
                weight_col1, weight_col2 = st.columns(2)
                
                with weight_col1:
                    bm25_weight = st.slider(
                        "BM25 가중치 (키워드 검색)",
                        min_value=0.0, max_value=1.0, 
                        value=current_weights['bm25_weight'],
                        step=0.1,
                        help="키워드 기반 검색의 중요도"
                    )
                
                with weight_col2:
                    vector_weight = st.slider(
                        "Vector 가중치 (의미 검색)",
                        min_value=0.0, max_value=1.0,
                        value=current_weights['vector_weight'],
                        step=0.1,
                        help="의미 기반 검색의 중요도"
                    )
                
                # Weight normalization display
                total_weight = bm25_weight + vector_weight
                if total_weight > 0:
                    norm_bm25 = bm25_weight / total_weight
                    norm_vector = vector_weight / total_weight
                    st.info(f"정규화된 가중치: BM25 {norm_bm25:.3f}, Vector {norm_vector:.3f}")
                
                # Preset buttons
                st.write("**빠른 설정:**")
                preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
                
                with preset_col1:
                    if st.button("균형 (0.5/0.5)"):
                        optimizer.apply_preset("균형")
                        st.rerun()
                
                with preset_col2:
                    if st.button("키워드 중심 (0.7/0.3)"):
                        optimizer.apply_preset("키워드 중심")
                        st.rerun()
                
                with preset_col3:
                    if st.button("의미 중심 (0.3/0.7)"):
                        optimizer.apply_preset("의미 중심")
                        st.rerun()
                
                with preset_col4:
                    if st.button("기본값 복원"):
                        optimizer.reset_to_default()
                        st.rerun()
                
                # Apply weight changes
                if st.button("가중치 적용", type="primary"):
                    if optimizer.set_weights(bm25_weight, vector_weight, mode="manual"):
                        st.success("가중치가 성공적으로 적용되었습니다!")
                        st.rerun()
                    else:
                        st.error("가중치 적용에 실패했습니다.")
            
            else:  # auto mode
                st.write("**자동 최적화 모드:**")
                st.info("🤖 쿼리 유형에 따라 자동으로 최적 가중치를 선택합니다.")
                
                # Show query type analysis if available
                if hasattr(st.session_state, 'last_query_type') and st.session_state.last_query_type:
                    st.write(f"**마지막 쿼리 유형:** {st.session_state.last_query_type}")
                
                # Apply auto mode
                if current_weights['mode'] != 'auto':
                    if st.button("자동 모드 활성화", type="primary"):
                        optimizer.set_weights(
                            current_weights['bm25_weight'], 
                            current_weights['vector_weight'], 
                            mode="auto"
                        )
                        st.success("자동 모드가 활성화되었습니다!")
                        st.rerun()
            
            # Current weight display
            st.write("**현재 설정:**")
            display_col1, display_col2, display_col3 = st.columns(3)
            
            with display_col1:
                st.metric("BM25 가중치", f"{current_weights['bm25_weight']:.3f}")
            with display_col2:
                st.metric("Vector 가중치", f"{current_weights['vector_weight']:.3f}")
            with display_col3:
                st.metric("모드", current_weights['mode'])
        
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
                        
                        if search_type == "hybrid":
                            # Enhanced info display for hybrid search
                            info_col1, info_col2, info_col3, info_col4 = st.columns(4)
                            
                            with info_col1:
                                st.metric("검색 방법", search_info.get('search_type', search_type))
                                st.metric("총 결과 수", len(results))
                            
                            with info_col2:
                                if 'search_methods_used' in search_info:
                                    methods = ", ".join(search_info['search_methods_used'])
                                    st.metric("사용된 방법", methods)
                                if 'rrf_k' in search_info:
                                    st.metric("RRF 상수", search_info['rrf_k'])
                            
                            with info_col3:
                                if 'bm25_weight' in search_info:
                                    st.metric("BM25 가중치", f"{search_info['bm25_weight']:.3f}")
                                if 'vector_results_count' in search_info:
                                    st.metric("Vector 결과", search_info['vector_results_count'])
                            
                            with info_col4:
                                if 'vector_weight' in search_info:
                                    st.metric("Vector 가중치", f"{search_info['vector_weight']:.3f}")
                                if 'bm25_results_count' in search_info:
                                    st.metric("BM25 결과", search_info['bm25_results_count'])
                            
                            # Display weight mode information
                            if 'weight_mode' in search_info:
                                mode_text = "🤖 자동 최적화" if search_info['weight_mode'] == 'auto' else "⚙️ 수동 설정"
                                st.info(f"**가중치 모드:** {mode_text}")
                                
                                # Show query type if auto mode
                                if search_info['weight_mode'] == 'auto' and hasattr(st.session_state, 'last_query_type'):
                                    st.info(f"**감지된 쿼리 유형:** {st.session_state.last_query_type}")
                        else:
                            # Standard info display for non-hybrid search
                            info_col1, info_col2 = st.columns(2)
                            
                            with info_col1:
                                st.metric("검색 방법", search_info.get('search_type', search_type))
                                st.metric("총 결과 수", len(results))
                            
                            with info_col2:
                                if 'search_methods_used' in search_info:
                                    methods = ", ".join(search_info['search_methods_used'])
                                    st.metric("사용된 방법", methods)
                        
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
    st.header("📊 검색 품질 분석")
    
    # 품질 분석을 위한 설정
    st.subheader("🔧 분석 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        analysis_query = st.text_input(
            "분석할 쿼리 입력",
            placeholder="예: 소득세율이 어떻게 되나요?",
            help="품질 분석을 위한 검색 쿼리를 입력하세요"
        )
        
        k_values = st.multiselect(
            "분석할 K 값 선택",
            [1, 3, 5, 10, 20],
            default=[3, 5, 10],
            help="상위 몇 개의 결과를 분석할지 선택하세요"
        )
    
    with col2:
        # Ground truth 문서 선택 (선택적)
        st.subheader("관련 문서 선택 (선택사항)")
        
        # 문서 선택 방법 선택
        selection_method = st.radio(
            "문서 선택 방법:",
            ["문서 목록에서 선택", "직접 ID 입력"],
            help="문서 목록에서 선택하거나 직접 ID를 입력할 수 있습니다."
        )
        
        ground_truth = None
        
        if selection_method == "문서 목록에서 선택":
            # DB 연결 상태 확인 및 보장
            ensure_db_connection()
            
            # ChromaDB에서 문서 목록 가져오기
            db_manager = st.session_state.get('db_manager')
            if db_manager and db_manager.db and hasattr(db_manager, 'get_document_metadata'):
                try:
                    doc_metadata = db_manager.get_document_metadata()
                    
                    if doc_metadata:
                        # 문서 필터링 기능
                        search_filter = st.text_input(
                            "문서 검색 (파일명으로 필터링):",
                            placeholder="예: 세법, 소득세, 2025...",
                            help="입력한 키워드가 포함된 문서만 표시합니다."
                        )
                        
                        # 필터링된 문서 목록 생성
                        filtered_metadata = doc_metadata
                        if search_filter.strip():
                            filtered_metadata = [
                                doc for doc in doc_metadata 
                                if search_filter.lower() in doc['filename'].lower() 
                                or search_filter.lower() in doc['preview'].lower()
                            ]
                        
                        if filtered_metadata:
                            # 문서 선택을 위한 옵션 생성
                            doc_options = {}
                            for doc in filtered_metadata:
                                display_name = f"📄 {doc['filename']} (ID: {doc['id'][:8]}...)"
                                doc_options[display_name] = doc['id']
                            
                            st.write(f"**사용 가능한 문서: {len(filtered_metadata)}개**")
                            
                            selected_docs = st.multiselect(
                                "관련 문서 선택:",
                                options=list(doc_options.keys()),
                                help="쿼리와 관련있는 문서들을 선택하세요. 선택한 문서를 기준으로 정확한 품질 지표를 계산합니다."
                            )
                            
                            # 문서 미리보기 토글
                            if st.checkbox("📖 문서 미리보기 표시", help="선택하기 전에 문서 내용을 미리 볼 수 있습니다."):
                                st.write("**문서 미리보기:**")
                                for doc in filtered_metadata:
                                    with st.expander(f"📄 {doc['filename']} (ID: {doc['id'][:8]}...)"):
                                        st.write(f"**파일명:** {doc['filename']}")
                                        st.write(f"**문서 ID:** `{doc['id']}`")
                                        st.write(f"**파일 경로:** {doc['source']}")
                                        st.write("**내용 미리보기:**")
                                        st.write(doc['preview'])
                        else:
                            st.warning(f"'{search_filter}' 키워드에 해당하는 문서가 없습니다.")
                            selected_docs = []
                        
                        if selected_docs:
                            ground_truth = [doc_options[doc] for doc in selected_docs]
                            st.success(f"✅ 선택된 문서: {len(ground_truth)}개")
                            
                            # 선택된 문서 정보 표시
                            with st.expander("선택된 문서 상세 정보"):
                                for doc_display, doc_id in zip(selected_docs, ground_truth):
                                    doc_info = next((d for d in doc_metadata if d['id'] == doc_id), None)
                                    if doc_info:
                                        st.write(f"**{doc_info['filename']}**")
                                        st.write(f"- ID: `{doc_info['id']}`")
                                        st.write(f"- 미리보기: {doc_info['preview']}")
                                        st.write("---")
                    else:
                        st.warning("인덱싱된 문서가 없습니다. '동기화' 탭에서 문서를 먼저 인덱싱해주세요.")
                except Exception as e:
                    st.error(f"문서 목록 로드 실패: {str(e)}")
                    st.info("직접 ID 입력 방식을 사용해주세요.")
            else:
                st.warning("문서 데이터베이스가 연결되지 않았습니다. '동기화' 탭에서 먼저 초기화해주세요.")
        
        else:  # 직접 ID 입력
            ground_truth_input = st.text_area(
                "관련 문서 ID 직접 입력",
                placeholder="doc1, doc2, doc3 (쉼표로 구분)",
                help="정답 문서 ID를 직접 입력하세요. 없으면 기본적인 분석만 수행됩니다."
            )
            
            if ground_truth_input.strip():
                ground_truth = [doc.strip() for doc in ground_truth_input.split(',') if doc.strip()]
                st.info(f"입력된 문서: {len(ground_truth)}개")
    
    # 분석 실행
    if st.button("🔍 품질 분석 실행", type="primary"):
        if not analysis_query.strip():
            st.error("분석할 쿼리를 입력해주세요.")
        elif not st.session_state.hybrid_search_manager:
            st.error("하이브리드 검색 매니저가 초기화되지 않았습니다. '하이브리드 검색' 탭에서 먼저 초기화해주세요.")
        else:
            with st.spinner("검색 품질을 분석하고 있습니다..."):
                try:
                    # 하이브리드 검색 매니저 가져오기
                    hybrid_manager = st.session_state.hybrid_search_manager
                    
                    # 검색 가용성 확인
                    availability = hybrid_manager.check_search_availability()
                    
                    # 다양한 검색 방법으로 검색 수행
                    search_results = {}
                    
                    if availability['vector_search']:
                        try:
                            vector_results = hybrid_manager.vector_search(analysis_query, k=max(k_values) if k_values else 10)
                            search_results['Vector Search'] = vector_results
                        except Exception as e:
                            st.warning(f"Vector 검색 실패: {str(e)}")
                    
                    if availability['bm25_search']:
                        try:
                            bm25_results = hybrid_manager.bm25_search(analysis_query, k=max(k_values) if k_values else 10)
                            search_results['BM25 Search'] = bm25_results
                        except Exception as e:
                            st.warning(f"BM25 검색 실패: {str(e)}")
                    
                    if availability['hybrid_search']:
                        try:
                            # 현재 최적화 설정 사용
                            optimizer = hybrid_manager.parameter_optimizer
                            if optimizer.mode == "auto":
                                weights = optimizer.get_auto_weights(analysis_query)
                            else:
                                weights = {
                                    "bm25_weight": optimizer.bm25_weight, 
                                    "vector_weight": optimizer.vector_weight
                                }
                            
                            hybrid_results = hybrid_manager.hybrid_search(
                                analysis_query, 
                                k=max(k_values) if k_values else 10,
                                bm25_weight=weights["bm25_weight"],
                                vector_weight=weights["vector_weight"]
                            )
                            search_results['Hybrid Search'] = hybrid_results
                        except Exception as e:
                            st.warning(f"하이브리드 검색 실패: {str(e)}")
                    
                    # 검색 결과가 있는 경우 품질 분석 대시보드 표시
                    if search_results:
                        create_quality_analysis_dashboard(
                            query=analysis_query,
                            search_results=search_results,
                            ground_truth=ground_truth
                        )
                    else:
                        st.error("검색 결과를 가져올 수 없습니다. 검색 시스템을 확인해주세요.")
                
                except Exception as e:
                    st.error(f"품질 분석 중 오류가 발생했습니다: {str(e)}")
    
    # 도움말 섹션
    with st.expander("📖 품질 분석 도움말"):
        st.markdown("""
        ### 품질 분석 지표 설명
        
        **Precision@K**: 상위 K개 결과 중 관련 있는 문서의 비율
        - 값이 높을수록 정확한 결과를 상위에 배치
        
        **Recall@K**: 전체 관련 문서 중 상위 K개에 포함된 문서의 비율  
        - 값이 높을수록 관련 문서를 놓치지 않음
        
        **NDCG@K**: 순위를 고려한 정규화된 누적 이득
        - 상위 결과일수록 높은 가중치, 0~1 사이 값
        
        **MRR**: 첫 번째 관련 문서의 순위 역수
        - 관련 문서가 상위에 있을수록 높은 값
        
        ### 사용 팁
        1. **정답 문서 ID**를 입력하면 더 정확한 분석 가능
        2. **여러 K 값**을 선택해 다양한 관점에서 분석
        3. **검색 방법별 비교**로 최적 방법 선택
        """)

with tab5:
    st.header("⚖️ 가중치 최적화")
    
    # Weight optimization experiment and visualization
    weight_experiment = get_weight_experiment()
    viz_manager = get_visualization_manager()
    
    # Check DB connection
    if st.session_state.db is None or not hasattr(st.session_state, 'hybrid_search_manager'):
        st.warning("먼저 '문서 청킹 및 인덱싱' 탭에서 문서를 동기화하고 하이브리드 검색을 설정해 주세요.")
    else:
        hybrid_search_manager = st.session_state.hybrid_search_manager
        
        # Ensure SearchParameterOptimizer is initialized
        if not hasattr(st.session_state, 'search_optimizer') or st.session_state.search_optimizer is None:
            st.session_state.search_optimizer = SearchParameterOptimizer()
        
        # Sidebar for experiment control
        with st.sidebar:
            st.subheader("🧪 실험 설정")
            
            # Log file path
            log_path = st.text_input("로그 파일 경로", value="./weight_search.log")
            
            # Clear log button
            if st.button("🗑️ 로그 파일 삭제"):
                if weight_experiment.clear_experiment_log():
                    st.success("로그 파일이 삭제되었습니다.")
                else:
                    st.error("로그 파일 삭제에 실패했습니다.")
            
            st.markdown("---")
            
            # Experiment parameters
            st.subheader("실험 파라미터")
            min_weight = st.slider("최소 가중치", 0.0, 1.0, 0.0, 0.1)
            max_weight = st.slider("최대 가중치", 0.0, 1.0, 1.0, 0.1) 
            step_size = st.selectbox("스텝 크기", [0.1, 0.2, 0.25, 0.5], index=0)
            max_workers = st.slider("병렬 처리 수", 1, 5, 3)
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Tab selection for manual vs automated
            tuning_mode = st.radio(
                "튜닝 모드 선택:",
                ["🎛️ 수동 튜닝", "🧪 자동 실험"],
                horizontal=True
            )
            
            if tuning_mode == "🎛️ 수동 튜닝":
                st.subheader("🎛️ 수동 가중치 튜닝")
                
                # Check for preset values first
                if 'preset_values' in st.session_state and st.session_state.preset_values:
                    current_bm25, current_vector = st.session_state.preset_values
                    # Clear preset values after using them
                    st.session_state.preset_values = None
                else:
                    # Get current optimizer settings
                    search_optimizer = st.session_state.get('search_optimizer')
                    if search_optimizer:
                        current_bm25 = search_optimizer.bm25_weight
                        current_vector = search_optimizer.vector_weight
                    else:
                        current_bm25 = 0.5
                        current_vector = 0.5
                
                # Manual weight sliders
                manual_col1, manual_col2 = st.columns(2)
                
                with manual_col1:
                    manual_bm25 = st.slider(
                        "BM25 가중치",
                        min_value=0.0,
                        max_value=1.0,
                        value=current_bm25,
                        step=0.05,
                        key="manual_bm25"
                    )
                
                with manual_col2:
                    manual_vector = st.slider(
                        "벡터 가중치", 
                        min_value=0.0,
                        max_value=1.0,
                        value=current_vector,
                        step=0.05,
                        key="manual_vector"
                    )
                
                # Normalized weights display
                total_weight = manual_bm25 + manual_vector
                if total_weight > 0:
                    norm_bm25 = manual_bm25 / total_weight
                    norm_vector = manual_vector / total_weight
                else:
                    norm_bm25 = 0.5
                    norm_vector = 0.5
                
                st.info(f"정규화된 가중치: BM25 {norm_bm25:.3f} | 벡터 {norm_vector:.3f}")
                
                # Weight presets
                st.write("**가중치 프리셋:**")
                preset_cols = st.columns(5)
                
                presets = {
                    "균형": (0.5, 0.5),
                    "키워드": (0.7, 0.3), 
                    "의미": (0.3, 0.7),
                    "BM25": (1.0, 0.0),
                    "벡터": (0.0, 1.0)
                }
                
                for i, (preset_name, (bm25, vector)) in enumerate(presets.items()):
                    with preset_cols[i]:
                        if st.button(f"{preset_name}", key=f"preset_{preset_name}"):
                            # Immediately apply preset to SearchParameterOptimizer
                            search_optimizer = st.session_state.get('search_optimizer')
                            if search_optimizer:
                                success = search_optimizer.set_weights(bm25, vector, mode="manual")
                                if success:
                                    st.success(f"✅ {preset_name} 프리셋 적용! (BM25: {search_optimizer.bm25_weight:.3f}, 벡터: {search_optimizer.vector_weight:.3f})")
                                else:
                                    st.error("❌ 프리셋 적용에 실패했습니다.")
                            # Also store for slider update
                            st.session_state.preset_values = (bm25, vector)
                            st.rerun()
                
                # Apply weights button
                if st.button("⚙️ 가중치 적용", type="primary"):
                    if search_optimizer:
                        success = search_optimizer.set_weights(manual_bm25, manual_vector, mode="manual")
                        if success:
                            # Display the actual weights stored in optimizer
                            actual_bm25 = search_optimizer.bm25_weight
                            actual_vector = search_optimizer.vector_weight
                            st.success(f"✅ 가중치가 적용되었습니다! (BM25: {actual_bm25:.3f}, 벡터: {actual_vector:.3f})")
                        else:
                            st.error("❌ 가중치 적용에 실패했습니다.")
                    else:
                        st.warning("검색 최적화 매니저를 찾을 수 없습니다.")
                
                # Real-time test section
                st.markdown("---")
                st.subheader("🔍 실시간 테스트")
                
                test_query = st.text_input(
                    "테스트 쿼리:",
                    placeholder="예: 소득세 공제 방법",
                    key="manual_test_query"
                )
                
                test_k = st.slider("검색 결과 수", 1, 10, 5, key="manual_test_k")
                
                if st.button("🚀 검색 테스트", disabled=not test_query):
                    if test_query:
                        try:
                            start_time = time.time()
                            
                            # Apply current weights temporarily for test
                            # Use weights from search optimizer if available, otherwise use normalized UI weights
                            search_optimizer = st.session_state.get('search_optimizer')
                            if search_optimizer:
                                test_bm25 = search_optimizer.bm25_weight
                                test_vector = search_optimizer.vector_weight
                            else:
                                test_bm25 = norm_bm25
                                test_vector = norm_vector
                            
                            results, search_info = hybrid_search_manager.hybrid_search(
                                query=test_query,
                                k=test_k,
                                bm25_weight=test_bm25,
                                vector_weight=test_vector
                            )
                            
                            search_time = (time.time() - start_time) * 1000
                            
                            st.success(f"✅ 검색 완료! ({search_time:.1f}ms, {len(results)}개 결과)")
                            st.info(f"사용된 가중치: BM25 {test_bm25:.3f} | 벡터 {test_vector:.3f}")
                            
                            # Display results
                            if results:
                                st.write("**검색 결과:**")
                                for i, result in enumerate(results, 1):
                                    with st.expander(f"{i}. {result.get('filename', 'Unknown')} (점수: {result.get('score', 0):.3f})"):
                                        st.write(result.get('content', '')[:300] + "..." if len(result.get('content', '')) > 300 else result.get('content', ''))
                            else:
                                st.warning("검색 결과가 없습니다.")
                                
                        except Exception as e:
                            st.error(f"검색 테스트 실패: {str(e)}")
                
                # Performance comparison section
                st.markdown("---")
                st.subheader("📊 성능 비교")
                
                if st.button("🔬 다중 가중치 비교 테스트"):
                    if test_query:
                        try:
                            comparison_results = []
                            test_weights = [
                                ("균형", 0.5, 0.5),
                                ("키워드 중심", 0.7, 0.3),
                                ("의미 중심", 0.3, 0.7),
                                ("현재 설정", norm_bm25, norm_vector)
                            ]
                            
                            progress_bar = st.progress(0)
                            
                            for i, (name, bm25_w, vector_w) in enumerate(test_weights):
                                start_time = time.time()
                                
                                results, _ = hybrid_search_manager.hybrid_search(
                                    query=test_query,
                                    k=test_k,
                                    bm25_weight=bm25_w,
                                    vector_weight=vector_w
                                )
                                
                                search_time = (time.time() - start_time) * 1000
                                
                                comparison_results.append({
                                    'name': name,
                                    'bm25_weight': bm25_w,
                                    'vector_weight': vector_w,
                                    'result_count': len(results),
                                    'search_time_ms': search_time,
                                    'avg_score': np.mean([r.get('score', 0) for r in results]) if results else 0.0
                                })
                                
                                progress_bar.progress((i + 1) / len(test_weights))
                            
                            # Display comparison table
                            comparison_df = pd.DataFrame(comparison_results)
                            st.dataframe(
                                comparison_df[['name', 'bm25_weight', 'vector_weight', 'result_count', 'search_time_ms', 'avg_score']],
                                use_container_width=True
                            )
                            
                            # Best performer highlight
                            best_idx = comparison_df['avg_score'].idxmax()
                            best_result = comparison_df.iloc[best_idx]
                            st.success(f"🏆 최고 성능: **{best_result['name']}** (평균 점수: {best_result['avg_score']:.4f})")
                            
                        except Exception as e:
                            st.error(f"비교 테스트 실패: {str(e)}")
                    else:
                        st.warning("먼저 테스트 쿼리를 입력해주세요.")
            
            else:  # 자동 실험 모드
                st.subheader("🎯 자동 최적화 실험")
                
                # Test queries input
                st.write("**테스트 쿼리 설정:**")
                use_default_queries = st.checkbox("기본 테스트 쿼리 사용", value=True)
                
                if use_default_queries:
                    test_queries = weight_experiment.get_default_test_queries()
                    st.info(f"기본 테스트 쿼리 {len(test_queries)}개를 사용합니다.")
                    
                    # Show default queries in expander
                    with st.expander("기본 쿼리 목록 보기"):
                        for i, query in enumerate(test_queries, 1):
                            st.write(f"{i}. {query}")
                else:
                    custom_queries = st.text_area(
                        "커스텀 테스트 쿼리 (한 줄에 하나씩)",
                        placeholder="소득세 공제 방법\n부가가치세 신고 기한\n...",
                        height=150
                    )
                    test_queries = [q.strip() for q in custom_queries.split('\n') if q.strip()]
                    
                    if not test_queries:
                        st.warning("테스트 쿼리를 입력해주세요.")
                
                # Run experiment button
                if st.button("🚀 가중치 최적화 실험 실행", type="primary", disabled=not test_queries):
                    if test_queries:
                        # Generate weight combinations
                        weight_combinations = weight_experiment.generate_weight_combinations(
                            min_weight=min_weight,
                            max_weight=max_weight, 
                            step=step_size
                        )
                        
                        st.info(f"생성된 가중치 조합 수: {len(weight_combinations)}개")
                        
                        # Run experiment
                        try:
                            log_file = weight_experiment.run_weight_experiment(
                                hybrid_search_manager=hybrid_search_manager,
                                test_queries=test_queries,
                                weight_combinations=weight_combinations,
                                max_workers=max_workers
                            )
                            
                            st.success(f"✅ 실험 완료! 결과가 {log_file}에 저장되었습니다.")
                            
                            # Automatically load and show initial results
                            if viz_manager.load_weight_data(log_file):
                                st.rerun()
                                
                        except Exception as e:
                            st.error(f"실험 실행 중 오류 발생: {str(e)}")
                    else:
                        st.warning("테스트 쿼리를 설정해주세요.")
        
        with col2:
            st.subheader("📊 실험 현황")
            
            # Load existing data
            if os.path.exists(log_path):
                if viz_manager.load_weight_data(log_path):
                    df = viz_manager.df
                    
                    st.metric("총 실험 수", len(df))
                    
                    if viz_manager.best_combination:
                        best = viz_manager.best_combination
                        st.metric("최고 점수", f"{best['score']:.4f}")
                        
                        st.write("**최적 가중치 조합:**")
                        st.write(f"• BM25: {best['bm25_weight']:.3f}")
                        st.write(f"• Vector: {best['vector_weight']:.3f}")
                        st.write(f"• 응답시간: {best['avg_latency_ms']:.1f}ms")
                        st.write(f"• 오류율: {best['error_rate']:.1%}")
                else:
                    st.info("데이터를 로드할 수 없습니다.")
            else:
                st.info("아직 실험 결과가 없습니다.")
        
        st.markdown("---")
        
        # Visualization section
        if os.path.exists(log_path) and viz_manager.load_weight_data(log_path):
            st.subheader("📈 실험 결과 시각화")
            
            # Visualization options
            viz_col1, viz_col2 = st.columns(2)
            
            with viz_col1:
                chart_type = st.selectbox(
                    "차트 유형 선택",
                    ["2D 산점도", "3D 표면 차트", "히트맵", "성능 비교 차트"],
                    index=0
                )
            
            with viz_col2:
                if chart_type == "2D 산점도":
                    color_metric = st.selectbox(
                        "색상 기준 메트릭",
                        ["score", "avg_latency_ms", "error_rate", "score_std"],
                        index=0
                    )
                elif chart_type == "히트맵":
                    heat_metric = st.selectbox(
                        "히트맵 메트릭",
                        ["score", "avg_latency_ms", "error_rate", "score_std"],
                        index=0
                    )
            
            # Display selected chart
            try:
                if chart_type == "2D 산점도":
                    fig = viz_manager.create_2d_scatter_plot(color_metric)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type == "3D 표면 차트":
                    fig = viz_manager.create_3d_surface_plot()
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type == "히트맵":
                    fig = viz_manager.create_heatmap(heat_metric)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                
                elif chart_type == "성능 비교 차트":
                    fig = viz_manager.create_performance_comparison_chart()
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                        
            except Exception as e:
                st.error(f"차트 생성 중 오류 발생: {str(e)}")
            
            st.markdown("---")
            
            # Analysis insights
            st.subheader("🔍 분석 인사이트")
            
            insights = viz_manager.get_optimization_insights()
            if insights:
                insight_col1, insight_col2, insight_col3 = st.columns(3)
                
                with insight_col1:
                    st.metric("총 실험 조합", insights['total_combinations'])
                    st.metric("최고 점수", f"{insights['best_score']:.4f}")
                
                with insight_col2:
                    st.metric("평균 점수", f"{insights['avg_score']:.4f}")
                    st.metric("점수 표준편차", f"{insights['score_std']:.4f}")
                
                with insight_col3:
                    best = insights['best_combination']
                    st.write("**최적 조합:**")
                    st.write(f"BM25: {best['bm25_weight']:.3f}")
                    st.write(f"Vector: {best['vector_weight']:.3f}")
                
                # Recommendations
                st.subheader("💡 권장사항")
                for i, rec in enumerate(insights.get('recommendations', []), 1):
                    st.write(f"{i}. {rec}")
            
            # Raw data table (expandable)
            with st.expander("📋 실험 데이터 상세보기"):
                df_display = viz_manager.df[[
                    'bm25_weight', 'vector_weight', 'score', 
                    'avg_latency_ms', 'error_rate', 'score_std'
                ]].copy()
                
                # Sort by score descending
                df_display = df_display.sort_values('score', ascending=False)
                
                st.dataframe(
                    df_display,
                    use_container_width=True,
                    height=300
                )
                
                # Download button
                csv = df_display.to_csv(index=False)
                st.download_button(
                    label="📥 CSV 다운로드",
                    data=csv,
                    file_name=f"weight_optimization_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        # Usage instructions
        st.markdown("---")
        st.subheader("💡 사용 방법")
        st.info("""
        **가중치 최적화 실험 순서:**
        1. **실험 파라미터 설정**: 사이드바에서 가중치 범위와 스텝 크기 조정
        2. **테스트 쿼리 준비**: 기본 쿼리 사용 또는 커스텀 쿼리 입력
        3. **실험 실행**: '가중치 최적화 실험 실행' 버튼 클릭
        4. **결과 분석**: 다양한 차트로 결과 시각화 및 분석
        5. **최적 가중치 적용**: 분석 결과를 바탕으로 최적 가중치 선택
        
        **팁:**
        - 스텝 크기가 작을수록 정밀하지만 실험 시간이 길어집니다
        - 병렬 처리 수를 늘리면 실험 속도가 향상됩니다
        - 3D 표면 차트로 전체적인 성능 분포를 파악할 수 있습니다
        """)

with tab6:
    st.header("💬 RAG 테스트")
    
    if st.session_state.db is None:
        st.warning("먼저 '문서 청킹 및 인덱싱' 탭에서 문서를 동기화해 주세요.")
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
            search_k = st.slider("검색할 청크 개수", min_value=1, max_value=10, value=3, key="chat_k")
        
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

with tab7:
    st.header("📝 질문 생성하기")
    
    if st.session_state.db is None:
        st.warning("먼저 '문서 청킹 및 인덱싱' 탭에서 문서를 동기화해 주세요.")
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

with tab8:
    st.header("🔍 RAG 평가하기")
    
    if st.session_state.db is None:
        st.warning("먼저 '문서 청킹 및 인덱싱' 탭에서 문서를 동기화해 주세요.")
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
            k = st.slider("검색할 청크 개수 (k)", min_value=1, max_value=20, value=5)
        
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