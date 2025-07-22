"""Weight Optimization Experiment Module for Hybrid Search"""

import json
import os
import time
import numpy as np
import streamlit as st
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import pandas as pd


class WeightOptimizationExperiment:
    """하이브리드 검색 가중치 최적화 실험 클래스"""
    
    def __init__(self, log_path: str = "./weight_search.log"):
        self.log_path = log_path
        self.log_dir = os.path.dirname(log_path) or "."
        
        # 로그 디렉토리 생성
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
    
    def generate_weight_combinations(
        self, 
        min_weight: float = 0.0, 
        max_weight: float = 1.0, 
        step: float = 0.1
    ) -> List[Tuple[float, float]]:
        """가중치 조합 생성 (Grid Search)"""
        combinations = []
        
        # BM25와 Vector 가중치의 모든 조합 생성
        weights = np.arange(min_weight, max_weight + step, step)
        
        for bm25_weight in weights:
            for vector_weight in weights:
                # 가중치 합이 1에 가깝거나 둘 다 0이 아닌 경우만 포함
                total = bm25_weight + vector_weight
                if total > 0:
                    # 정규화
                    norm_bm25 = bm25_weight / total
                    norm_vector = vector_weight / total
                    combinations.append((
                        round(norm_bm25, 3), 
                        round(norm_vector, 3)
                    ))
        
        # 중복 제거
        return list(set(combinations))
    
    def evaluate_search_quality(
        self, 
        hybrid_search_manager, 
        test_queries: List[str],
        bm25_weight: float, 
        vector_weight: float
    ) -> Dict[str, Any]:
        """특정 가중치 조합의 검색 품질 평가"""
        
        total_score = 0.0
        query_scores = []
        total_latency = 0.0
        error_count = 0
        
        for query in test_queries:
            try:
                start_time = time.time()
                
                # 하이브리드 검색 실행
                results, info = hybrid_search_manager.search(
                    query=query,
                    search_type="hybrid",
                    k=5,  # 상위 5개 결과
                    weight_ratio=int(bm25_weight * 100)  # 백분율로 변환
                )
                
                latency = (time.time() - start_time) * 1000  # ms
                total_latency += latency
                
                # 품질 점수 계산 (예시: 결과 수, 평균 점수, 다양성 등)
                if results:
                    # 기본 점수: 결과 개수와 점수의 조화평균
                    result_count_score = min(len(results) / 5.0, 1.0)  # 최대 1.0
                    
                    # 평균 점수 (정규화)
                    if hasattr(results[0], 'score') or (isinstance(results[0], dict) and 'score' in results[0]):
                        scores = [r.score if hasattr(r, 'score') else r['score'] for r in results]
                        avg_score = np.mean(scores) if scores else 0.0
                        avg_score_normalized = min(avg_score / 10.0, 1.0)  # 10으로 정규화
                    else:
                        avg_score_normalized = 0.5  # 기본값
                    
                    # 결과 다양성 (파일명 기준)
                    if len(results) > 1:
                        filenames = set()
                        for r in results:
                            if hasattr(r, 'filename'):
                                filenames.add(r.filename)
                            elif isinstance(r, dict) and 'filename' in r:
                                filenames.add(r['filename'])
                        diversity_score = len(filenames) / len(results)
                    else:
                        diversity_score = 1.0 if results else 0.0
                    
                    # 종합 점수 (가중 평균)
                    query_score = (
                        result_count_score * 0.4 + 
                        avg_score_normalized * 0.4 + 
                        diversity_score * 0.2
                    )
                else:
                    query_score = 0.0
                
                query_scores.append(query_score)
                total_score += query_score
                
            except Exception as e:
                error_count += 1
                st.warning(f"쿼리 '{query}' 평가 중 오류: {str(e)}")
                query_scores.append(0.0)
        
        # 전체 평가 지표 계산
        num_queries = len(test_queries)
        avg_score = total_score / num_queries if num_queries > 0 else 0.0
        avg_latency = total_latency / num_queries if num_queries > 0 else 0.0
        error_rate = error_count / num_queries if num_queries > 0 else 0.0
        
        # 표준편차 계산 (일관성 지표)
        score_std = np.std(query_scores) if query_scores else 0.0
        
        return {
            "avg_score": round(avg_score, 4),
            "avg_latency_ms": round(avg_latency, 2),
            "error_rate": round(error_rate, 4),
            "score_std": round(score_std, 4),
            "query_scores": query_scores,
            "total_queries": num_queries
        }
    
    def run_weight_experiment(
        self, 
        hybrid_search_manager,
        test_queries: List[str],
        weight_combinations: Optional[List[Tuple[float, float]]] = None,
        max_workers: int = 3
    ) -> str:
        """가중치 최적화 실험 실행"""
        
        if weight_combinations is None:
            weight_combinations = self.generate_weight_combinations(
                min_weight=0.0, max_weight=1.0, step=0.1
            )
        
        st.info(f"🔬 {len(weight_combinations)}개 가중치 조합으로 실험 시작")
        st.info(f"📝 테스트 쿼리 수: {len(test_queries)}개")
        
        # 결과를 저장할 리스트
        results = []
        experiment_start_time = datetime.now()
        
        # 프로그레스 바
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 병렬 처리를 위한 ThreadPoolExecutor 사용
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 모든 실험을 스케줄링
            future_to_weights = {
                executor.submit(
                    self.evaluate_search_quality,
                    hybrid_search_manager,
                    test_queries,
                    bm25_weight,
                    vector_weight
                ): (bm25_weight, vector_weight)
                for bm25_weight, vector_weight in weight_combinations
            }
            
            completed = 0
            total_experiments = len(weight_combinations)
            
            # 완료된 실험 결과 수집
            for future in future_to_weights:
                try:
                    bm25_weight, vector_weight = future_to_weights[future]
                    evaluation_result = future.result(timeout=60)  # 60초 타임아웃
                    
                    # 로그 엔트리 생성
                    log_entry = {
                        "timestamp": datetime.now().isoformat(),
                        "experiment_id": f"exp_{experiment_start_time.strftime('%Y%m%d_%H%M%S')}",
                        "bm25_weight": bm25_weight,
                        "vector_weight": vector_weight,
                        "weights": {
                            "bm25": bm25_weight,
                            "vector": vector_weight
                        },
                        "score": evaluation_result["avg_score"],
                        "metrics": evaluation_result,
                        "test_queries": test_queries
                    }
                    
                    results.append(log_entry)
                    
                    # JSON Lines 형식으로 로그 파일에 즉시 저장
                    with open(self.log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
                    
                    completed += 1
                    progress = completed / total_experiments
                    progress_bar.progress(progress)
                    status_text.text(
                        f"진행률: {completed}/{total_experiments} "
                        f"({progress*100:.1f}%) | "
                        f"현재: BM25={bm25_weight:.2f}, Vector={vector_weight:.2f} | "
                        f"점수: {evaluation_result['avg_score']:.4f}"
                    )
                    
                except Exception as e:
                    completed += 1
                    progress = completed / total_experiments
                    progress_bar.progress(progress)
                    st.error(f"실험 실패 - BM25: {bm25_weight}, Vector: {vector_weight}: {str(e)}")
        
        # 실험 완료 메시지
        experiment_duration = (datetime.now() - experiment_start_time).total_seconds()
        st.success(f"✅ 실험 완료! 총 {len(results)}개 조합 테스트 완료 (소요 시간: {experiment_duration:.1f}초)")
        st.success(f"📁 결과가 {self.log_path}에 저장되었습니다.")
        
        return self.log_path
    
    def load_experiment_results(self) -> pd.DataFrame:
        """저장된 실험 결과 로드"""
        if not os.path.exists(self.log_path):
            return pd.DataFrame()
        
        results = []
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line.strip())
                        results.append(data)
            
            return pd.DataFrame(results)
        except Exception as e:
            st.error(f"실험 결과 로드 실패: {str(e)}")
            return pd.DataFrame()
    
    def get_default_test_queries(self) -> List[str]:
        """기본 테스트 쿼리 세트"""
        return [
            "소득세 공제 방법",
            "부가가치세 신고 기한", 
            "사업자 세금 계산",
            "연말정산 공제 항목",
            "원천징수 세율",
            "법인세 계산 방법",
            "양도소득세 면제 조건",
            "상속세 공제 한도",
            "종합부동산세 계산",
            "근로소득세 구간"
        ]
    
    def clear_experiment_log(self) -> bool:
        """실험 로그 파일 삭제"""
        try:
            if os.path.exists(self.log_path):
                os.remove(self.log_path)
                return True
            return True
        except Exception as e:
            st.error(f"로그 파일 삭제 실패: {str(e)}")
            return False


# 전역 인스턴스
_weight_experiment = None

def get_weight_experiment(log_path: str = "./weight_search.log") -> WeightOptimizationExperiment:
    """Weight Optimization Experiment 인스턴스 반환"""
    global _weight_experiment
    if _weight_experiment is None:
        _weight_experiment = WeightOptimizationExperiment(log_path)
    return _weight_experiment