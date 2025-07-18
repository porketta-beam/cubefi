import streamlit as st
import os
import tempfile
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
    context_recall,
    answer_correctness
)
from ragas.evaluation import evaluate

# Load environment variables
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env', override=True)

# Matplotlib 한글 및 음수 깨짐 방지 설정
plt.rcParams['axes.unicode_minus'] = False

# Set page config
st.set_page_config(
    page_title="RAG System with RAGAS Evaluation",
    page_icon="🤖",
    layout="wide"
)

# VectorDB 관리 함수들
def get_vectordb_path():
    """VectorDB 저장 경로 반환"""
    return "./chroma_db"

def check_vectordb_exists():
    """로컬 VectorDB 존재 여부 확인"""
    db_path = get_vectordb_path()
    return os.path.exists(db_path) and os.path.isdir(db_path) and len(os.listdir(db_path)) > 0

def load_existing_vectordb(embedding_model="text-embedding-3-large"):
    """기존 VectorDB 로드"""
    try:
        embeddings = OpenAIEmbeddings(model=embedding_model)
        db = Chroma(
            persist_directory=get_vectordb_path(),
            embedding_function=embeddings,
            collection_name="rag_db"
        )
        return db
    except Exception as e:
        st.error(f"VectorDB 로드 중 오류 발생: {str(e)}")
        return None

def create_new_vectordb(documents, embedding_model="text-embedding-3-large"):
    """새로운 VectorDB 생성 및 로컬 저장"""
    try:
        embeddings = OpenAIEmbeddings(model=embedding_model)
        
        # 기존 디렉토리가 있다면 삭제
        db_path = get_vectordb_path()
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
        
        # 새로운 VectorDB 생성
        db = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            collection_name="rag_db",
            persist_directory=db_path
        )
        
        return db
    except Exception as e:
        st.error(f"VectorDB 생성 중 오류 발생: {str(e)}")
        return None

def add_documents_to_vectordb(new_documents, embedding_model="text-embedding-3-large"):
    """기존 VectorDB에 새로운 문서 추가"""
    try:
        # 기존 VectorDB 로드
        db = load_existing_vectordb(embedding_model)
        if not db:
            st.error("기존 VectorDB를 로드할 수 없습니다.")
            return None
        
        # 새로운 문서들을 기존 컬렉션에 추가
        db.add_documents(new_documents)
        
        return db
    except Exception as e:
        st.error(f"문서 추가 중 오류 발생: {str(e)}")
        return None

def get_vectordb_documents(limit=None):
    """VectorDB에 저장된 문서들 조회"""
    try:
        db = load_existing_vectordb()
        if not db:
            return []
        
        # ChromaDB에서 모든 문서 조회
        collection = db._collection
        
        # 모든 문서의 ID와 메타데이터, 내용 조회
        if limit:
            results = collection.get(limit=limit, include=['documents', 'metadatas'])
        else:
            results = collection.get(include=['documents', 'metadatas'])
        
        documents_info = []
        for i, (doc_id, document, metadata) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
            doc_info = {
                'id': doc_id,
                'content': document,
                'metadata': metadata or {},
                'content_preview': document[:200] + "..." if len(document) > 200 else document,
                'char_count': len(document)
            }
            documents_info.append(doc_info)
        
        return documents_info
    except Exception as e:
        st.error(f"문서 조회 중 오류 발생: {str(e)}")
        return []

def close_vectordb_connection():
    """VectorDB 연결 안전하게 종료"""
    import gc
    import time
    
    try:
        # session state의 db 연결 해제
        if 'db' in st.session_state and st.session_state.db is not None:
            db = st.session_state.db
            
            # 여러 방법으로 ChromaDB 연결 종료 시도
            try:
                # 방법 1: 클라이언트 리셋
                if hasattr(db, '_client') and db._client:
                    db._client.reset()
                    
                # 방법 2: 컬렉션 참조 제거
                if hasattr(db, '_collection'):
                    db._collection = None
                    
                # 방법 3: 클라이언트 참조 제거
                if hasattr(db, '_client'):
                    db._client = None
                    
            except Exception as e:
                print(f"DB 연결 종료 중 오류 (무시됨): {e}")
            
            # session state 초기화
            st.session_state.db = None
            del db  # 명시적 삭제
        
        # 강제 가비지 컬렉션 여러 번 실행
        for _ in range(3):
            gc.collect()
            time.sleep(0.3)
        
        # 더 긴 대기 시간
        time.sleep(3.0)
        
        # 추가: 모든 전역 ChromaDB 클라이언트 정리 시도
        try:
            import chromadb
            # ChromaDB의 전역 클라이언트들 정리
            if hasattr(chromadb, '_client_cache'):
                chromadb._client_cache.clear()
        except:
            pass
        
        return True
    except Exception as e:
        print(f"연결 종료 중 오류: {str(e)}")
        return False

