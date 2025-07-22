"""
Quality analysis charts and metrics calculation for RAG search evaluation
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Any, Optional, Tuple
import math
from collections import defaultdict


class QualityMetrics:
    """Calculate and visualize search quality metrics"""
    
    @staticmethod
    def calculate_precision_at_k(relevant_docs: List[str], retrieved_docs: List[str], k: int = 5) -> float:
        """Calculate Precision@K
        
        Args:
            relevant_docs: List of relevant document IDs
            retrieved_docs: List of retrieved document IDs (in order)
            k: Number of top results to consider
            
        Returns:
            Precision@K score (0.0 to 1.0)
        """
        if not retrieved_docs or k == 0:
            return 0.0
            
        top_k_retrieved = retrieved_docs[:k]
        relevant_set = set(relevant_docs)
        
        relevant_in_top_k = sum(1 for doc in top_k_retrieved if doc in relevant_set)
        return relevant_in_top_k / min(k, len(top_k_retrieved))
    
    @staticmethod
    def calculate_recall_at_k(relevant_docs: List[str], retrieved_docs: List[str], k: int = 5) -> float:
        """Calculate Recall@K
        
        Args:
            relevant_docs: List of relevant document IDs
            retrieved_docs: List of retrieved document IDs (in order)
            k: Number of top results to consider
            
        Returns:
            Recall@K score (0.0 to 1.0)
        """
        if not relevant_docs:
            return 0.0
            
        top_k_retrieved = retrieved_docs[:k]
        relevant_set = set(relevant_docs)
        
        relevant_in_top_k = sum(1 for doc in top_k_retrieved if doc in relevant_set)
        return relevant_in_top_k / len(relevant_set)
    
    @staticmethod
    def calculate_ndcg_at_k(relevant_docs: List[str], retrieved_docs: List[str], 
                           relevance_scores: Optional[Dict[str, float]] = None, k: int = 5) -> float:
        """Calculate NDCG@K (Normalized Discounted Cumulative Gain)
        
        Args:
            relevant_docs: List of relevant document IDs
            retrieved_docs: List of retrieved document IDs (in order)
            relevance_scores: Dict mapping doc_id to relevance score (0-1). If None, uses binary relevance.
            k: Number of top results to consider
            
        Returns:
            NDCG@K score (0.0 to 1.0)
        """
        if not retrieved_docs or k == 0:
            return 0.0
            
        top_k_retrieved = retrieved_docs[:k]
        relevant_set = set(relevant_docs)
        
        # Calculate DCG
        dcg = 0.0
        for i, doc in enumerate(top_k_retrieved):
            if doc in relevant_set:
                relevance = relevance_scores.get(doc, 1.0) if relevance_scores else 1.0
                dcg += relevance / math.log2(i + 2)  # i+2 because log2(1) is 0
        
        # Calculate IDCG (Ideal DCG)
        ideal_relevance = []
        for doc in relevant_docs:
            relevance = relevance_scores.get(doc, 1.0) if relevance_scores else 1.0
            ideal_relevance.append(relevance)
        
        ideal_relevance.sort(reverse=True)  # Sort by relevance score descending
        
        idcg = 0.0
        for i, relevance in enumerate(ideal_relevance[:k]):
            idcg += relevance / math.log2(i + 2)
        
        return dcg / idcg if idcg > 0 else 0.0
    
    @staticmethod
    def calculate_mean_reciprocal_rank(relevant_docs: List[str], retrieved_docs: List[str]) -> float:
        """Calculate Mean Reciprocal Rank (MRR)
        
        Args:
            relevant_docs: List of relevant document IDs
            retrieved_docs: List of retrieved document IDs (in order)
            
        Returns:
            MRR score (0.0 to 1.0)
        """
        if not retrieved_docs:
            return 0.0
            
        relevant_set = set(relevant_docs)
        
        for i, doc in enumerate(retrieved_docs):
            if doc in relevant_set:
                return 1.0 / (i + 1)
        
        return 0.0


class SearchResultAnalyzer:
    """Analyze and compare different search results"""
    
    def __init__(self):
        self.metrics_calculator = QualityMetrics()
    
    def analyze_search_results(self, query: str, search_results: Dict[str, List[Dict]], 
                             ground_truth: Optional[List[str]] = None, 
                             k_values: List[int] = [1, 3, 5, 10]) -> pd.DataFrame:
        """Analyze multiple search results and calculate metrics
        
        Args:
            query: Search query
            search_results: Dict with keys like 'vector', 'bm25', 'hybrid' and values as search results
            ground_truth: List of relevant document IDs (if available)
            k_values: List of K values to calculate metrics for
            
        Returns:
            DataFrame with calculated metrics
        """
        results = []
        
        for method_name, results_list in search_results.items():
            if not results_list:
                continue
                
            # Extract document IDs from search results
            doc_ids = []
            scores = []
            for result in results_list:
                if isinstance(result, dict):
                    # Handle different result formats
                    if 'id' in result:
                        doc_ids.append(result['id'])
                        scores.append(result.get('score', result.get('distance', 0)))
                    elif 'metadata' in result and 'doc_id' in result['metadata']:
                        doc_ids.append(result['metadata']['doc_id'])
                        scores.append(result.get('score', result.get('distance', 0)))
                    else:
                        # Fallback: use string representation as ID
                        doc_ids.append(str(result))
                        scores.append(1.0)
            
            # Calculate metrics for each k value
            for k in k_values:
                row = {
                    'method': method_name,
                    'query': query,
                    'k': k,
                    'num_results': len(doc_ids)
                }
                
                if ground_truth:
                    # Calculate metrics with ground truth
                    row['precision@k'] = self.metrics_calculator.calculate_precision_at_k(
                        ground_truth, doc_ids, k
                    )
                    row['recall@k'] = self.metrics_calculator.calculate_recall_at_k(
                        ground_truth, doc_ids, k
                    )
                    row['ndcg@k'] = self.metrics_calculator.calculate_ndcg_at_k(
                        ground_truth, doc_ids, k=k
                    )
                    row['mrr'] = self.metrics_calculator.calculate_mean_reciprocal_rank(
                        ground_truth, doc_ids
                    ) if k == max(k_values) else None  # Calculate MRR only once
                else:
                    # Without ground truth, calculate basic metrics
                    row['precision@k'] = None
                    row['recall@k'] = None
                    row['ndcg@k'] = None
                    row['mrr'] = None
                
                # Add score statistics
                if scores:
                    row['avg_score'] = np.mean(scores[:k])
                    row['max_score'] = max(scores[:k])
                    row['min_score'] = min(scores[:k])
                else:
                    row['avg_score'] = None
                    row['max_score'] = None
                    row['min_score'] = None
                
                results.append(row)
        
        return pd.DataFrame(results)


def draw_metric_comparison_chart(metrics_df: pd.DataFrame, metric_name: str = 'precision@k') -> go.Figure:
    """Draw comparison chart for different search methods
    
    Args:
        metrics_df: DataFrame with calculated metrics
        metric_name: Name of the metric to visualize
        
    Returns:
        Plotly figure
    """
    if metrics_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No data available", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=16))
        return fig
    
    # Filter out rows with None values for the selected metric
    valid_df = metrics_df.dropna(subset=[metric_name])
    
    if valid_df.empty:
        fig = go.Figure()
        fig.add_annotation(text=f"No valid data for {metric_name}", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False,
                          font=dict(size=16))
        return fig
    
    # Create line chart
    fig = px.line(valid_df, x='k', y=metric_name, color='method',
                  title=f'{metric_name.upper()} Comparison by Search Method',
                  markers=True)
    
    fig.update_layout(
        xaxis_title="K (Number of Results)",
        yaxis_title=metric_name.replace('@k', '@K'),
        legend_title="Search Method",
        hovermode='x unified'
    )
    
    return fig


def draw_score_distribution_chart(search_results: Dict[str, List[Dict]]) -> go.Figure:
    """Draw score distribution comparison chart
    
    Args:
        search_results: Dict with search method names and their results
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    for method_name, results_list in search_results.items():
        if not results_list:
            continue
            
        scores = []
        for result in results_list:
            if isinstance(result, dict):
                score = result.get('score', result.get('distance', 0))
                scores.append(score)
        
        if scores:
            fig.add_trace(go.Box(
                y=scores,
                name=method_name,
                boxpoints='outliers'
            ))
    
    fig.update_layout(
        title="Score Distribution by Search Method",
        yaxis_title="Score",
        xaxis_title="Search Method"
    )
    
    return fig


