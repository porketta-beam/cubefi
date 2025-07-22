"""Weight Optimization Visualization Module"""

import json
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from typing import Dict, List, Tuple, Optional, Any
from scipy.interpolate import griddata
import seaborn as sns
import matplotlib.pyplot as plt


class WeightVisualizationManager:
    """가중치 최적화 결과 시각화 관리 클래스"""
    
    def __init__(self):
        self.df = None
        self.best_combination = None
        
    def load_weight_data(self, log_path: str = "./weight_search.log") -> bool:
        """weight_search.log 파일에서 데이터 로드"""
        if not os.path.exists(log_path):
            st.error(f"로그 파일을 찾을 수 없습니다: {log_path}")
            return False
        
        try:
            data_list = []
            with open(log_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            data = json.loads(line.strip())
                            
                            # 필요한 데이터 추출
                            row = {
                                'timestamp': data.get('timestamp'),
                                'experiment_id': data.get('experiment_id'),
                                'bm25_weight': data.get('bm25_weight', 0.0),
                                'vector_weight': data.get('vector_weight', 0.0),
                                'score': data.get('score', 0.0),
                                'avg_latency_ms': data.get('metrics', {}).get('avg_latency_ms', 0.0),
                                'error_rate': data.get('metrics', {}).get('error_rate', 0.0),
                                'score_std': data.get('metrics', {}).get('score_std', 0.0),
                                'total_queries': data.get('metrics', {}).get('total_queries', 0)
                            }
                            data_list.append(row)
                            
                        except json.JSONDecodeError as e:
                            st.warning(f"라인 {line_num}에서 JSON 파싱 오류: {str(e)}")
                            continue
                            
            if data_list:
                self.df = pd.DataFrame(data_list)
                
                # 데이터 타입 변환
                self.df['bm25_weight'] = pd.to_numeric(self.df['bm25_weight'], errors='coerce')
                self.df['vector_weight'] = pd.to_numeric(self.df['vector_weight'], errors='coerce')
                self.df['score'] = pd.to_numeric(self.df['score'], errors='coerce')
                self.df['avg_latency_ms'] = pd.to_numeric(self.df['avg_latency_ms'], errors='coerce')
                
                # 결측값 제거
                self.df = self.df.dropna(subset=['bm25_weight', 'vector_weight', 'score'])
                
                # 최적 조합 찾기
                self.best_combination = self.find_best_combination()
                
                st.success(f"✅ {len(self.df)}개의 실험 결과를 성공적으로 로드했습니다.")
                return True
            else:
                st.error("유효한 데이터를 찾을 수 없습니다.")
                return False
                
        except Exception as e:
            st.error(f"데이터 로드 실패: {str(e)}")
            return False
    
    def find_best_combination(self) -> Optional[Dict]:
        """최고 성능의 가중치 조합 찾기"""
        if self.df is None or self.df.empty:
            return None
        
        # 점수가 가장 높은 조합 찾기
        best_idx = self.df['score'].idxmax()
        best_row = self.df.loc[best_idx]
        
        return {
            'bm25_weight': best_row['bm25_weight'],
            'vector_weight': best_row['vector_weight'], 
            'score': best_row['score'],
            'avg_latency_ms': best_row['avg_latency_ms'],
            'error_rate': best_row['error_rate']
        }
    
    def create_2d_scatter_plot(self, color_metric: str = 'score') -> go.Figure:
        """2D 산점도 생성"""
        if self.df is None or self.df.empty:
            st.error("데이터가 로드되지 않았습니다.")
            return None
        
        # 컬러맵 설정
        color_scales = {
            'score': 'Viridis',
            'avg_latency_ms': 'Reds_r', 
            'error_rate': 'Reds_r',
            'score_std': 'Blues_r'
        }
        
        fig = px.scatter(
            self.df,
            x='bm25_weight',
            y='vector_weight', 
            color=color_metric,
            size='score',
            hover_data=['score', 'avg_latency_ms', 'error_rate'],
            title=f'가중치 조합별 {color_metric} 분포',
            labels={
                'bm25_weight': 'BM25 가중치',
                'vector_weight': '벡터 가중치',
                'score': '성능 점수',
                'avg_latency_ms': '평균 응답시간 (ms)',
                'error_rate': '오류율'
            },
            color_continuous_scale=color_scales.get(color_metric, 'Viridis')
        )
        
        # 최적 조합 표시
        if self.best_combination:
            fig.add_scatter(
                x=[self.best_combination['bm25_weight']],
                y=[self.best_combination['vector_weight']],
                mode='markers+text',
                marker=dict(size=15, color='red', symbol='star'),
                text=['최적'],
                textposition='top center',
                name='최적 조합',
                showlegend=True
            )
        
        fig.update_layout(
            width=800,
            height=600,
            font_family="Arial",
            title_x=0.5
        )
        
        return fig
    
    def create_3d_surface_plot(self) -> go.Figure:
        """3D 표면 차트 생성"""
        if self.df is None or self.df.empty:
            st.error("데이터가 로드되지 않았습니다.")
            return None
        
        try:
            # 그리드 데이터 생성 (interpolation 사용)
            bm25_range = np.linspace(self.df['bm25_weight'].min(), 
                                   self.df['bm25_weight'].max(), 50)
            vector_range = np.linspace(self.df['vector_weight'].min(), 
                                     self.df['vector_weight'].max(), 50)
            
            BM25, VECTOR = np.meshgrid(bm25_range, vector_range)
            
            # 점수 데이터를 그리드에 맞게 보간
            points = self.df[['bm25_weight', 'vector_weight']].values
            values = self.df['score'].values
            
            SCORE = griddata(points, values, (BM25, VECTOR), method='cubic', fill_value=0)
            
            # 3D Surface Plot
            fig = go.Figure(data=[
                go.Surface(
                    x=BM25,
                    y=VECTOR,
                    z=SCORE,
                    colorscale='Viridis',
                    showscale=True,
                    colorbar=dict(title="성능 점수")
                )
            ])
            
            # 원본 데이터 포인트 추가
            fig.add_scatter3d(
                x=self.df['bm25_weight'],
                y=self.df['vector_weight'],
                z=self.df['score'],
                mode='markers',
                marker=dict(size=4, color='red', symbol='circle'),
                name='실제 측정값'
            )
            
            # 최적 조합 표시
            if self.best_combination:
                fig.add_scatter3d(
                    x=[self.best_combination['bm25_weight']],
                    y=[self.best_combination['vector_weight']],
                    z=[self.best_combination['score']],
                    mode='markers+text',
                    marker=dict(size=12, color='gold', symbol='star'),
                    text=['최적'],
                    textposition='top center',
                    name='최적 조합'
                )
            
            fig.update_layout(
                title='가중치 조합별 성능 점수 3D Surface',
                scene=dict(
                    xaxis_title='BM25 가중치',
                    yaxis_title='벡터 가중치', 
                    zaxis_title='성능 점수',
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.5))
                ),
                width=900,
                height=700,
                font_family="Arial"
            )
            
            return fig
            
        except Exception as e:
            st.error(f"3D 차트 생성 실패: {str(e)}")
            return None
    
    def create_heatmap(self, metric: str = 'score') -> go.Figure:
        """히트맵 생성"""
        if self.df is None or self.df.empty:
            st.error("데이터가 로드되지 않았습니다.")
            return None
        
        try:
            # 피벗 테이블 생성
            pivot_data = self.df.pivot_table(
                values=metric,
                index='vector_weight',
                columns='bm25_weight',
                aggfunc='mean',
                fill_value=0
            )
            
            fig = px.imshow(
                pivot_data,
                aspect='auto',
                title=f'가중치 조합별 {metric} 히트맵',
                labels=dict(
                    x="BM25 가중치",
                    y="벡터 가중치", 
                    color=metric
                ),
                color_continuous_scale='Viridis'
            )
            
            fig.update_layout(
                width=800,
                height=600,
                font_family="Arial",
                title_x=0.5
            )
            
            return fig
            
        except Exception as e:
            st.error(f"히트맵 생성 실패: {str(e)}")
            return None
    
    def create_performance_comparison_chart(self) -> go.Figure:
        """성능 지표 비교 차트"""
        if self.df is None or self.df.empty:
            st.error("데이터가 로드되지 않았습니다.")
            return None
        
        # 상위 10개 조합 선택
        top_combinations = self.df.nlargest(10, 'score').copy()
        top_combinations['combination'] = (
            top_combinations['bm25_weight'].round(2).astype(str) + ':' +
            top_combinations['vector_weight'].round(2).astype(str)
        )
        
        # 멀티 메트릭 차트 생성
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('성능 점수', '평균 응답시간', '오류율', '점수 표준편차'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 성능 점수
        fig.add_trace(
            go.Bar(x=top_combinations['combination'], y=top_combinations['score'], 
                  name='성능 점수', marker_color='blue'),
            row=1, col=1
        )
        
        # 평균 응답시간
        fig.add_trace(
            go.Bar(x=top_combinations['combination'], y=top_combinations['avg_latency_ms'],
                  name='응답시간 (ms)', marker_color='green'),
            row=1, col=2
        )
        
        # 오류율
        fig.add_trace(
            go.Bar(x=top_combinations['combination'], y=top_combinations['error_rate'],
                  name='오류율', marker_color='red'),
            row=2, col=1
        )
        
        # 점수 표준편차
        fig.add_trace(
            go.Bar(x=top_combinations['combination'], y=top_combinations['score_std'],
                  name='점수 표준편차', marker_color='orange'),
            row=2, col=2
        )
        
        fig.update_layout(
            height=800,
            showlegend=False,
            title_text="상위 10개 가중치 조합 성능 비교",
            font_family="Arial"
        )
        
        # x축 레이블 회전
        fig.update_xaxes(tickangle=45)
        
        return fig
    
    def get_optimization_insights(self) -> Dict[str, Any]:
        """최적화 인사이트 생성"""
        if self.df is None or self.df.empty:
            return {}
        
        insights = {}
        
        # 기본 통계
        insights['total_combinations'] = len(self.df)
        insights['best_score'] = self.df['score'].max()
        insights['worst_score'] = self.df['score'].min()
        insights['avg_score'] = self.df['score'].mean()
        insights['score_std'] = self.df['score'].std()
        
        # 최적/최악 조합
        best_idx = self.df['score'].idxmax()
        worst_idx = self.df['score'].idxmin()
        
        insights['best_combination'] = {
            'bm25_weight': self.df.loc[best_idx, 'bm25_weight'],
            'vector_weight': self.df.loc[best_idx, 'vector_weight'],
            'score': self.df.loc[best_idx, 'score']
        }
        
        insights['worst_combination'] = {
            'bm25_weight': self.df.loc[worst_idx, 'bm25_weight'],
            'vector_weight': self.df.loc[worst_idx, 'vector_weight'], 
            'score': self.df.loc[worst_idx, 'score']
        }
        
        # 가중치 범위별 분석
        bm25_high = self.df[self.df['bm25_weight'] > 0.6]['score'].mean()
        bm25_low = self.df[self.df['bm25_weight'] < 0.4]['score'].mean()
        vector_high = self.df[self.df['vector_weight'] > 0.6]['score'].mean()
        vector_low = self.df[self.df['vector_weight'] < 0.4]['score'].mean()
        
        insights['weight_analysis'] = {
            'bm25_high_performance': bm25_high,
            'bm25_low_performance': bm25_low,
            'vector_high_performance': vector_high,
            'vector_low_performance': vector_low
        }
        
        # 권장사항 생성
        recommendations = []
        
        if bm25_high > bm25_low:
            recommendations.append("BM25 가중치를 높게 설정하는 것이 성능에 도움됩니다.")
        else:
            recommendations.append("BM25 가중치를 낮게 설정하는 것이 성능에 도움됩니다.")
            
        if vector_high > vector_low:
            recommendations.append("벡터 가중치를 높게 설정하는 것이 성능에 도움됩니다.")
        else:
            recommendations.append("벡터 가중치를 낮게 설정하는 것이 성능에 도움됩니다.")
        
        insights['recommendations'] = recommendations
        
        return insights


# 전역 인스턴스
_visualization_manager = None

def get_visualization_manager() -> WeightVisualizationManager:
    """Visualization Manager 인스턴스 반환"""
    global _visualization_manager
    if _visualization_manager is None:
        _visualization_manager = WeightVisualizationManager()
    return _visualization_manager