def safe_delete_vectordb_with_retry(db_path, max_retries=3):
    """재시도 메커니즘을 포함한 안전한 VectorDB 삭제"""
    import time
    import gc
    
    for attempt in range(max_retries):
        try:
            # 삭제 시도 전 추가 정리
            gc.collect()
            time.sleep(1.0)
            
            if os.path.exists(db_path):
                shutil.rmtree(db_path)
            return True
            
        except PermissionError as e:
            if attempt < max_retries - 1:
                st.warning(f"삭제 시도 {attempt + 1}/{max_retries} 실패. {2 * (attempt + 1)}초 후 재시도...")
                time.sleep(2 * (attempt + 1))  # 점진적으로 더 오래 대기
            else:
                # 마지막 시도도 실패한 경우 이름 변경으로 대체
                try:
                    backup_path = f"{db_path}_deleted_{int(time.time())}"
                    os.rename(db_path, backup_path)
                    st.warning(f"직접 삭제 실패. 폴더를 {backup_path}로 이름 변경했습니다. 수동으로 삭제해주세요.")
                    return True
                except Exception as rename_error:
                    raise e  # 원래 오류 다시 발생
        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"예상치 못한 오류 발생. 재시도 중... ({str(e)})")
                time.sleep(2)
            else:
                raise e
    
    return False

def get_vectordb_info():
    """VectorDB 정보 조회"""
    if check_vectordb_exists():
        try:
            db = load_existing_vectordb()
            if db:
                collection = db._collection
                return {
                    "exists": True,
                    "count": collection.count(),
                    "path": get_vectordb_path()
                }
        except:
            pass
    
    return {
        "exists": False,
        "count": 0,
        "path": get_vectordb_path()
    }

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

st.title("🤖 RAG 시스템 및 RAGAS 평가")
st.markdown("---")

# 탭 이름
tab1, tab2, tab3, tab4 = st.tabs(["📚 문서 임베딩", "💬 RAG 테스트", "📝 질문 생성하기", "🔍 RAG 평가하기"])