def draw_hit_highlight_table(search_results: Dict[str, List[Dict]], 
                           ground_truth: Optional[List[str]] = None,
                           max_results: int = 10) -> None:
    """Draw highlighted results table showing hits/misses
    
    Args:
        search_results: Dict with search method names and their results
        ground_truth: List of relevant document IDs
        max_results: Maximum number of results to show
    """
    if not search_results:
        st.warning("검색 결과가 없습니다.")
        return
    
    # Prepare data for table
    table_data = []
    
    for method_name, results_list in search_results.items():
        if not results_list:
            continue
            
        for i, result in enumerate(results_list[:max_results]):
            if isinstance(result, dict):
                doc_id = result.get('id', result.get('metadata', {}).get('doc_id', f'doc_{i}'))
                content = result.get('content', result.get('text', 'N/A'))[:200] + "..."
                score = result.get('score', result.get('distance', 0))
                
                # Check if it's a hit (relevant)
                is_hit = ground_truth and doc_id in ground_truth if ground_truth else None
                
                table_data.append({
                    'Method': method_name,
                    'Rank': i + 1,
                    'Document ID': doc_id,
                    'Score': f"{score:.4f}",
                    'Content Preview': content,
                    'Relevant': '✅ Hit' if is_hit else ('❌ Miss' if is_hit is False else '❔ Unknown')
                })
    
    if table_data:
        df = pd.DataFrame(table_data)
        
        # Color coding function
        def highlight_hits(row):
            if row['Relevant'] == '✅ Hit':
                return ['background-color: #d4edda'] * len(row)
            elif row['Relevant'] == '❌ Miss':
                return ['background-color: #f8d7da'] * len(row)
            else:
                return [''] * len(row)
        
        st.subheader("📋 검색 결과 상세 비교")
        styled_df = df.style.apply(highlight_hits, axis=1)
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.warning("표시할 검색 결과가 없습니다.")


