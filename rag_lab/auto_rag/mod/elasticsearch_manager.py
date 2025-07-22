"""Elasticsearch management module for hybrid search"""

import os
import json
import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime


class ElasticsearchManager:
    """Elasticsearch management class for hybrid search"""
    
    def __init__(self, 
                 host: str = "http://localhost:9200", 
                 index_name: str = "tax_documents",
                 username: str = "",
                 password: str = ""):
        self.host = host
        self.index_name = index_name
        self.username = username
        self.password = password
        self.client = None
        self.embedding_dims = 1536  # text-embedding-3-large 차원수
        
    def _get_client(self):
        """Get Elasticsearch client with lazy loading"""
        if self.client is None:
            try:
                # elasticsearch 라이브러리를 동적으로 import (설치 안되어 있을 수도)
                from elasticsearch import Elasticsearch
                
                if self.username and self.password:
                    self.client = Elasticsearch(
                        hosts=[self.host],
                        basic_auth=(self.username, self.password),
                        request_timeout=30,
                        max_retries=3,
                        retry_on_timeout=True
                    )
                else:
                    self.client = Elasticsearch(
                        hosts=[self.host],
                        request_timeout=30,
                        max_retries=3,
                        retry_on_timeout=True
                    )
                    
            except ImportError:
                st.error("elasticsearch 라이브러리가 설치되어 있지 않습니다. 'pip install elasticsearch>=8.0.0' 을 실행해주세요.")
                return None
            except Exception as e:
                st.error(f"Elasticsearch 클라이언트 생성 실패: {str(e)}")
                return None
                
        return self.client
    
    def check_connection(self) -> bool:
        """Check Elasticsearch connection"""
        try:
            client = self._get_client()
            if client is None:
                return False
                
            # 클러스터 상태 확인
            health = client.cluster.health()
            return health['status'] in ['green', 'yellow']
            
        except Exception as e:
            st.warning(f"Elasticsearch 연결 확인 실패: {str(e)}")
            return False
    
    def check_index_exists(self) -> bool:
        """Check if index exists"""
        try:
            client = self._get_client()
            if client is None:
                return False
                
            return client.indices.exists(index=self.index_name)
            
        except Exception as e:
            st.error(f"인덱스 존재 확인 실패: {str(e)}")
            return False
    
    def create_index(self, force_recreate: bool = False) -> bool:
        """Create Elasticsearch index with hybrid search mapping"""
        try:
            client = self._get_client()
            if client is None:
                return False
            
            # 인덱스가 이미 존재하고 재생성이 아닌 경우
            if self.check_index_exists():
                if not force_recreate:
                    st.info(f"인덱스 '{self.index_name}'이 이미 존재합니다.")
                    return True
                else:
                    # 기존 인덱스 삭제
                    client.indices.delete(index=self.index_name)
                    st.info(f"기존 인덱스 '{self.index_name}' 삭제 완료")
            
            # 인덱스 매핑 설정
            index_mapping = {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,  # 로컬 환경에서는 복제본 불필요
                    "analysis": {
                        "analyzer": {
                            "korean_analyzer": {
                                "type": "standard",  # nori 없을 때 fallback
                                "stopwords": "_korean_"
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "content": {
                            "type": "text",
                            "analyzer": "korean_analyzer",
                            "fields": {
                                "keyword": {
                                    "type": "keyword",
                                    "ignore_above": 256
                                }
                            }
                        },
                        "embedding": {
                            "type": "dense_vector",
                            "dims": self.embedding_dims,
                            "index": True,
                            "similarity": "cosine"
                        },
                        "source": {
                            "type": "keyword"
                        },
                        "filename": {
                            "type": "keyword"
                        },
                        "doc_id": {
                            "type": "keyword"
                        },
                        "chunk_id": {
                            "type": "keyword"
                        },
                        "created_at": {
                            "type": "date"
                        }
                    }
                }
            }
            
            # 인덱스 생성
            client.indices.create(index=self.index_name, body=index_mapping)
            st.success(f"인덱스 '{self.index_name}' 생성 완료")
            return True
            
        except Exception as e:
            st.error(f"인덱스 생성 실패: {str(e)}")
            return False
    
    def index_documents(self, documents: List[Any], embeddings: List[List[float]]) -> bool:
        """Index documents with embeddings to Elasticsearch"""
        try:
            st.info(f"🔄 Elasticsearch 인덱싱 시작: {len(documents)}개 문서, {len(embeddings)}개 임베딩")
            
            client = self._get_client()
            if client is None:
                st.error("❌ Elasticsearch 클라이언트 연결 실패")
                return False
            
            # 인덱스가 존재하지 않으면 생성
            if not self.check_index_exists():
                st.info(f"📝 인덱스 '{self.index_name}'가 존재하지 않음. 새로 생성합니다.")
                if not self.create_index():
                    st.error("❌ 인덱스 생성 실패")
                    return False
            
            # bulk 인덱싱을 위한 데이터 준비
            bulk_data = []
            current_time = datetime.now().isoformat()
            
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                # 문서 메타데이터에서 정보 추출
                source = doc.metadata.get('source', '')
                filename = os.path.basename(source) if source else f'doc_{i}'
                
                # 고유 ID 생성
                doc_id = f"{filename}_{i}_{hash(doc.page_content) % 10000}"
                
                # 인덱싱할 문서 데이터
                doc_data = {
                    "content": doc.page_content,
                    "embedding": embedding,
                    "source": source,
                    "filename": filename,
                    "doc_id": doc_id,
                    "chunk_id": f"chunk_{i}",
                    "created_at": current_time
                }
                
                # bulk API 형식으로 추가
                bulk_data.append({"index": {"_index": self.index_name, "_id": doc_id}})
                bulk_data.append(doc_data)
            
            # bulk 인덱싱 실행
            if bulk_data:
                st.info(f"📤 {len(bulk_data)//2}개 문서 Elasticsearch 인덱싱 중...")
                response = client.bulk(body=bulk_data, refresh=True)
                
                # 오류 확인
                if response.get("errors"):
                    error_count = sum(1 for item in response["items"] if "error" in item.get("index", {}))
                    st.error(f"❌ Elasticsearch 인덱싱 중 {error_count}개 오류 발생")
                    # 상세 오류 정보 표시
                    for item in response["items"]:
                        if "error" in item.get("index", {}):
                            error_detail = item["index"]["error"]
                            st.error(f"오류 상세: {error_detail}")
                    return False
                else:
                    indexed_count = len(documents)
                    st.success(f"✅ Elasticsearch에 {indexed_count}개 문서 인덱싱 완료")
                    return True
            else:
                st.warning("⚠️ 인덱싱할 데이터가 없습니다.")
                return True
            
        except Exception as e:
            st.error(f"Elasticsearch 문서 인덱싱 실패: {str(e)}")
            return False
    
    def get_document_count(self) -> int:
        """Get number of documents in index"""
        try:
            client = self._get_client()
            if client is None:
                return 0
            
            if not self.check_index_exists():
                return 0
                
            response = client.count(index=self.index_name)
            return response.get("count", 0)
            
        except Exception as e:
            st.error(f"Elasticsearch 문서 개수 조회 실패: {str(e)}")
            return 0
    
    def get_files_in_index(self) -> List[str]:
        """Get list of filenames in index"""
        try:
            client = self._get_client()
            if client is None:
                return []
            
            if not self.check_index_exists():
                return []
            
            # filename 필드의 unique 값들 조회
            query = {
                "size": 0,
                "aggs": {
                    "unique_filenames": {
                        "terms": {
                            "field": "filename",
                            "size": 1000
                        }
                    }
                }
            }
            
            response = client.search(index=self.index_name, body=query)
            
            filenames = []
            buckets = response.get("aggregations", {}).get("unique_filenames", {}).get("buckets", [])
            for bucket in buckets:
                filenames.append(bucket["key"])
                
            return filenames
            
        except Exception as e:
            st.error(f"Elasticsearch 파일 목록 조회 실패: {str(e)}")
            return []
    
    def delete_index(self) -> bool:
        """Delete entire index"""
        try:
            client = self._get_client()
            if client is None:
                return False
            
            if self.check_index_exists():
                client.indices.delete(index=self.index_name)
                st.success(f"인덱스 '{self.index_name}' 삭제 완료")
            else:
                st.info("삭제할 인덱스가 존재하지 않습니다.")
                
            return True
            
        except Exception as e:
            st.error(f"인덱스 삭제 실패: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get Elasticsearch status information"""
        connection_ok = self.check_connection()
        index_exists = self.check_index_exists() if connection_ok else False
        document_count = self.get_document_count() if index_exists else 0
        
        return {
            'connection_ok': connection_ok,
            'index_exists': index_exists,
            'document_count': document_count,
            'index_name': self.index_name,
            'host': self.host,
            'embedding_dims': self.embedding_dims
        }
    
    def search_documents(self, query: str, size: int = 5) -> List[Dict]:
        """Simple BM25 text search (벡터 검색은 별도 구현)"""
        try:
            client = self._get_client()
            if client is None:
                return []
            
            if not self.check_index_exists():
                return []
            
            search_query = {
                "query": {
                    "match": {
                        "content": query
                    }
                },
                "size": size,
                "_source": ["content", "filename", "source", "doc_id"]
            }
            
            response = client.search(index=self.index_name, body=search_query)
            
            results = []
            for hit in response["hits"]["hits"]:
                results.append({
                    "content": hit["_source"]["content"],
                    "filename": hit["_source"]["filename"],
                    "source": hit["_source"]["source"],
                    "doc_id": hit["_source"]["doc_id"],
                    "score": hit["_score"]
                })
                
            return results
            
        except Exception as e:
            st.error(f"Elasticsearch 검색 실패: {str(e)}")
            return []