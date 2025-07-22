"""Search Parameter Optimizer Module for Hybrid Search"""

import streamlit as st
from typing import Dict, Tuple, Optional, Any
import json
import os
from datetime import datetime
import numpy as np


class SearchParameterOptimizer:
    """검색 파라미터 최적화 관리 클래스"""
    
    def __init__(self, config_path: str = "./.streamlit/search_weights.json"):
        self.config_path = config_path
        self.config_dir = os.path.dirname(config_path)
        
        # Ensure config directory exists
        if not os.path.exists(self.config_dir):
            try:
                os.makedirs(self.config_dir)
            except Exception as e:
                st.warning(f"설정 디렉토리 생성 실패, 임시 경로 사용: {str(e)}")
                self.config_path = "./search_weights.json"
                self.config_dir = "."
        
        # 기본 가중치 설정
        self.default_weights = {
            "bm25_weight": 0.5,
            "vector_weight": 0.5,
            "mode": "manual",  # "auto" or "manual"
            "last_updated": None
        }
        
        # 쿼리 유형별 최적 가중치 (자동 모드용)
        self.query_type_weights = {
            "keyword_heavy": {"bm25_weight": 0.7, "vector_weight": 0.3},
            "semantic_heavy": {"bm25_weight": 0.3, "vector_weight": 0.7},
            "balanced": {"bm25_weight": 0.5, "vector_weight": 0.5},
            "short_query": {"bm25_weight": 0.6, "vector_weight": 0.4},
            "long_query": {"bm25_weight": 0.4, "vector_weight": 0.6}
        }
        
        # 현재 가중치 로드
        self.current_weights = self.load_weights()
    
    @property
    def mode(self) -> str:
        """현재 최적화 모드 반환"""
        return self.current_weights.get("mode", "manual")
    
    @property
    def bm25_weight(self) -> float:
        """현재 BM25 가중치 반환"""
        return self.current_weights.get("bm25_weight", 0.5)
    
    @property  
    def vector_weight(self) -> float:
        """현재 벡터 가중치 반환"""
        return self.current_weights.get("vector_weight", 0.5)
    
    def analyze_query_type(self, query: str) -> str:
        """쿼리 유형 분석"""
        # 쿼리 길이 분석
        word_count = len(query.split())
        
        # 특수 키워드 패턴 분석
        keyword_patterns = ["세율", "법률", "조항", "제", "항", "호", "규정", "기한", "신고"]
        semantic_patterns = ["어떻게", "무엇", "왜", "설명", "의미", "차이", "비교", "장단점"]
        
        keyword_score = sum(1 for pattern in keyword_patterns if pattern in query)
        semantic_score = sum(1 for pattern in semantic_patterns if pattern in query)
        
        # 쿼리 유형 결정
        if word_count <= 3:
            return "short_query"
        elif word_count >= 10:
            return "long_query"
        elif keyword_score > semantic_score:
            return "keyword_heavy"
        elif semantic_score > keyword_score:
            return "semantic_heavy"
        else:
            return "balanced"
    
    def get_auto_weights(self, query: str) -> Dict[str, float]:
        """자동 모드에서 쿼리에 최적화된 가중치 반환"""
        query_type = self.analyze_query_type(query)
        weights = self.query_type_weights.get(query_type, self.query_type_weights["balanced"])
        
        # 쿼리 유형 정보 저장 (디버깅/모니터링용)
        st.session_state.last_query_type = query_type
        
        return weights
    
    def get_weights(self, query: Optional[str] = None) -> Tuple[float, float]:
        """현재 설정된 가중치 반환 (자동/수동 모드 고려)"""
        if self.current_weights["mode"] == "auto" and query:
            weights = self.get_auto_weights(query)
            return weights["bm25_weight"], weights["vector_weight"]
        else:
            return self.current_weights["bm25_weight"], self.current_weights["vector_weight"]
    
    def set_weights(self, bm25_weight: float, vector_weight: float, mode: str = "manual") -> bool:
        """가중치 설정 및 저장"""
        try:
            # 가중치 정규화 (합이 1이 되도록)
            total = bm25_weight + vector_weight
            if total > 0:
                bm25_weight = bm25_weight / total
                vector_weight = vector_weight / total
            else:
                bm25_weight = 0.5
                vector_weight = 0.5
            
            self.current_weights = {
                "bm25_weight": round(bm25_weight, 3),
                "vector_weight": round(vector_weight, 3),
                "mode": mode,
                "last_updated": datetime.now().isoformat()
            }
            
            return self.save_weights()
        except Exception as e:
            st.error(f"가중치 설정 실패: {str(e)}")
            return False
    
    def save_weights(self) -> bool:
        """가중치 설정을 파일에 저장"""
        try:
            # 디렉토리 생성
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
            
            # JSON 파일로 저장
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_weights, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            st.error(f"가중치 저장 실패: {str(e)}")
            return False
    
    def load_weights(self) -> Dict[str, Any]:
        """저장된 가중치 불러오기"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    weights = json.load(f)
                    # 버전 호환성을 위한 기본값 처리
                    return {**self.default_weights, **weights}
            else:
                return self.default_weights.copy()
        except Exception as e:
            st.warning(f"가중치 불러오기 실패, 기본값 사용: {str(e)}")
            return self.default_weights.copy()
    
    def reset_to_default(self) -> bool:
        """기본 가중치로 초기화"""
        self.current_weights = self.default_weights.copy()
        self.current_weights["last_updated"] = datetime.now().isoformat()
        return self.save_weights()
    
    def get_weight_presets(self) -> Dict[str, Dict[str, float]]:
        """미리 정의된 가중치 프리셋 반환"""
        return {
            "균형": {"bm25_weight": 0.5, "vector_weight": 0.5},
            "키워드 중심": {"bm25_weight": 0.7, "vector_weight": 0.3},
            "의미 중심": {"bm25_weight": 0.3, "vector_weight": 0.7},
            "BM25 전용": {"bm25_weight": 1.0, "vector_weight": 0.0},
            "벡터 전용": {"bm25_weight": 0.0, "vector_weight": 1.0}
        }
    
    def apply_preset(self, preset_name: str) -> bool:
        """프리셋 가중치 적용"""
        presets = self.get_weight_presets()
        if preset_name in presets:
            preset = presets[preset_name]
            return self.set_weights(
                preset["bm25_weight"], 
                preset["vector_weight"], 
                mode="manual"
            )
        return False
    
    def get_optimization_metrics(self) -> Dict[str, Any]:
        """최적화 관련 메트릭 반환 (향후 ML 모델 학습용)"""
        return {
            "current_weights": self.current_weights,
            "mode": self.current_weights["mode"],
            "last_updated": self.current_weights.get("last_updated"),
            "query_type_distribution": {},  # 향후 쿼리 유형 통계
            "performance_metrics": {}  # 향후 성능 메트릭
        }