def create_quality_analysis_dashboard(query: str, search_results: Dict[str, List[Dict]], 
                                    ground_truth: Optional[List[str]] = None) -> None:
    """Create complete quality analysis dashboard
    
    Args:
        query: Search query
        search_results: Dict with search method names and their results
        ground_truth: List of relevant document IDs (optional)
    """
    st.subheader("📊 검색 품질 분석 대시보드")
    
    if not search_results or all(not results for results in search_results.values()):
        st.warning("분석할 검색 결과가 없습니다.")
        return
    
    # Calculate metrics
    analyzer = SearchResultAnalyzer()
    metrics_df = analyzer.analyze_search_results(
        query=query, 
        search_results=search_results, 
        ground_truth=ground_truth,
        k_values=[1, 3, 5, 10]
    )
    
    # Display metrics table
    if not metrics_df.empty:
        st.subheader("📈 성능 지표 요약")
        
        # Create pivot table for better visualization
        if ground_truth:
            metric_cols = ['precision@k', 'recall@k', 'ndcg@k']
            for metric in metric_cols:
                if metric in metrics_df.columns:
                    pivot_df = metrics_df.pivot(index='method', columns='k', values=metric)
                    st.write(f"**{metric.upper()}**")
                    st.dataframe(pivot_df.style.format("{:.3f}"), use_container_width=True)
        else:
            st.info("정답 데이터가 없어 품질 지표를 계산할 수 없습니다. 점수 분포만 표시됩니다.")
    
    # Create visualizations in columns
    col1, col2 = st.columns(2)
    
    with col1:
        if ground_truth and not metrics_df.empty:
            # Precision@K chart
            precision_fig = draw_metric_comparison_chart(metrics_df, 'precision@k')
            st.plotly_chart(precision_fig, use_container_width=True)
            
            # NDCG@K chart
            ndcg_fig = draw_metric_comparison_chart(metrics_df, 'ndcg@k')
            st.plotly_chart(ndcg_fig, use_container_width=True)
    
    with col2:
        # Score distribution chart
        score_dist_fig = draw_score_distribution_chart(search_results)
        st.plotly_chart(score_dist_fig, use_container_width=True)
        
        # Results summary
        st.subheader("📋 결과 요약")
        summary_data = []
        for method_name, results_list in search_results.items():
            summary_data.append({
                'Method': method_name,
                'Results Count': len(results_list) if results_list else 0,
                'Avg Score': f"{np.mean([r.get('score', r.get('distance', 0)) for r in results_list]):.4f}" 
                           if results_list else "N/A"
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)
    
    # Hit/Miss table
    draw_hit_highlight_table(search_results, ground_truth)
    
    # Download options
    st.subheader("💾 결과 다운로드")
    col1, col2 = st.columns(2)
    
    with col1:
        if not metrics_df.empty:
            csv = metrics_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📈 성능 지표 CSV 다운로드",
                data=csv,
                file_name=f"quality_metrics_{query[:20]}.csv",
                mime="text/csv"
            )
    
    with col2:
        # Export search results as JSON
        import json
        results_json = json.dumps(search_results, ensure_ascii=False, indent=2, default=str)
        st.download_button(
            label="🔍 검색 결과 JSON 다운로드",
            data=results_json,
            file_name=f"search_results_{query[:20]}.json",
            mime="application/json"
        )