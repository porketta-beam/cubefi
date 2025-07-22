"""Workflow status management module"""

import time
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class StepStatus:
    """Individual workflow step status"""
    name: str
    status: str = "pending"  # pending, in_progress, completed, error
    progress: float = 0.0  # 0-100%
    last_updated: float = field(default_factory=time.time)
    details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    def update(self, status: str = None, progress: float = None, details: Dict[str, Any] = None, error: str = None):
        """Update step status"""
        if status:
            self.status = status
        if progress is not None:
            self.progress = progress
        if details:
            self.details.update(details)
        if error:
            self.error_message = error
            self.status = "error"
        self.last_updated = time.time()
    
    def get_status_emoji(self) -> str:
        """Get status emoji"""
        emoji_map = {
            "pending": "⏳",
            "in_progress": "🔄",
            "completed": "✅",
            "error": "❌"
        }
        return emoji_map.get(self.status, "❓")
    
    def get_last_updated_text(self) -> str:
        """Get human-readable last updated time"""
        now = time.time()
        diff = now - self.last_updated
        
        if diff < 60:
            return f"{int(diff)}초 전"
        elif diff < 3600:
            return f"{int(diff/60)}분 전"
        elif diff < 86400:
            return f"{int(diff/3600)}시간 전"
        else:
            return f"{int(diff/86400)}일 전"


class WorkflowStatusManager:
    """Workflow status management class"""
    
    def __init__(self):
        self.steps = {
            "embedding": StepStatus("Document Embedding", "pending"),
            "question_generation": StepStatus("Question Generation", "pending"),
            "evaluation": StepStatus("Question Evaluation", "pending")
        }
        self.current_step = "embedding"
        self.workflow_started = False
        self.workflow_completed = False
        self.start_time = None
        self.completion_time = None
    
    def get_step_status(self, step: str) -> StepStatus:
        """Get specific step status"""
        return self.steps.get(step)
    
    def update_step_status(self, step: str, status: str = None, progress: float = None, 
                          details: Dict[str, Any] = None, error: str = None):
        """Update specific step status"""
        if step in self.steps:
            self.steps[step].update(status, progress, details, error)
            
            # Update current step
            if status == "in_progress":
                self.current_step = step
                if not self.workflow_started:
                    self.workflow_started = True
                    self.start_time = time.time()
            
            # Check if workflow is completed
            if status == "completed":
                self._check_workflow_completion()
    
    def _check_workflow_completion(self):
        """Check if entire workflow is completed"""
        all_completed = all(step.status == "completed" for step in self.steps.values())
        if all_completed and not self.workflow_completed:
            self.workflow_completed = True
            self.completion_time = time.time()
    
    def get_overall_progress(self) -> float:
        """Get overall workflow progress percentage"""
        if not self.workflow_started:
            return 0.0
        
        total_progress = sum(step.progress for step in self.steps.values())
        return total_progress / len(self.steps)
    
    def get_workflow_status(self) -> str:
        """Get overall workflow status"""
        if self.workflow_completed:
            return "completed"
        elif self.workflow_started:
            return "in_progress"
        else:
            return "pending"
    
    def get_next_step(self) -> Optional[str]:
        """Get next step to execute"""
        step_order = ["embedding", "question_generation", "evaluation"]
        
        for step in step_order:
            if self.steps[step].status in ["pending", "error"]:
                return step
        
        return None
    
    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get comprehensive workflow summary"""
        return {
            "overall_status": self.get_workflow_status(),
            "overall_progress": self.get_overall_progress(),
            "current_step": self.current_step,
            "next_step": self.get_next_step(),
            "workflow_started": self.workflow_started,
            "workflow_completed": self.workflow_completed,
            "start_time": self.start_time,
            "completion_time": self.completion_time,
            "steps": {name: {
                "status": step.status,
                "progress": step.progress,
                "last_updated": step.last_updated,
                "details": step.details,
                "error_message": step.error_message
            } for name, step in self.steps.items()}
        }
    
    def reset_workflow(self):
        """Reset entire workflow"""
        for step in self.steps.values():
            step.status = "pending"
            step.progress = 0.0
            step.details = {}
            step.error_message = None
            step.last_updated = time.time()
        
        self.current_step = "embedding"
        self.workflow_started = False
        self.workflow_completed = False
        self.start_time = None
        self.completion_time = None
    
    def get_step_display_info(self, step: str) -> Dict[str, Any]:
        """Get step information for display"""
        step_obj = self.steps.get(step)
        if not step_obj:
            return {}
        
        return {
            "name": step_obj.name,
            "emoji": step_obj.get_status_emoji(),
            "status": step_obj.status,
            "progress": step_obj.progress,
            "last_updated": step_obj.get_last_updated_text(),
            "details": step_obj.details,
            "error": step_obj.error_message
        }