with tab1:
    st.header("문서 임베딩 설정")
    st.write("윈도우 보안 이슈 발생 크로마에서 supabase로 변경 필요")
    st.write("일단 노트북 파일로 db 추가할 것")
    
    # VectorDB 상태 확인
    db_info = get_vectordb_info()
    
    st.subheader("📁 VectorDB 상태")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if db_info["exists"]:
            st.success("✅ VectorDB 존재")
            st.metric("저장된 문서 수", db_info["count"])
        else:
            st.warning("❌ VectorDB 없음")
            st.metric("저장된 문서 수", 0)
    
    with col2:
        st.info(f"📂 저장 경로: {db_info['path']}")
    
    with col3:
        if db_info["exists"]:
            if st.button("🗑️ VectorDB 삭제", type="secondary"):
                try:
                    with st.spinner("VectorDB 연결을 종료하고 삭제하는 중입니다..."):
                        # 1. ChromaDB 연결 안전하게 종료
                        st.info("1단계: ChromaDB 연결 종료 중...")
                        close_vectordb_connection()
                        
                        # 2. 문서 관련 session state 초기화
                        st.info("2단계: 세션 데이터 초기화 중...")
                        st.session_state.documents = None
                        st.session_state.generated_questions = []
                        st.session_state.edited_questions = []
                        st.session_state.evaluation_results = None
                        
                        # 3. 재시도 메커니즘으로 디렉토리 삭제
                        st.info("3단계: VectorDB 파일 삭제 중...")
                        success = safe_delete_vectordb_with_retry(db_info['path'])
                        
                        if success:
                            st.success("✅ VectorDB가 성공적으로 삭제되었습니다!")
                        else:
                            st.error("❌ VectorDB 삭제에 실패했습니다.")
                            
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"VectorDB 삭제 중 오류 발생: {str(e)}")
                    st.info("💡 해결 방법:")
                    st.info("1. 페이지를 새로고침한 후 다시 시도")
                    st.info("2. Streamlit 서버 재시작 후 시도")
                    st.info("3. 수동으로 ./chroma_db 폴더 삭제")
    
    # 기존 VectorDB 관리 버튼들
    if db_info["exists"]:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.db is None:
                if st.button("📥 기존 VectorDB 로드", type="primary"):
                    try:
                        with st.spinner("기존 VectorDB를 로드 중입니다..."):
                            # 임베딩 모델 설정 (기본값 사용)
                            embedding_model = "text-embedding-3-large"
                            db = load_existing_vectordb(embedding_model)
                            
                            if db:
                                st.session_state.db = db
                                st.success(f"기존 VectorDB를 성공적으로 로드했습니다! (문서 수: {db_info['count']})")
                                st.rerun()
                            
                    except Exception as e:
                        st.error(f"VectorDB 로드 중 오류 발생: {str(e)}")
        
        with col2:
            if st.button("📋 저장된 문서 목록 보기"):
                with st.spinner("문서 목록을 불러오는 중입니다..."):
                    documents = get_vectordb_documents(limit=100)  # 최대 100개까지 표시
                    
                    if documents:
                        st.subheader("📚 저장된 문서 목록")
                        st.write(f"총 {len(documents)}개의 문서 청크가 저장되어 있습니다.")
                        
                        # 문서 목록을 데이터프레임으로 표시
                        df_data = []
                        for i, doc in enumerate(documents):
                            source = doc['metadata'].get('source', 'Unknown')
                            page = doc['metadata'].get('page', 'N/A')
                            
                            df_data.append({
                                'No.': i + 1,
                                'Source': source.split('/')[-1] if source != 'Unknown' else source,  # 파일명만 표시
                                'Page': page,
                                'Length': doc['char_count'],
                                'Preview': doc['content_preview']
                            })
                        
                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True)
                        
                        # 상세 내용 보기
                        st.subheader("📄 문서 상세 내용")
                        selected_doc_idx = st.selectbox(
                            "문서 선택 (상세 내용 보기)",
                            range(len(documents)),
                            format_func=lambda x: f"문서 {x+1}: {documents[x]['metadata'].get('source', 'Unknown').split('/')[-1]} (페이지 {documents[x]['metadata'].get('page', 'N/A')})"
                        )
                        
                        if selected_doc_idx is not None:
                            selected_doc = documents[selected_doc_idx]
                            
                            # 메타데이터 표시
                            st.write("**메타데이터:**")
                            metadata_cols = st.columns(3)
                            with metadata_cols[0]:
                                st.write(f"**Source:** {selected_doc['metadata'].get('source', 'Unknown')}")
                            with metadata_cols[1]:
                                st.write(f"**Page:** {selected_doc['metadata'].get('page', 'N/A')}")
                            with metadata_cols[2]:
                                st.write(f"**Length:** {selected_doc['char_count']} 자")
                            
                            # 문서 내용 표시
                            st.write("**전체 내용:**")
                            st.text_area(
                                "문서 내용",
                                value=selected_doc['content'],
                                height=300,
                                key=f"doc_content_{selected_doc_idx}",
                                disabled=True
                            )
                    else:
                        st.warning("저장된 문서를 찾을 수 없습니다.")
    
    st.markdown("---")
    
    # File upload
    st.subheader("📄 새로운 문서 업로드")
    uploaded_file = st.file_uploader("텍스트 또는 PDF 파일 업로드", type=['txt', 'pdf'])
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        file_extension = uploaded_file.name.split('.')[-1].lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{file_extension}') as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name
        
        # Text splitter parameters
        st.subheader("텍스트 분할기 설정")
        col1, col2 = st.columns(2)
        
        with col1:
            chunk_size = st.slider("청크 크기", min_value=100, max_value=2000, value=500, step=50)
        
        with col2:
            chunk_overlap = st.slider("청크 중첩", min_value=0, max_value=500, value=100, step=25)
        
        
        # Embedding model selection
        st.subheader("임베딩 설정")
        embedding_model = st.selectbox(
            "Embedding Model",
            ["text-embedding-3-large", "text-embedding-3-small", "text-embedding-ada-002"],
            index=0
        )
        
        # VectorDB 저장 옵션
        st.subheader("VectorDB 설정")
        
        # 기존 DB가 있는 경우 옵션 제공
        if db_info["exists"]:
            operation_mode = st.radio(
                "문서 처리 방식",
                options=["새로운 VectorDB 생성 (기존 DB 덮어쓰기)", "기존 VectorDB에 문서 추가"],
                index=1,
                help="기존 VectorDB가 있습니다. 어떤 방식으로 처리할지 선택하세요."
            )
            save_to_local = True  # 기존 DB가 있으면 항상 로컬 저장
        else:
            save_to_local = st.checkbox("💾 로컬에 VectorDB 저장", value=True, help="체크하면 VectorDB를 로컬에 저장하여 재사용할 수 있습니다.")
            operation_mode = "새로운 VectorDB 생성"
        
        # Process documents button
        if st.button("문서 처리", type="primary"):
            try:
                with st.spinner("문서를 처리 중입니다..."):
                    # Load and split documents
                    if file_extension == 'txt':
                        loader = TextLoader(tmp_file_path)
                    elif file_extension == 'pdf':
                        loader = PyPDFLoader(tmp_file_path)
                    else:
                        raise ValueError(f"지원하지 않는 파일 형식: {file_extension}")
                    
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
                    documents = loader.load_and_split(text_splitter)
                    
                    # Create or update vector database
                    if operation_mode == "기존 VectorDB에 문서 추가":
                        # 기존 VectorDB에 문서 추가
                        old_count = db_info["count"]
                        db = add_documents_to_vectordb(documents, embedding_model)
                        action_text = f"기존 VectorDB에 {len(documents)}개의 문서 청크가 추가되었습니다! (총 {old_count + len(documents)}개)"
                    elif save_to_local:
                        # 로컬에 저장하는 새로운 VectorDB 생성
                        db = create_new_vectordb(documents, embedding_model)
                        action_text = f"{len(documents)}개의 문서 청크가 성공적으로 처리되고 로컬에 저장되었습니다!"
                    else:
                        # 메모리에만 저장하는 VectorDB 생성 (기존 방식)
                        embeddings = OpenAIEmbeddings(model=embedding_model)
                        db = Chroma.from_documents(
                            documents=documents,
                            embedding=embeddings,
                            collection_name="rag_db"
                        )
                        action_text = f"{len(documents)}개의 문서 청크가 성공적으로 처리되었습니다!"
                    
                    if db:
                        # Store in session state
                        st.session_state.db = db
                        if operation_mode != "기존 VectorDB에 문서 추가":
                            st.session_state.documents = documents
                        
                        st.success(action_text)
                        
                        # Display document info
                        st.subheader("처리된 문서 정보")
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if operation_mode == "기존 VectorDB에 문서 추가":
                                st.metric("추가된 청크 수", len(documents))
                                updated_db_info = get_vectordb_info()
                                st.metric("전체 청크 수", updated_db_info["count"])
                            else:
                                st.metric("총 청크 수", len(documents))
                        
                        with col2:
                            avg_chunk_size = np.mean([len(doc.page_content) for doc in documents])
                            st.metric("평균 청크 크기", f"{avg_chunk_size:.0f}자")
                        
                        with col3:
                            total_chars = sum(len(doc.page_content) for doc in documents)
                            st.metric("처리된 문자 수", f"{total_chars:,}")
                        
                        # Show sample chunks
                        st.subheader("샘플 문서 청크")
                        for i, doc in enumerate(documents[:3]):
                            with st.expander(f"청크 {i+1}"):
                                st.text(doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content)
                    else:
                        st.error("VectorDB 생성에 실패했습니다.")
                                
            except Exception as e:
                st.error(f"문서 처리 중 오류 발생: {str(e)}")
        
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)

