"""
Agent Performance Tracking and Dynamic Selection Module

This module tracks agent performance metrics and enables dynamic model selection
based on task complexity, historical performance, and system load.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import numpy as np

from database import get_database_manager
from sqlalchemy import text
from logging_config import log_info, log_warning, log_debug, log_error
from config_system import config_system
from cache import cache_result

logger = logging.getLogger(__name__)


class DatabaseAdapter:
    """Adapter to provide simple execute/fetch interface for SQLAlchemy database"""
    
    def __init__(self):
        self.db_manager = get_database_manager()
    
    def execute(self, sql, params=None):
        """Execute SQL statement"""
        try:
            with self.db_manager.get_session() as session:
                if params:
                    session.execute(text(sql), params)
                else:
                    session.execute(text(sql))
                session.commit()
        except Exception as e:
            log_error(logger, f"Database execute error: {e}")
            raise
    
    def fetch_one(self, sql, params=None):
        """Fetch one row from SQL query"""
        try:  
            with self.db_manager.get_session() as session:
                if params:
                    result = session.execute(text(sql), params)
                else:
                    result = session.execute(text(sql))
                row = result.first()
                return dict(row._mapping) if row else None
        except Exception as e:
            log_error(logger, f"Database fetch_one error: {e}")
            return None
    
    def fetch_all(self, sql, params=None):
        """Fetch all rows from SQL query"""
        try:
            with self.db_manager.get_session() as session:
                if params:
                    result = session.execute(text(sql), params)
                else:
                    result = session.execute(text(sql))
                return [dict(row._mapping) for row in result]
        except Exception as e:
            log_error(logger, f"Database fetch_all error: {e}")
            return []


@dataclass
class AgentPerformanceMetrics:
    """Performance metrics for an agent"""
    agent_id: str
    model_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0
    average_quality_score: float = 0.0
    average_cost_per_execution: float = 0.0
    success_rate: float = 0.0
    last_execution_time: Optional[datetime] = None
    performance_trend: float = 0.0  # Positive = improving, negative = declining
    
    def update_metrics(self, execution_time: float, success: bool, 
                      quality_score: Optional[float] = None, cost: Optional[float] = None):
        """Update metrics with new execution data"""
        self.total_executions += 1
        
        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
        
        # Update success rate
        self.success_rate = self.successful_executions / self.total_executions
        
        # Update average execution time (moving average)
        self.average_execution_time = (
            (self.average_execution_time * (self.total_executions - 1) + execution_time) 
            / self.total_executions
        )
        
        # Update average quality score if provided
        if quality_score is not None:
            if self.average_quality_score == 0:
                self.average_quality_score = quality_score
            else:
                self.average_quality_score = (
                    (self.average_quality_score * (self.successful_executions - 1) + quality_score)
                    / self.successful_executions
                )
        
        # Update average cost if provided
        if cost is not None:
            self.average_cost_per_execution = (
                (self.average_cost_per_execution * (self.total_executions - 1) + cost)
                / self.total_executions
            )
        
        self.last_execution_time = datetime.now()


class TaskComplexityAnalyzer:
    """Analyze task complexity to help with model selection"""
    
    def __init__(self):
        self.complexity_factors = config_system.get("agent_performance.complexity_factors", {
            "input_length_weight": 0.3,
            "context_depth_weight": 0.2,
            "domain_specificity_weight": 0.2,
            "output_requirements_weight": 0.3
        })
        
        # Thresholds for complexity levels
        self.complexity_thresholds = {
            "simple": 0.3,
            "moderate": 0.6,
            "complex": 0.8,
            "very_complex": 1.0
        }
    
    def analyze_task_complexity(self, task_data: Dict[str, Any]) -> Tuple[float, str]:
        """
        Analyze task complexity and return score and level
        
        Returns:
            Tuple of (complexity_score, complexity_level)
        """
        complexity_score = 0.0
        
        # 1. Input length factor
        input_text = task_data.get('conversation_thread', '') + task_data.get('message_context', '')
        input_length = len(input_text)
        
        # Normalize to 0-1 scale (assuming 10000 chars is very complex)
        input_length_score = min(input_length / 10000, 1.0)
        complexity_score += input_length_score * self.complexity_factors['input_length_weight']
        
        # 2. Context depth factor (number of different data sources)
        context_fields = ['prospect_profile_url', 'prospect_company_url', 
                         'prospect_company_website', 'qubit_context']
        context_depth = sum(1 for field in context_fields if task_data.get(field))
        context_depth_score = context_depth / len(context_fields)
        complexity_score += context_depth_score * self.complexity_factors['context_depth_weight']
        
        # 3. Domain specificity (based on keywords)
        domain_keywords = {
            'technical': ['api', 'integration', 'architecture', 'infrastructure', 'algorithm'],
            'financial': ['roi', 'revenue', 'investment', 'budget', 'cost'],
            'legal': ['compliance', 'regulation', 'contract', 'terms', 'liability'],
            'medical': ['clinical', 'patient', 'treatment', 'diagnosis', 'healthcare']
        }
        
        domain_matches = 0
        for domain, keywords in domain_keywords.items():
            if any(keyword in input_text.lower() for keyword in keywords):
                domain_matches += 1
        
        domain_specificity_score = min(domain_matches / 2, 1.0)  # 2+ domains = max complexity
        complexity_score += domain_specificity_score * self.complexity_factors['domain_specificity_weight']
        
        # 4. Output requirements (based on task type)
        if 'follow_up' in task_data.get('message_context', '').lower():
            output_req_score = 0.7  # Follow-ups are moderately complex
        elif 'cold' in task_data.get('message_context', '').lower():
            output_req_score = 0.9  # Cold outreach is complex
        else:
            output_req_score = 0.5  # Default moderate complexity
        
        complexity_score += output_req_score * self.complexity_factors['output_requirements_weight']
        
        # Determine complexity level
        complexity_level = "simple"
        for level, threshold in self.complexity_thresholds.items():
            if complexity_score <= threshold:
                complexity_level = level
                break
        
        log_debug(logger, f"Task complexity analysis: score={complexity_score:.2f}, level={complexity_level}")
        
        return complexity_score, complexity_level


class DynamicAgentSelector:
    """Select the best agent/model for a given task based on various factors"""
    
    def __init__(self, performance_tracker):
        self.performance_tracker = performance_tracker
        self.complexity_analyzer = TaskComplexityAnalyzer()
        
        # Model capability matrix (can be configured)
        self.model_capabilities = config_system.get("agent_performance.model_capabilities", {
            "gpt-4": {
                "complexity_range": [0.5, 1.0],
                "cost_factor": 1.0,
                "quality_factor": 1.0,
                "speed_factor": 0.7
            },
            "gpt-35-turbo": {
                "complexity_range": [0.0, 0.7],
                "cost_factor": 0.1,
                "quality_factor": 0.8,
                "speed_factor": 1.0
            }
        })
        
        # Selection weights
        self.selection_weights = config_system.get("agent_performance.selection_weights", {
            "performance_history": 0.4,
            "task_complexity_match": 0.3,
            "cost_efficiency": 0.2,
            "current_load": 0.1
        })
    
    def select_agent_model(self, agent_id: str, task_data: Dict[str, Any], 
                          available_models: List[str] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Select the best model for the given agent and task
        
        Returns:
            Tuple of (selected_model, selection_metadata)
        """
        # Get task complexity
        complexity_score, complexity_level = self.complexity_analyzer.analyze_task_complexity(task_data)
        
        # Get available models
        if not available_models:
            available_models = list(self.model_capabilities.keys())
        
        # Score each model
        model_scores = {}
        selection_metadata = {
            "task_complexity": complexity_score,
            "complexity_level": complexity_level,
            "model_scores": {}
        }
        
        for model in available_models:
            score = self._calculate_model_score(
                agent_id, model, complexity_score, task_data
            )
            model_scores[model] = score
            selection_metadata["model_scores"][model] = score
        
        # Select best model
        selected_model = max(model_scores, key=model_scores.get)
        selection_metadata["selected_model"] = selected_model
        selection_metadata["selection_reason"] = self._get_selection_reason(
            selected_model, model_scores, complexity_level
        )
        
        log_info(logger, 
                f"Selected model '{selected_model}' for agent '{agent_id}' "
                f"(complexity: {complexity_level}, score: {model_scores[selected_model]:.2f})")
        
        return selected_model, selection_metadata
    
    def _calculate_model_score(self, agent_id: str, model: str, 
                              complexity_score: float, task_data: Dict[str, Any]) -> float:
        """Calculate score for a model based on multiple factors"""
        score = 0.0
        
        # 1. Performance history score
        metrics = self.performance_tracker.get_agent_model_metrics(agent_id, model)
        if metrics and metrics.total_executions > 0:
            perf_score = (
                metrics.success_rate * 0.4 +
                (metrics.average_quality_score / 100) * 0.4 +
                (1 - min(metrics.average_execution_time / 60, 1)) * 0.2  # Faster is better
            )
        else:
            perf_score = 0.5  # Neutral score for new models
        
        score += perf_score * self.selection_weights['performance_history']
        
        # 2. Task complexity match score
        model_caps = self.model_capabilities.get(model, {})
        complexity_range = model_caps.get('complexity_range', [0, 1])
        
        if complexity_range[0] <= complexity_score <= complexity_range[1]:
            complexity_match_score = 1.0
        else:
            # Penalize based on distance from ideal range
            if complexity_score < complexity_range[0]:
                # Task is simpler than model's ideal range
                complexity_match_score = 1 - (complexity_range[0] - complexity_score)
            else:
                # Task is more complex than model's ideal range
                complexity_match_score = 1 - (complexity_score - complexity_range[1]) * 2  # Heavier penalty
        
        score += max(complexity_match_score, 0) * self.selection_weights['task_complexity_match']
        
        # 3. Cost efficiency score
        cost_factor = model_caps.get('cost_factor', 1.0)
        cost_score = 1 - (cost_factor * 0.7)  # Lower cost = higher score
        score += cost_score * self.selection_weights['cost_efficiency']
        
        # 4. Current load score (simple implementation)
        recent_usage = self.performance_tracker.get_recent_usage(model, minutes=5)
        load_score = 1 - min(recent_usage / 10, 1)  # Penalize if >10 recent uses
        score += load_score * self.selection_weights['current_load']
        
        return score
    
    def _get_selection_reason(self, selected_model: str, model_scores: Dict[str, float], 
                             complexity_level: str) -> str:
        """Generate human-readable reason for model selection"""
        reasons = []
        
        # Check if it's the highest scoring model
        if selected_model == max(model_scores, key=model_scores.get):
            reasons.append(f"Best overall score ({model_scores[selected_model]:.2f})")
        
        # Add complexity match reason
        model_caps = self.model_capabilities.get(selected_model, {})
        if complexity_level in ['complex', 'very_complex'] and model_caps.get('quality_factor', 0) >= 1.0:
            reasons.append("High quality model for complex task")
        elif complexity_level in ['simple', 'moderate'] and model_caps.get('cost_factor', 1) < 0.5:
            reasons.append("Cost-effective model for simple task")
        
        return "; ".join(reasons) if reasons else "Default selection"


