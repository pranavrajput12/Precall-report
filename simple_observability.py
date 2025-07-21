"""
Simple in-memory observability system for workflow tracking
No external dependencies required
"""

import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class WorkflowMetric:
    """Simple metric tracking"""
    workflow_id: str
    workflow_name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    status: str = "running"
    steps_completed: int = 0
    total_steps: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """Performance statistics"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    success_rate: float = 0.0
    

class SimpleObservability:
    """Simple observability manager with in-memory tracking"""
    
    def __init__(self):
        self.metrics: Dict[str, WorkflowMetric] = {}
        self.performance_history: List[WorkflowMetric] = []
        self.counters: Dict[str, int] = defaultdict(int)
        self.is_initialized = True
        
    def start_workflow(self, workflow_id: str, workflow_name: str, metadata: Dict[str, Any] = None) -> None:
        """Start tracking a workflow execution"""
        metric = WorkflowMetric(
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            start_time=time.time(),
            metadata=metadata or {}
        )
        self.metrics[workflow_id] = metric
        self.counters["workflows_started"] += 1
        logger.info(f"Started tracking workflow {workflow_id}")
        
    def update_workflow(self, workflow_id: str, **updates) -> None:
        """Update workflow metrics"""
        if workflow_id in self.metrics:
            metric = self.metrics[workflow_id]
            for key, value in updates.items():
                if hasattr(metric, key):
                    setattr(metric, key, value)
                    
    def complete_workflow(self, workflow_id: str, status: str = "completed", error: Optional[str] = None) -> None:
        """Complete workflow tracking"""
        if workflow_id in self.metrics:
            metric = self.metrics[workflow_id]
            metric.end_time = time.time()
            metric.duration = metric.end_time - metric.start_time
            metric.status = status
            metric.error = error
            
            # Move to history
            self.performance_history.append(metric)
            del self.metrics[workflow_id]
            
            # Update counters
            if status == "completed":
                self.counters["workflows_completed"] += 1
            else:
                self.counters["workflows_failed"] += 1
                
            logger.info(f"Completed tracking workflow {workflow_id} with status {status}")
            
    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment a counter"""
        self.counters[name] += value
        
    def get_performance_stats(self) -> PerformanceStats:
        """Get performance statistics"""
        stats = PerformanceStats()
        
        if not self.performance_history:
            return stats
            
        completed = [m for m in self.performance_history if m.status == "completed"]
        failed = [m for m in self.performance_history if m.status == "failed"]
        
        stats.total_executions = len(self.performance_history)
        stats.successful_executions = len(completed)
        stats.failed_executions = len(failed)
        
        if completed:
            durations = [m.duration for m in completed if m.duration]
            if durations:
                stats.average_duration = sum(durations) / len(durations)
                stats.min_duration = min(durations)
                stats.max_duration = max(durations)
                
        if stats.total_executions > 0:
            stats.success_rate = stats.successful_executions / stats.total_executions
            
        return stats
        
    def get_active_workflows(self) -> List[WorkflowMetric]:
        """Get currently active workflows"""
        return list(self.metrics.values())
        
    def get_recent_workflows(self, limit: int = 10) -> List[WorkflowMetric]:
        """Get recent workflow executions"""
        return self.performance_history[-limit:] if self.performance_history else []
        
    def get_counters(self) -> Dict[str, int]:
        """Get all counters"""
        return dict(self.counters)
        
    def get_trace_summary(self) -> Dict[str, Any]:
        """Get trace summary (compatible with old API)"""
        stats = self.get_performance_stats()
        recent = self.get_recent_workflows()
        
        return {
            "total_traces": stats.total_executions,
            "recent_traces": [
                {
                    "workflow_id": w.workflow_id,
                    "workflow_name": w.workflow_name,
                    "duration": w.duration,
                    "status": w.status,
                    "timestamp": datetime.fromtimestamp(w.start_time).isoformat()
                }
                for w in recent
            ],
            "timestamp": datetime.now().isoformat(),
            "performance": {
                "average_duration": stats.average_duration,
                "success_rate": stats.success_rate * 100,
                "total_executions": stats.total_executions
            },
            "active_workflows": len(self.metrics)
        }
        
    def initialize(self) -> None:
        """Initialize (no-op for compatibility)"""
        pass
        
    def instrument_fastapi_app(self, app) -> None:
        """Instrument FastAPI app (no-op for compatibility)"""
        pass
        
    # Context managers for compatibility
    def trace_workflow(self, workflow_name: str, **attributes):
        """Context manager for workflow tracing"""
        class WorkflowTracer:
            def __init__(self, obs_manager, workflow_name, attributes):
                self.obs_manager = obs_manager
                self.workflow_name = workflow_name
                self.workflow_id = f"{workflow_name}_{int(time.time() * 1000)}"
                self.attributes = attributes
                
            def __enter__(self):
                self.obs_manager.start_workflow(self.workflow_id, self.workflow_name, self.attributes)
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type:
                    self.obs_manager.complete_workflow(self.workflow_id, "failed", str(exc_val))
                else:
                    self.obs_manager.complete_workflow(self.workflow_id, "completed")
                    
        return WorkflowTracer(self, workflow_name, attributes)
        
    def trace_agent(self, agent_id: str, task_description: str = "", **attributes):
        """Context manager for agent tracing"""
        class AgentTracer:
            def __init__(self, obs_manager, agent_id):
                self.obs_manager = obs_manager
                self.agent_id = agent_id
                
            def __enter__(self):
                self.obs_manager.increment_counter(f"agent_{self.agent_id}_calls")
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type:
                    self.obs_manager.increment_counter(f"agent_{self.agent_id}_errors")
                    
        return AgentTracer(self, agent_id)
        
    def record_cache_hit(self, cache_type: str, key: str) -> None:
        """Record cache hit"""
        self.increment_counter(f"cache_{cache_type}_hits")
        
    def record_cache_miss(self, cache_type: str, key: str) -> None:
        """Record cache miss"""
        self.increment_counter(f"cache_{cache_type}_misses")
        
    def record_token_usage(self, agent_id: str, prompt_tokens: int, completion_tokens: int) -> None:
        """Record token usage"""
        total_tokens = prompt_tokens + completion_tokens
        self.increment_counter(f"tokens_{agent_id}", total_tokens)
        self.increment_counter("total_tokens", total_tokens)


# Create global instance for compatibility
simple_observability = SimpleObservability()