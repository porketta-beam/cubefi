import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain.prompts import PromptTemplate
import json
import time

# 로깅 설정
logging.basicConfig(level=logging.WARNING)  # INFO에서 WARNING으로 변경
logger = logging.getLogger(__name__)

class RAGChatbot:
    def __init__(self, 
                 openai_api_key: str = None, 
                 anthropic_api_key: str = None,
                 llm_provider: str = "openai",  # "openai" 또는 "anthropic"
                 vectorstore_path: str = "vectorstore"):
        """
        RAG 챗봇 초기화
        
        Args:
            openai_api_key: OpenAI API 키
            anthropic_api_key: Anthropic API 키
            llm_provider: 사용할 LLM 제공자 ("openai" 또는 "anthropic")
            vectorstore_path: 벡터 스토어 저장 경로
        """
        load_dotenv()
        
        # API 키 설정
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.llm_provider = llm_provider.lower()
        
        # LLM 제공자별 API 키 검증
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OpenAI API 키가 필요합니다. .env 파일에 OPENAI_API_KEY를 설정하거나 파라미터로 전달하세요.")
        elif self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("Anthropic API 키가 필요합니다. .env 파일에 ANTHROPIC_API_KEY를 설정하거나 파라미터로 전달하세요.")
        
        # 벡터 스토어 경로 설정
        self.vectorstore_path = vectorstore_path
        os.makedirs(vectorstore_path, exist_ok=True)
        
        # 모델 초기화
        self._initialize_models()
        
        # 벡터 스토어 초기화
        self.vectorstore = None
        self.retriever = None
        self.qa_chain = None
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            output_key="answer",
            return_messages=True
        )
        
        # 문서 메타데이터 저장
        self.documents_metadata = {}
        self.metadata_file = os.path.join(vectorstore_path, "documents_metadata.json")
        self._load_metadata()
        
        # BM25용 문서 저장소
        self.bm25_documents = []
        self.bm25_retriever = None
        
        # 초기화 로그를 더 간결하게
        logger.debug(f"RAG 챗봇이 초기화되었습니다. (LLM: {self.llm_provider})")
    
    def _initialize_models(self):
        """모델 및 임베딩 모델 초기화"""
        try:
            if self.llm_provider == "openai":
                # OpenAI 모델 초기화
                self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
                self.llm = ChatOpenAI(
                    openai_api_key=self.openai_api_key,
                    model_name="gpt-4o-mini",
                    temperature=0.7
                )
                logger.debug("OpenAI 모델이 초기화되었습니다.")
                
            elif self.llm_provider == "anthropic":
                # Anthropic 모델 초기화
                self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)  # 임베딩은 OpenAI 사용
                self.llm = ChatAnthropic(
                    anthropic_api_key=self.anthropic_api_key,
                    model="claude-3-5sonnet-20241022",
                    temperature=0.7
                )
                logger.debug("Anthropic 모델이 초기화되었습니다.")
                
            else:
                raise ValueError("지원하지 않는 LLM 제공자입니다. 'openai' 또는 'anthropic'을 사용하세요.")
                
        except Exception as e:
            logger.error(f"모델 초기화 실패: {e}")
            raise
    
    def switch_llm_provider(self, provider: str):
        """LLM 제공자 변경"""
        old_provider = self.llm_provider
        self.llm_provider = provider.lower()
        
        if self.llm_provider not in ["openai", "anthropic"]:
            raise ValueError("지원하지 않는 LLM 제공자입니다. 'openai' 또는 'anthropic'을 사용하세요.")
        
        # API 키 검증
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OpenAI API 키가 필요합니다.")
        elif self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("Anthropic API 키가 필요합니다.")
        
        # 모델 재초기화
        self._initialize_models()
        
        # QA 체인 재생성
        if self.vectorstore:
            self._create_qa_chain()
        
        logger.debug(f"LLM 제공자가 {old_provider}에서 {self.llm_provider}로 변경되었습니다.")
    
    def _load_metadata(self):
        """문서 메타데이터 로드"""
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    self.documents_metadata = json.load(f)
        except Exception as e:
            logger.warning(f"메타데이터 로드 실패: {e}")
            self.documents_metadata = {}
    
    def _save_metadata(self):
        """문서 메타데이터 저장"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents_metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"메타데이터 저장 실패: {e}")
    
    def add_document(self, content: str, doc_id: str, metadata: Dict = None):
        """
        단일 문서 추가
        
        Args:
            content: 문서 내용
            doc_id: 문서 ID
            metadata: 추가 메타데이터
        """
        if metadata is None:
            metadata = {}
        
        # 메타데이터에 기본 정보 추가
        doc_metadata = {
            "doc_id": doc_id,
            "content_length": len(content),
            "added_at": str(datetime.now()),
            **metadata
        }
        
        # 기업명 추출 (파일명에서)
        company_name = self._extract_company_from_filename(doc_id)
        
        # 문서를 청크로 분할 (성능 최적화)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,      # 더 작은 청크로 정확도 향상
            chunk_overlap=100,    # 적절한 오버랩
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]  # 더 세밀한 분할
        )
        
        doc = Document(page_content=content, metadata=doc_metadata)
        chunks = text_splitter.split_documents([doc])
        
        # 각 청크에 기업명 추가
        if company_name:
            for chunk in chunks:
                chunk.page_content = f"[{company_name}] {chunk.page_content}"
        
        # 기존 벡터 스토어에 추가
        if self.vectorstore is None:
            self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
        else:
            self.vectorstore.add_documents(chunks)
        
        # BM25용 문서 추가
        for chunk in chunks:
            self.bm25_documents.append(chunk)
        
        # BM25 검색기 재생성
        if self.bm25_documents:
            try:
                self.bm25_retriever = BM25Retriever.from_documents(self.bm25_documents)
                self.bm25_retriever.k = 8
            except Exception as e:
                logger.warning(f"BM25 검색기 생성 실패: {e}")
        
        # 메타데이터 저장
        self.documents_metadata[doc_id] = doc_metadata
        self._save_metadata()
        
        # QA 체인 재생성
        self._create_qa_chain()
        
        logger.debug(f"문서 '{doc_id}'가 추가되었습니다. ({len(chunks)}개 청크)")
        return len(chunks)
    
    def _extract_company_from_filename(self, filename: str) -> str:
        """
        파일명에서 기업명 추출
        
        Args:
            filename: 파일명 (예: TSLA_2025-06-17)
            
        Returns:
            추출된 기업명 (예: Tesla)
        """
        # 기업 코드 매핑
        company_mapping = {
            "TSLA": "Tesla",
            "SKC": "SKC", 
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            "GOOGL": "Google",
            "AMZN": "Amazon",
            "NVDA": "NVIDIA",
            "META": "Meta",
            "NFLX": "Netflix",
            "SOXS": "SOXS"
        }
        
        # 파일명에서 기업 코드 추출 (첫 번째 부분)
        company_code = filename.split('_')[0].upper()
        
        # 매핑에서 찾기
        if company_code in company_mapping:
            return company_mapping[company_code]
        
        # 매핑에 없으면 원본 반환
        return company_code
    
    def add_documents_from_files(self, file_paths: List[str], doc_ids: List[str] = None):
        """
        파일에서 문서들을 추가 (PDF, TXT, MD 지원)
        
        Args:
            file_paths: 파일 경로 리스트
            doc_ids: 문서 ID 리스트 (None이면 파일명 사용)
        """
        if doc_ids is None:
            doc_ids = [os.path.basename(f) for f in file_paths]
        
        if len(file_paths) != len(doc_ids):
            raise ValueError("파일 경로와 문서 ID의 개수가 일치하지 않습니다.")
        
        # PDF 유틸리티 임포트
        try:
            from pdf_utils import extract_text_from_files
        except ImportError:
            logger.error("PDF 처리를 위한 pdf_utils.py가 필요합니다.")
            return
        
        # 파일에서 텍스트 추출
        file_results = extract_text_from_files(file_paths)
        
        total_chunks = 0
        success_count = 0
        
        for result, doc_id in zip(file_results, doc_ids):
            if result["success"]:
                try:
                    chunks = self.add_document(
                        result["content"], 
                        doc_id, 
                        {"source_file": result["file_path"]}
                    )
                    total_chunks += chunks
                    success_count += 1
                    logger.debug(f"파일 로드 성공: {result['file_path']} ({chunks}개 청크)")
                    
                except Exception as e:
                    logger.error(f"문서 추가 실패 {result['file_path']}: {e}")
            else:
                logger.error(f"파일 처리 실패 {result['file_path']}: {result['error']}")
        
        logger.debug(f"총 {len(file_paths)}개 파일 중 {success_count}개 성공, {total_chunks}개 청크가 추가되었습니다.")
    
    def add_documents(self, documents: List[Dict]):
        """
        문서 딕셔너리 리스트로 문서들 추가
        
        Args:
            documents: [{"content": "문서내용", "doc_id": "문서ID", "metadata": {...}}] 형태
        """
        total_chunks = 0
        for doc in documents:
            content = doc.get("content", "")
            doc_id = doc.get("doc_id", f"doc_{len(self.documents_metadata)}")
            metadata = doc.get("metadata", {})
            
            chunks = self.add_document(content, doc_id, metadata)
            total_chunks += chunks
        
        logger.info(f"총 {len(documents)}개 문서에서 {total_chunks}개 청크가 추가되었습니다.")
    
    def remove_document(self, doc_id: str):
        """
        문서 제거 (벡터 스토어 재생성 필요)
        
        Args:
            doc_id: 제거할 문서 ID
        """
        if doc_id in self.documents_metadata:
            del self.documents_metadata[doc_id]
            self._save_metadata()
            logger.info(f"문서 '{doc_id}'가 제거되었습니다.")
            return True
        else:
            logger.warning(f"문서 '{doc_id}'를 찾을 수 없습니다.")
            return False
    
    def get_document_info(self, doc_id: str = None):
        """
        문서 정보 조회
        
        Args:
            doc_id: 문서 ID (None이면 모든 문서)
        """
        if doc_id:
            return self.documents_metadata.get(doc_id)
        else:
            return self.documents_metadata
    
    def create_simple_retriever(self):
        """단순화된 하이브리드 검색기 생성 (벡터 + BM25)"""
        if not self.vectorstore:
            return None
        
        # 벡터 검색기 (단순화)
        vector_retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 8
            }
        )
        
        # BM25 검색기 (문서가 있으면)
        bm25_retriever = None
        if hasattr(self, 'bm25_retriever') and self.bm25_retriever:
            bm25_retriever = self.bm25_retriever
        
        # 앙상블 검색기 (벡터 + BM25) - 단순화
        if bm25_retriever:
            ensemble_retriever = EnsembleRetriever(
                retrievers=[vector_retriever, bm25_retriever],
                weights=[0.7, 0.3]  # 벡터 검색 70%, BM25 30%
            )
            return ensemble_retriever
        else:
            return vector_retriever

    def _create_qa_chain(self):
        """단순화된 QA 체인 생성"""
        if self.vectorstore:
            # 단순화된 검색기 사용
            self.retriever = self.create_simple_retriever()
            if not self.retriever:
                # 기본 검색기로 폴백
                self.retriever = self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={
                        "k": 5
                    }
                )
            # 프롬프트 템플릿
            qa_prompt_template = """
            다음 문맥을 사용하여 질문에 답변하세요. 
            답변할 수 없는 경우 "죄송합니다. 주어진 정보로는 답변할 수 없습니다."라고 말하세요.
            
            문맥: {context}
            
            질문: {question}
            
            답변:"""
            qa_prompt = PromptTemplate(
                template=qa_prompt_template,
                input_variables=["context", "question"]
            )
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.retriever,
                memory=self.memory,
                return_source_documents=True,
                output_key="answer",
                combine_docs_chain_kwargs={"prompt": qa_prompt},
                verbose=True
            )
    
    def load_vectorstore(self, path: str = None):
        """
        벡터 스토어 로드
        
        Args:
            path: 벡터 스토어 경로 (None이면 기본 경로)
        """
        load_path = path or self.vectorstore_path
        
        if os.path.exists(load_path):
            try:
                self.vectorstore = FAISS.load_local(load_path, self.embeddings, allow_dangerous_deserialization=True)
                self._load_metadata()
                self._create_qa_chain()
                logger.debug(f"벡터 스토어가 로드되었습니다: {load_path}")
                return True
            except Exception as e:
                logger.warning(f"벡터 스토어 로드 실패: {e}")
                return False
        else:
            logger.debug(f"벡터 스토어를 찾을 수 없습니다: {load_path}")
            return False
    
    def save_vectorstore(self, path: str = None):
        """
        벡터 스토어 저장
        
        Args:
            path: 저장 경로 (None이면 기본 경로)
        """
        if self.vectorstore:
            save_path = path or self.vectorstore_path
            self.vectorstore.save_local(save_path)
            self._save_metadata()
            logger.info(f"벡터 스토어가 저장되었습니다: {save_path}")
            return True
        else:
            logger.warning("저장할 벡터 스토어가 없습니다.")
            return False
    
    def ask(self, question: str, stock_code: str) -> Dict[str, Any]:
        """
        질문에 대한 답변 생성 (stock_code별 문서 필터링)
        Args:
            question: 사용자 질문
            stock_code: 검색할 기업 티커(문서 필터링용)
        Returns:
            답변과 관련 문서 정보
        """
        if not self.vectorstore:
            raise ValueError("먼저 문서를 로드해야 합니다.")
        
        # stock_code로 벡터스토어 필터링 retriever 생성
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={
                "k": 8,
                "filter": {"stock_code": stock_code.upper()}
            }
        )
        # BM25도 필터링 적용 (있으면)
        bm25_retriever = None
        if hasattr(self, 'bm25_retriever') and self.bm25_retriever:
            # stock_code가 일치하는 청크만 대상으로 BM25 인스턴스 생성
            filtered_bm25_docs = [doc for doc in self.bm25_documents if doc.metadata.get("stock_code", "").upper() == stock_code.upper()]
            if filtered_bm25_docs:
                bm25_retriever = BM25Retriever.from_documents(filtered_bm25_docs)
                bm25_retriever.k = 8
        # 앙상블 (벡터+BM25)
        if bm25_retriever:
            from langchain.retrievers import EnsembleRetriever
            final_retriever = EnsembleRetriever(
                retrievers=[retriever, bm25_retriever],
                weights=[0.7, 0.3]
            )
        else:
            final_retriever = retriever
        # QA 체인 생성 (stock_code별)
        qa_prompt_template = """
        다음 문맥을 사용하여 질문에 답변하세요. 
        답변할 수 없는 경우 "죄송합니다. 주어진 정보로는 답변할 수 없습니다."라고 말하세요.
        
        문맥: {context}
        
        질문: {question}
        
        답변:"""
        qa_prompt = PromptTemplate(
            template=qa_prompt_template,
            input_variables=["context", "question"]
        )
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=final_retriever,
            memory=self.memory,
            return_source_documents=True,
            output_key="answer",
            combine_docs_chain_kwargs={"prompt": qa_prompt},
            verbose=True
        )
        try:
            start_time = time.time()
            result = qa_chain.invoke({"question": question})
            elapsed = time.time() - start_time
            usage = result.get('usage', {})
            total_tokens = usage.get('total_tokens')
            if total_tokens is None:
                if hasattr(self.llm, 'last_response') and hasattr(self.llm.last_response, 'usage'):
                    total_tokens = getattr(self.llm.last_response.usage, 'total_tokens', None)
            source_docs = result.get("source_documents", [])
            if source_docs:
                sorted_docs = sorted(
                    source_docs, 
                    key=lambda x: x.metadata.get('score', 0), 
                    reverse=True
                )[:3]
                context = "\n\n".join([doc.page_content for doc in sorted_docs])
                improved_result_obj = self.llm.invoke(
                    f"다음 문맥을 바탕으로 질문에 답변하세요:\n\n문맥: {context}\n\n질문: {question}\n\n답변:"
                )
                improved_result = improved_result_obj.content if hasattr(improved_result_obj, 'content') else str(improved_result_obj)
                improved_usage = getattr(improved_result_obj, 'usage', None)
                improved_tokens = getattr(improved_usage, 'total_tokens', None) if improved_usage else None
                if improved_tokens:
                    total_tokens = improved_tokens
                sources = []
                for doc in sorted_docs:
                    sources.append({
                        "content": doc.page_content[:200] + "...",
                        "metadata": doc.metadata
                    })
                return {
                    "answer": improved_result,
                    "sources": sources,
                    "question": question,
                    "tokens_used": total_tokens,
                    "response_time": elapsed
                }
            sources = []
            for doc in source_docs:
                sources.append({
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                })
            return {
                "answer": result["answer"],
                "sources": sources,
                "question": question,
                "tokens_used": total_tokens,
                "response_time": elapsed
            }
        except Exception as e:
            logger.error(f"질문 처리 중 오류 발생: {e}")
            return {
                "answer": f"죄송합니다. 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "question": question,
                "tokens_used": None,
                "response_time": None
            }
    
    def clear_memory(self):
        """대화 기록 초기화"""
        self.memory.clear()
        logger.info("대화 기록이 초기화되었습니다.")
    
    def get_stats(self):
        """챗봇 통계 정보"""
        return {
            "total_documents": len(self.documents_metadata),
            "vectorstore_exists": self.vectorstore is not None,
            "qa_chain_exists": self.qa_chain is not None,
            "documents": list(self.documents_metadata.keys())
        } 