"""Hybrid search manager combining Elasticsearch BM25 and ChromaDB vector search"""

import streamlit as st
from typing import List, Dict, Any, Optional, Tuple
from langchain_openai.embeddings import OpenAIEmbeddings
from .chroma_db_manager import ChromaDBManager
from .elasticsearch_manager import ElasticsearchManager
from .search_parameter_optimizer import SearchParameterOptimizer


class HybridSearchManager:
    """Elasticsearch BM25 + ChromaDB vector ensemble search manager"""
    
    def __init__(self,
                 chroma_manager: ChromaDBManager,
                 elasticsearch_manager: Optional[ElasticsearchManager] = None,
                 embedding_model: str = "text-embedding-3-large"):
        self.chroma_manager = chroma_manager
        self.elasticsearch_manager = elasticsearch_manager
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self.parameter_optimizer = SearchParameterOptimizer()
        
    def check_search_availability(self) -> Dict[str, bool]:
        """Check which search methods are available"""
        availability = {
            'vector_search': False,
            'bm25_search': False,
            'hybrid_search': False
        }
        
        # ChromaDB vector search availability
        if self.chroma_manager.db is not None:
            availability['vector_search'] = True
        
        # Elasticsearch BM25 search availability
        if (self.elasticsearch_manager and 
            self.elasticsearch_manager.check_connection() and 
            self.elasticsearch_manager.check_index_exists()):
            availability['bm25_search'] = True
            
        # Hybrid search requires both
        availability['hybrid_search'] = availability['vector_search'] and availability['bm25_search']
        
        return availability
    
    def vector_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """ChromaDB vector similarity search"""
        try:
            if not self.chroma_manager.db:
                st.warning("ChromaDB not loaded")
                return []
            
            # ChromaDB similarity search
            results = self.chroma_manager.db.similarity_search_with_score(query, k=k)
            
            search_results = []
            for i, (doc, score) in enumerate(results):
                search_results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': float(score),  # ChromaDB distance score (lower = more similar)
                    'rank': i + 1,
                    'search_type': 'vector',
                    'source': doc.metadata.get('source', ''),
                    'filename': doc.metadata.get('source', '').split('/')[-1] if doc.metadata.get('source') else ''
                })
                
            return search_results
            
        except Exception as e:
            st.error(f"Vector search failed: {str(e)}")
            return []
    
    def bm25_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Elasticsearch BM25 keyword search"""
        try:
            if not self.elasticsearch_manager:
                st.warning("Elasticsearch manager not available")
                return []
            
            # Elasticsearch BM25 search
            results = self.elasticsearch_manager.search_documents(query, size=k)
            
            search_results = []
            for i, result in enumerate(results):
                search_results.append({
                    'content': result['content'],
                    'metadata': {
                        'source': result['source'],
                        'filename': result['filename'],
                        'doc_id': result['doc_id']
                    },
                    'score': result['score'],  # Elasticsearch relevance score (higher = more relevant)
                    'rank': i + 1,
                    'search_type': 'bm25',
                    'source': result['source'],
                    'filename': result['filename']
                })
                
            return search_results
            
        except Exception as e:
            st.error(f"BM25 search failed: {str(e)}")
            return []
    
    def normalize_scores(self, results: List[Dict[str, Any]], search_type: str) -> List[Dict[str, Any]]:
        """Normalize scores for RRF calculation"""
        if not results:
            return results
            
        if search_type == 'vector':
            # ChromaDB uses distance (lower = better), convert to similarity
            # Normalize to 0-1 range where 1 = most similar
            max_score = max(result['score'] for result in results)
            for result in results:
                # Convert distance to similarity and normalize
                result['normalized_score'] = 1.0 / (1.0 + result['score'])
        elif search_type == 'bm25':
            # Elasticsearch BM25 scores (higher = better)
            # Normalize to 0-1 range
            max_score = max(result['score'] for result in results) if results else 1.0
            for result in results:
                result['normalized_score'] = result['score'] / max_score if max_score > 0 else 0.0
                
        return results
    
    def reciprocal_rank_fusion(self, 
                              vector_results: List[Dict[str, Any]], 
                              bm25_results: List[Dict[str, Any]], 
                              k: int = 60,
                              bm25_weight: float = 0.5,
                              vector_weight: float = 0.5) -> List[Dict[str, Any]]:
        """Apply Reciprocal Rank Fusion (RRF) to combine results"""
        
        # RRF 스코어 계산을 위한 딕셔너리 (content를 key로 사용)
        rrf_scores = {}
        content_to_result = {}
        
        # Vector search results에 RRF 스코어 추가 (가중치 적용)
        for rank, result in enumerate(vector_results, 1):
            content = result['content']
            rrf_score = vector_weight * (1.0 / (k + rank))
            
            rrf_scores[content] = rrf_scores.get(content, 0) + rrf_score
            content_to_result[content] = result
            content_to_result[content]['vector_rank'] = rank
            content_to_result[content]['vector_score'] = result['score']
        
        # BM25 search results에 RRF 스코어 추가 (가중치 적용)
        for rank, result in enumerate(bm25_results, 1):
            content = result['content']
            rrf_score = bm25_weight * (1.0 / (k + rank))
            
            rrf_scores[content] = rrf_scores.get(content, 0) + rrf_score
            
            if content in content_to_result:
                # 이미 vector search에 있는 결과
                content_to_result[content]['bm25_rank'] = rank
                content_to_result[content]['bm25_score'] = result['score']
                content_to_result[content]['search_type'] = 'hybrid'
            else:
                # BM25에만 있는 결과
                content_to_result[content] = result
                content_to_result[content]['bm25_rank'] = rank
                content_to_result[content]['bm25_score'] = result['score']
                content_to_result[content]['vector_rank'] = None
                content_to_result[content]['vector_score'] = None
        
        # RRF 스코어로 정렬
        sorted_contents = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        # 최종 결과 생성
        hybrid_results = []
        for rank, content in enumerate(sorted_contents, 1):
            result = content_to_result[content].copy()
            result['rrf_score'] = rrf_scores[content]
            result['hybrid_rank'] = rank
            hybrid_results.append(result)
        
        return hybrid_results
    
    def hybrid_search(self, query: str, k: int = 5, rrf_k: int = 60, 
                      bm25_weight: Optional[float] = None, 
                      vector_weight: Optional[float] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Hybrid search combining BM25 and vector search with RRF
        
        Returns:
            Tuple of (results, search_info)
        """
        # 가중치 가져오기 (없으면 optimizer에서 가져옴)
        if bm25_weight is None or vector_weight is None:
            bm25_weight, vector_weight = self.parameter_optimizer.get_weights(query)
        
        search_info = {
            'query': query,
            'k': k,
            'rrf_k': rrf_k,
            'bm25_weight': bm25_weight,
            'vector_weight': vector_weight,
            'weight_mode': self.parameter_optimizer.current_weights['mode'],
            'vector_results_count': 0,
            'bm25_results_count': 0,
            'hybrid_results_count': 0,
            'search_methods_used': []
        }
        
        try:
            # Check availability
            availability = self.check_search_availability()
            
            if not availability['hybrid_search']:
                st.warning("Hybrid search not available. Using available search method.")
                if availability['vector_search']:
                    results = self.vector_search(query, k)
                    search_info['search_methods_used'] = ['vector']
                    search_info['hybrid_results_count'] = len(results)
                    return results, search_info
                elif availability['bm25_search']:
                    results = self.bm25_search(query, k)
                    search_info['search_methods_used'] = ['bm25']
                    search_info['hybrid_results_count'] = len(results)
                    return results, search_info
                else:
                    st.error("No search methods available")
                    return [], search_info
            
            # Perform both searches
            st.info("🔍 Performing hybrid search (BM25 + Vector)")
            
            # Vector search
            vector_results = self.vector_search(query, k=k*2)  # Get more results for better fusion
            search_info['vector_results_count'] = len(vector_results)
            
            # BM25 search  
            bm25_results = self.bm25_search(query, k=k*2)  # Get more results for better fusion
            search_info['bm25_results_count'] = len(bm25_results)
            
            # Apply RRF fusion
            if vector_results and bm25_results:
                hybrid_results = self.reciprocal_rank_fusion(
                    vector_results, bm25_results, rrf_k, 
                    bm25_weight, vector_weight
                )
                search_info['search_methods_used'] = ['vector', 'bm25', 'rrf']
                search_info['hybrid_results_count'] = len(hybrid_results[:k])
                
                st.success(f"✅ Hybrid search complete: {len(vector_results)} vector + {len(bm25_results)} BM25 → {len(hybrid_results[:k])} fused results")
                
                return hybrid_results[:k], search_info
            elif vector_results:
                search_info['search_methods_used'] = ['vector']
                search_info['hybrid_results_count'] = len(vector_results[:k])
                st.info("Using vector search only (BM25 results empty)")
                return vector_results[:k], search_info
            elif bm25_results:
                search_info['search_methods_used'] = ['bm25']
                search_info['hybrid_results_count'] = len(bm25_results[:k])
                st.info("Using BM25 search only (vector results empty)")
                return bm25_results[:k], search_info
            else:
                st.warning("No results from either search method")
                return [], search_info
                
        except Exception as e:
            st.error(f"Hybrid search failed: {str(e)}")
            return [], search_info
    
    def search(self, 
               query: str, 
               search_type: str = "hybrid", 
               k: int = 5, 
               rrf_k: int = 60) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Unified search interface
        
        Args:
            query: Search query
            search_type: 'vector', 'bm25', or 'hybrid'
            k: Number of results to return
            rrf_k: RRF constant (for hybrid search)
        """
        
        if search_type == "vector":
            results = self.vector_search(query, k)
            search_info = {
                'query': query,
                'search_type': 'vector',
                'k': k,
                'results_count': len(results)
            }
            return results, search_info
            
        elif search_type == "bm25":
            results = self.bm25_search(query, k)
            search_info = {
                'query': query,
                'search_type': 'bm25',
                'k': k,
                'results_count': len(results)
            }
            return results, search_info
            
        elif search_type == "hybrid":
            return self.hybrid_search(query, k, rrf_k)
            
        else:
            st.error(f"Unknown search type: {search_type}")
            return [], {'error': f'Unknown search type: {search_type}'}
    
    def get_search_status(self) -> Dict[str, Any]:
        """Get comprehensive search system status"""
        availability = self.check_search_availability()
        
        chroma_status = self.chroma_manager.get_status()
        es_status = self.elasticsearch_manager.get_status() if self.elasticsearch_manager else {
            'connection_ok': False,
            'index_exists': False,
            'document_count': 0,
            'message': 'Elasticsearch manager not initialized'
        }
        
        return {
            'availability': availability,
            'chromadb_status': chroma_status,
            'elasticsearch_status': es_status,
            'embedding_model': self.embeddings.model,
            'ready_for_search': any(availability.values())
        }