with tab2:
    st.header("RAG 테스트")
    
    if st.session_state.db is None:
        st.warning("먼저 '문서 임베딩' 탭에서 문서를 업로드하고 처리해 주세요.")
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
        st.warning("먼저 '문서 임베딩' 탭에서 문서를 업로드하고 처리해 주세요.")
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
                    # Create LLM instance
                    llm_for_question = ChatOpenAI(model_name=question_model, temperature=question_temperature)
                    
                    # Generate questions
                    questions = []
                    documents = st.session_state.documents
                    
                    for i in range(num_questions):
                        prompt_text = f"""
다음 문서를 바탕으로 질문을 1개 생성해 주세요.
반드시 질문문장만 출력해 주세요. '질문:'이라는 표현 없이 완전한 한국어 질문 형태로만 작성해 주세요.

문서 내용:
{documents[i % len(documents)].page_content}
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
        st.warning("먼저 '문서 임베딩' 탭에서 문서를 업로드하고 처리해 주세요.")
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
1. **문서 임베딩 탭**: 텍스트 파일을 업로드하고 텍스트 분할 파라미터를 설정하세요.
2. **RAG 테스트 탭**: RAG 시스템과 실시간으로 채팅하며 답변을 확인하세요.
3. **질문 생성하기 탭**: 문서를 바탕으로 질문을 자동 생성하고 편집하세요.
4. **RAG 평가하기 탭**: 생성된 질문을 RAG 시스템으로 평가하세요.

### RAGAS 평가 지표:
- **정확성(Faithfulness)**: 답변이 사실에 얼마나 부합하는지
- **답변 관련성(Answer Relevancy)**: 답변이 질문과 얼마나 관련 있는지
- **문맥 정밀도(Context Precision)**: 검색된 문맥이 얼마나 정밀한지
- **문맥 재현율(Context Recall)**: 검색된 문맥이 얼마나 완전한지

### 요구 사항:
- .env 파일에 OpenAI API 키 필요
- 필수 Python 패키지: streamlit, langchain, ragas 등
""")