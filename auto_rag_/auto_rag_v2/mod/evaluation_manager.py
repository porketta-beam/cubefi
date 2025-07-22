"""Evaluation management module"""

import pandas as pd
from typing import List, Dict
from datasets import Dataset
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from ragas.evaluation import evaluate


class EvaluationManager:
    """RAGAS evaluation management class"""
    
    def __init__(self):
        self.evaluation_results = None
        self.evaluation_data = None
        
    def evaluate_rag_system(self, questions: List[str], db, rag_manager, 
                           metrics_config: Dict[str, bool]) -> pd.DataFrame:
        """Execute RAG system evaluation"""
        try:
            # Generate evaluation data
            evaluation_data = {
                "question": [],
                "answer": [],
                "contexts": []
            }
            
            if metrics_config.get('use_context_precision', False) or metrics_config.get('use_context_recall', False):
                evaluation_data["reference"] = []
            
            # Generate answers for each question
            for question in questions:
                answer, contexts = rag_manager.get_answer(question)
                
                evaluation_data["question"].append(question)
                evaluation_data["answer"].append(answer)
                evaluation_data["contexts"].append(contexts)
                
                if metrics_config.get('use_context_precision', False) or metrics_config.get('use_context_recall', False):
                    evaluation_data["reference"].append(contexts[0] if contexts else "")
            
            # Create evaluation dataset
            eval_dataset = Dataset.from_dict(evaluation_data)
            
            # Select evaluation metrics
            metrics = []
            if metrics_config.get('use_faithfulness', False):
                metrics.append(faithfulness)
            if metrics_config.get('use_answer_relevancy', False):
                metrics.append(answer_relevancy)
            if metrics_config.get('use_context_precision', False):
                metrics.append(context_precision)
            if metrics_config.get('use_context_recall', False):
                metrics.append(context_recall)
            
            # Execute evaluation
            results = evaluate(eval_dataset, metrics=metrics)
            
            # Create results dataframe
            results_df = pd.DataFrame({
                "question": evaluation_data["question"],
                "answer": evaluation_data["answer"]
            })
            
            for metric in metrics:
                results_df[metric.name] = results[metric.name]
            
            self.evaluation_results = results_df
            self.evaluation_data = evaluation_data
            
            return results_df
            
        except Exception as e:
            raise Exception(f"Evaluation execution failed: {str(e)}")
    
    def get_average_scores(self) -> Dict[str, float]:
        """Get average scores"""
        if self.evaluation_results is None:
            return {}
        
        metric_columns = [col for col in self.evaluation_results.columns if col not in ["question", "answer"]]
        if metric_columns:
            return self.evaluation_results[metric_columns].mean().to_dict()
        return {}
    
    def get_results_dataframe(self) -> pd.DataFrame:
        """Get evaluation results dataframe"""
        return self.evaluation_results
    
    def clear_results(self):
        """Clear evaluation results"""
        self.evaluation_results = None
        self.evaluation_data = None