class AgentPerformanceTracker:
    """Track and manage agent performance metrics"""
    
    def __init__(self):
        self.db_manager = DatabaseAdapter()
        self.metrics_cache: Dict[str, AgentPerformanceMetrics] = {}
        self.selector = DynamicAgentSelector(self)
        
        # Initialize database table if needed
        self._init_database()
        
        # Load existing metrics
        self._load_metrics_from_db()
    
    def _init_database(self):
        """Initialize performance tracking database table"""
        try:
            self.db_manager.execute("""
                CREATE TABLE IF NOT EXISTS agent_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    execution_time REAL,
                    success BOOLEAN,
                    quality_score REAL,
                    cost REAL,
                    task_complexity REAL,
                    complexity_level TEXT,
                    selected_reason TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    UNIQUE(agent_id, model_name)
                )
            """)
            
            # Create index for performance queries
            self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_performance_timestamp 
                ON agent_performance(timestamp)
            """)
            
            log_info(logger, "Agent performance database initialized")
        except Exception as e:
            log_error(logger, f"Failed to initialize performance database: {e}")
    
    def _load_metrics_from_db(self):
        """Load aggregated metrics from database"""
        try:
            results = self.db_manager.fetch_all("""
                SELECT 
                    agent_id,
                    model_name,
                    COUNT(*) as total_executions,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_executions,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_executions,
                    AVG(execution_time) as avg_execution_time,
                    AVG(CASE WHEN success = 1 THEN quality_score ELSE NULL END) as avg_quality_score,
                    AVG(cost) as avg_cost,
                    MAX(timestamp) as last_execution
                FROM agent_performance
                GROUP BY agent_id, model_name
            """)
            
            for row in results:
                key = f"{row['agent_id']}_{row['model_name']}"
                metrics = AgentPerformanceMetrics(
                    agent_id=row['agent_id'],
                    model_name=row['model_name'],
                    total_executions=row['total_executions'],
                    successful_executions=row['successful_executions'],
                    failed_executions=row['failed_executions'],
                    average_execution_time=row['avg_execution_time'] or 0,
                    average_quality_score=row['avg_quality_score'] or 0,
                    average_cost_per_execution=row['avg_cost'] or 0,
                    success_rate=row['successful_executions'] / row['total_executions'] if row['total_executions'] > 0 else 0,
                    last_execution_time=datetime.fromisoformat(row['last_execution']) if row['last_execution'] else None
                )
                self.metrics_cache[key] = metrics
            
            log_info(logger, f"Loaded {len(self.metrics_cache)} agent performance metrics")
            
        except Exception as e:
            log_error(logger, f"Failed to load performance metrics: {e}")
    
    def track_execution(self, agent_id: str, model_name: str, execution_time: float,
                       success: bool, quality_score: Optional[float] = None,
                       cost: Optional[float] = None, task_data: Optional[Dict[str, Any]] = None,
                       metadata: Optional[Dict[str, Any]] = None):
        """Track an agent execution"""
        try:
            # Calculate task complexity if task data provided
            complexity_score = None
            complexity_level = None
            if task_data:
                complexity_score, complexity_level = self.selector.complexity_analyzer.analyze_task_complexity(task_data)
            
            # Store in database
            self.db_manager.execute("""
                INSERT INTO agent_performance 
                (agent_id, model_name, execution_time, success, quality_score, 
                 cost, task_complexity, complexity_level, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_id, model_name, execution_time, success, quality_score,
                cost, complexity_score, complexity_level,
                json.dumps(metadata) if metadata else None
            ))
            
            # Update cache
            key = f"{agent_id}_{model_name}"
            if key not in self.metrics_cache:
                self.metrics_cache[key] = AgentPerformanceMetrics(
                    agent_id=agent_id,
                    model_name=model_name
                )
            
            self.metrics_cache[key].update_metrics(
                execution_time, success, quality_score, cost
            )
            
            log_debug(logger, 
                     f"Tracked execution for {agent_id}/{model_name}: "
                     f"success={success}, time={execution_time:.2f}s, quality={quality_score}")
            
        except Exception as e:
            log_error(logger, f"Failed to track agent execution: {e}")
    
    def get_agent_model_metrics(self, agent_id: str, model_name: str) -> Optional[AgentPerformanceMetrics]:
        """Get metrics for specific agent and model"""
        key = f"{agent_id}_{model_name}"
        return self.metrics_cache.get(key)
    
    def get_agent_metrics(self, agent_id: str) -> Dict[str, AgentPerformanceMetrics]:
        """Get all metrics for an agent across all models"""
        return {
            model: metrics 
            for key, metrics in self.metrics_cache.items()
            if metrics.agent_id == agent_id
        }
    
    def get_recent_usage(self, model_name: str, minutes: int = 5) -> int:
        """Get number of recent uses of a model"""
        try:
            since = datetime.now() - timedelta(minutes=minutes)
            result = self.db_manager.fetch_one("""
                SELECT COUNT(*) as count
                FROM agent_performance
                WHERE model_name = ? AND timestamp > ?
            """, (model_name, since))
            
            return result['count'] if result else 0
            
        except Exception as e:
            log_error(logger, f"Failed to get recent usage: {e}")
            return 0
    
    def get_performance_trends(self, agent_id: str, days: int = 7) -> Dict[str, Any]:
        """Get performance trends for an agent"""
        try:
            since = datetime.now() - timedelta(days=days)
            
            results = self.db_manager.fetch_all("""
                SELECT 
                    DATE(timestamp) as date,
                    model_name,
                    COUNT(*) as executions,
                    AVG(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_rate,
                    AVG(quality_score) as avg_quality,
                    AVG(execution_time) as avg_time
                FROM agent_performance
                WHERE agent_id = ? AND timestamp > ?
                GROUP BY DATE(timestamp), model_name
                ORDER BY date
            """, (agent_id, since))
            
            # Process into trends
            trends = defaultdict(lambda: {
                'dates': [],
                'success_rates': [],
                'quality_scores': [],
                'execution_times': []
            })
            
            for row in results:
                model = row['model_name']
                trends[model]['dates'].append(row['date'])
                trends[model]['success_rates'].append(row['success_rate'])
                trends[model]['quality_scores'].append(row['avg_quality'] or 0)
                trends[model]['execution_times'].append(row['avg_time'] or 0)
            
            return dict(trends)
            
        except Exception as e:
            log_error(logger, f"Failed to get performance trends: {e}")
            return {}
    
    @cache_result(key_prefix="agent_perf_summary", ttl=300)
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        try:
            # Overall stats
            overall = self.db_manager.fetch_one("""
                SELECT 
                    COUNT(DISTINCT agent_id) as total_agents,
                    COUNT(DISTINCT model_name) as total_models,
                    COUNT(*) as total_executions,
                    AVG(CASE WHEN success = 1 THEN 1 ELSE 0 END) as overall_success_rate,
                    AVG(quality_score) as overall_quality,
                    AVG(execution_time) as overall_time
                FROM agent_performance
                WHERE timestamp > datetime('now', '-30 days')
            """)
            
            # Best performing agent-model combinations
            best_performers = self.db_manager.fetch_all("""
                SELECT 
                    agent_id,
                    model_name,
                    COUNT(*) as executions,
                    AVG(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_rate,
                    AVG(quality_score) as avg_quality
                FROM agent_performance
                WHERE timestamp > datetime('now', '-7 days')
                GROUP BY agent_id, model_name
                HAVING executions > 5
                ORDER BY success_rate DESC, avg_quality DESC
                LIMIT 10
            """)
            
            return {
                "overall_stats": dict(overall) if overall else {},
                "best_performers": [dict(row) for row in best_performers],
                "total_tracked_combinations": len(self.metrics_cache),
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            log_error(logger, f"Failed to get performance summary: {e}")
            return {}


# Create singleton instance
agent_performance_tracker = AgentPerformanceTracker()


def track_agent_execution(agent_id: str, model_name: str, execution_time: float,
                         success: bool, quality_score: Optional[float] = None,
                         cost: Optional[float] = None, task_data: Optional[Dict[str, Any]] = None,
                         metadata: Optional[Dict[str, Any]] = None):
    """
    Track agent execution performance
    
    Args:
        agent_id: ID of the agent
        model_name: Name of the model used
        execution_time: Time taken to execute (seconds)
        success: Whether execution was successful
        quality_score: Quality score of the output (0-100)
        cost: Cost of the execution
        task_data: Original task data for complexity analysis
        metadata: Additional metadata to store
    """
    agent_performance_tracker.track_execution(
        agent_id, model_name, execution_time, success,
        quality_score, cost, task_data, metadata
    )


def select_best_model(agent_id: str, task_data: Dict[str, Any], 
                     available_models: List[str] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Select the best model for an agent and task
    
    Returns:
        Tuple of (selected_model, selection_metadata)
    """
    return agent_performance_tracker.selector.select_agent_model(
        agent_id, task_data, available_models
    )


def get_agent_performance_metrics(agent_id: str) -> Dict[str, Any]:
    """Get performance metrics for an agent"""
    metrics = agent_performance_tracker.get_agent_metrics(agent_id)
    return {
        model: asdict(m) for model, m in metrics.items()
    }


def get_performance_summary() -> Dict[str, Any]:
    """Get overall performance summary"""
    return agent_performance_tracker.get_performance_summary()