"""Visualization utilities module"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, Optional


class VisualizationUtils:
    """Visualization utilities class"""
    
    @staticmethod
    def create_metric_bar_chart(results_df: pd.DataFrame, metric: str) -> plt.Figure:
        """Create bar chart for metric"""
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.barplot(x=results_df.index, y=results_df[metric], ax=ax)
        ax.set_title(f"Question-wise {metric.replace('_', ' ').title()} Score")
        ax.set_xlabel("Question Number")
        ax.set_ylabel("Score")
        ax.set_ylim(0, 1)
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig
    
    @staticmethod
    def create_radar_chart(avg_scores: Dict[str, float]) -> Optional[plt.Figure]:
        """Create radar chart"""
        if len(avg_scores) <= 2:
            return None
            
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        
        metrics = list(avg_scores.keys())
        scores = list(avg_scores.values())
        
        # Close the chart
        scores += scores[:1]
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]
        
        ax.plot(angles, scores, marker='o')
        ax.fill(angles, scores, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([m.replace('_', ' ').title() for m in metrics])
        ax.set_ylim(0, 1)
        ax.set_title("RAGAS Evaluation Metrics - Average Scores")
        
        return fig
    
    @staticmethod
    def create_comparison_bar_chart(data: Dict[str, float], title: str = "Comparison Chart") -> plt.Figure:
        """Create comparison bar chart"""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        keys = list(data.keys())
        values = list(data.values())
        
        bars = ax.bar(keys, values)
        ax.set_title(title)
        ax.set_ylabel("Score")
        ax.set_ylim(0, 1)
        
        # Display values on bars
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{value:.3f}', ha='center', va='bottom')
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        return fig
    
    @staticmethod
    def create_score_distribution(results_df: pd.DataFrame, metric: str) -> plt.Figure:
        """Create score distribution histogram"""
        fig, ax = plt.subplots(figsize=(8, 6))
        
        ax.hist(results_df[metric], bins=10, alpha=0.7, edgecolor='black')
        ax.set_title(f"{metric.replace('_', ' ').title()} Score Distribution")
        ax.set_xlabel("Score")
        ax.set_ylabel("Frequency")
        ax.set_xlim(0, 1)
        
        # Add mean line
        mean_score = results_df[metric].mean()
        ax.axvline(mean_score, color='red', linestyle='--', 
                  label=f'Mean: {mean_score:.3f}')
        ax.legend()
        
        plt.tight_layout()
        return fig
    
    @staticmethod
    def create_multi_metric_comparison(results_df: pd.DataFrame) -> plt.Figure:
        """Create multi-metric comparison chart"""
        metric_columns = [col for col in results_df.columns if col not in ["question", "answer"]]
        
        if not metric_columns:
            return None
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # All metric scores for each question
        x = np.arange(len(results_df))
        width = 0.8 / len(metric_columns)
        
        for i, metric in enumerate(metric_columns):
            offset = (i - len(metric_columns)/2) * width + width/2
            ax.bar(x + offset, results_df[metric], width, 
                  label=metric.replace('_', ' ').title())
        
        ax.set_xlabel('Question Number')
        ax.set_ylabel('Score')
        ax.set_title('Question-wise All Metric Score Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels([f'Q{i+1}' for i in range(len(results_df))])
        ax.legend()
        ax.set_ylim(0, 1)
        
        plt.tight_layout()
        return fig