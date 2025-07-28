"""
Feedback System Module

This module handles user feedback collection, analysis, and continuous improvement
of AI workflow outputs. It provides functionality for rating outputs, collecting
detailed feedback, and using that feedback to improve future performance.
"""

import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

from database import get_database_manager
from sqlalchemy import text
from logging_config import log_info, log_warning, log_debug, log_error
from config_system import config_system
from cache import cache_result

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """Types of feedback"""
    RATING = "rating"
    DETAILED = "detailed"  
    CORRECTION = "correction"
    SUGGESTION = "suggestion"
    COMPLAINT = "complaint"
    PRAISE = "praise"


class FeedbackSource(Enum):
    """Source of feedback"""
    USER_INTERFACE = "user_interface"
    API = "api"
    AUTOMATED = "automated"
    ADMIN = "admin"
    INTEGRATION = "integration"


class FeedbackStatus(Enum):
    """Feedback processing status"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"
    ARCHIVED = "archived"


@dataclass
class FeedbackEntry:
    """Individual feedback entry"""
    id: str
    execution_id: str
    workflow_id: str
    feedback_type: FeedbackType
    source: FeedbackSource
    user_id: Optional[str] = None
    rating: Optional[int] = None  # 1-5 scale
    content: Optional[str] = None
    suggested_improvement: Optional[str] = None
    original_output: Optional[str] = None
    improved_output: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    status: FeedbackStatus = FeedbackStatus.PENDING
    created_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    implementation_notes: Optional[str] = None


@dataclass 
class FeedbackSummary:
    """Summary statistics for feedback"""
    total_feedback: int
    average_rating: float
    rating_distribution: Dict[int, int]
    feedback_by_type: Dict[str, int]
    recent_feedback_count: int
    improvement_suggestions: int
    implemented_improvements: int
    common_issues: List[str]
    top_workflows_by_feedback: List[Dict[str, Any]]


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


class FeedbackSystem:
    """Comprehensive feedback collection and analysis system"""
    
    def __init__(self):
        self.db_manager = DatabaseAdapter()
        self.config = self._load_config()
        
        # Initialize database tables
        self._init_database()
        
        # Load common issue patterns
        self._load_issue_patterns()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load feedback system configuration"""
        return config_system.get("feedback_system", {
            "enable_auto_analysis": True,
            "min_rating_for_analysis": 3,
            "max_feedback_age_days": 90,
            "enable_sentiment_analysis": True,
            "require_user_id": False,
            "auto_implement_threshold": 0.8,  # Confidence threshold for auto-implementation
            "notification_thresholds": {
                "low_rating_count": 5,
                "repeated_issue_count": 3
            }
        })
    
    def _init_database(self):
        """Initialize feedback system database tables"""
        try:
            # Main feedback table
            self.db_manager.execute("""
                CREATE TABLE IF NOT EXISTS feedback_entries (
                    id TEXT PRIMARY KEY,
                    execution_id TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    user_id TEXT,
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    content TEXT,
                    suggested_improvement TEXT,
                    original_output TEXT,
                    improved_output TEXT,
                    metadata TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at DATETIME,
                    reviewed_by TEXT,
                    implementation_notes TEXT
                )
            """)
            
            # Feedback analysis table for storing analysis results
            self.db_manager.execute("""
                CREATE TABLE IF NOT EXISTS feedback_analysis (
                    id TEXT PRIMARY KEY,
                    feedback_id TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    analysis_result TEXT,
                    confidence_score REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (feedback_id) REFERENCES feedback_entries (id)
                )
            """)
            
            # Feedback themes/patterns table
            self.db_manager.execute("""
                CREATE TABLE IF NOT EXISTS feedback_themes (
                    id TEXT PRIMARY KEY,
                    theme_name TEXT NOT NULL,
                    description TEXT,
                    pattern_keywords TEXT,
                    workflow_ids TEXT,
                    occurrence_count INTEGER DEFAULT 1,
                    severity_level TEXT DEFAULT 'medium',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Improvement tracking table
            self.db_manager.execute("""
                CREATE TABLE IF NOT EXISTS feedback_improvements (
                    id TEXT PRIMARY KEY,
                    feedback_ids TEXT NOT NULL,
                    improvement_type TEXT NOT NULL,
                    description TEXT,
                    implementation_details TEXT,
                    impact_score REAL,
                    implemented_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    implemented_by TEXT,
                    validation_results TEXT
                )
            """)
            
            # Create indexes for performance
            self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_execution_id 
                ON feedback_entries(execution_id)
            """)
            
            self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_workflow_id 
                ON feedback_entries(workflow_id)
            """)
            
            self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_created_at 
                ON feedback_entries(created_at)
            """)
            
            self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_feedback_rating 
                ON feedback_entries(rating)
            """)
            
            log_info(logger, "Feedback system database initialized")
            
        except Exception as e:
            log_error(logger, f"Failed to initialize feedback database: {e}")
    
    def _load_issue_patterns(self):
        """Load common issue patterns for analysis"""
        self.issue_patterns = {
            'poor_personalization': [
                'generic', 'template', 'not personalized', 'copy paste', 'mass message'
            ],
            'incorrect_information': [
                'wrong', 'incorrect', 'outdated', 'inaccurate', 'mistake', 'error'
            ],
            'tone_issues': [
                'too formal', 'too casual', 'unprofessional', 'inappropriate tone', 'rude'
            ],
            'length_issues': [
                'too long', 'too short', 'verbose', 'brief', 'lengthy', 'concise'
            ],
            'relevance_issues': [
                'irrelevant', 'off-topic', 'not related', 'doesn\'t match', 'unrelated'
            ],
            'grammar_issues': [
                'grammar', 'spelling', 'typo', 'grammatical', 'language error'
            ]
        }
    
    def submit_feedback(self, 
                       execution_id: str,
                       workflow_id: str,
                       feedback_type: FeedbackType,
                       source: FeedbackSource,
                       user_id: Optional[str] = None,
                       rating: Optional[int] = None,
                       content: Optional[str] = None,
                       suggested_improvement: Optional[str] = None,
                       original_output: Optional[str] = None,
                       improved_output: Optional[str] = None,
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit new feedback entry
        
        Returns:
            str: Feedback ID
        """
        try:
            feedback_id = str(uuid.uuid4())
            
            # Validate rating if provided
            if rating is not None and (rating < 1 or rating > 5):
                raise ValueError("Rating must be between 1 and 5")
            
            # Create feedback entry
            feedback = FeedbackEntry(
                id=feedback_id,
                execution_id=execution_id,
                workflow_id=workflow_id,
                feedback_type=feedback_type,
                source=source,
                user_id=user_id,
                rating=rating,
                content=content,
                suggested_improvement=suggested_improvement,
                original_output=original_output,
                improved_output=improved_output,
                metadata=metadata,
                created_at=datetime.now()
            )
            
            # Save to database
            self.db_manager.execute("""
                INSERT INTO feedback_entries 
                (id, execution_id, workflow_id, feedback_type, source, user_id, 
                 rating, content, suggested_improvement, original_output, 
                 improved_output, metadata, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback.id,
                feedback.execution_id,
                feedback.workflow_id,
                feedback.feedback_type.value,
                feedback.source.value,
                feedback.user_id,
                feedback.rating,
                feedback.content,
                feedback.suggested_improvement,
                feedback.original_output,
                feedback.improved_output,
                json.dumps(feedback.metadata) if feedback.metadata else None,
                feedback.status.value,
                feedback.created_at.isoformat()
            ))
            
            # Perform automatic analysis if enabled
            if self.config.get("enable_auto_analysis", True):
                self._analyze_feedback_async(feedback_id)
            
            log_info(logger, f"Feedback submitted: {feedback_id} for execution {execution_id}")
            return feedback_id
            
        except Exception as e:
            log_error(logger, f"Failed to submit feedback: {e}")
            raise
    
    def _analyze_feedback_async(self, feedback_id: str):
        """Perform asynchronous feedback analysis"""
        try:
            feedback = self.get_feedback(feedback_id)
            if not feedback:
                return
            
            analyses = []
            
            # Sentiment analysis
            if feedback.content and self.config.get("enable_sentiment_analysis", True):
                sentiment = self._analyze_sentiment(feedback.content)
                analyses.append({
                    'type': 'sentiment',
                    'result': sentiment,
                    'confidence': sentiment.get('confidence', 0.0)
                })
            
            # Issue pattern matching
            if feedback.content:
                issues = self._detect_issue_patterns(feedback.content)
                if issues:
                    analyses.append({
                        'type': 'issue_patterns',
                        'result': issues,
                        'confidence': max([issue['confidence'] for issue in issues])
                    })
            
            # Rating analysis
            if feedback.rating:
                rating_analysis = self._analyze_rating_context(feedback)
                analyses.append({
                    'type': 'rating_analysis',
                    'result': rating_analysis,
                    'confidence': 0.8
                })
            
            # Save analyses
            for analysis in analyses:
                analysis_id = str(uuid.uuid4())
                self.db_manager.execute("""
                    INSERT INTO feedback_analysis 
                    (id, feedback_id, analysis_type, analysis_result, confidence_score)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    analysis_id,
                    feedback_id,
                    analysis['type'],
                    json.dumps(analysis['result']),
                    analysis['confidence']
                ))
            
            log_debug(logger, f"Completed analysis for feedback {feedback_id}")
            
        except Exception as e:
            log_error(logger, f"Failed to analyze feedback {feedback_id}: {e}")
    
    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of feedback text"""
        # Simple keyword-based sentiment analysis
        positive_keywords = ['good', 'great', 'excellent', 'helpful', 'useful', 'perfect', 'love', 'amazing']
        negative_keywords = ['bad', 'terrible', 'awful', 'useless', 'wrong', 'hate', 'horrible', 'poor']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_keywords if word in text_lower)
        negative_count = sum(1 for word in negative_keywords if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            confidence = min(positive_count / (positive_count + negative_count + 1), 0.9)
        elif negative_count > positive_count:
            sentiment = 'negative'
            confidence = min(negative_count / (positive_count + negative_count + 1), 0.9)
        else:
            sentiment = 'neutral'
            confidence = 0.5
        
        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'positive_signals': positive_count,
            'negative_signals': negative_count
        }
    
    def _detect_issue_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Detect known issue patterns in feedback text"""
        detected_issues = []
        text_lower = text.lower()
        
        for issue_type, keywords in self.issue_patterns.items():
            matches = [keyword for keyword in keywords if keyword in text_lower]
            if matches:
                confidence = min(len(matches) / len(keywords), 0.9)
                detected_issues.append({
                    'issue_type': issue_type,
                    'matched_keywords': matches,
                    'confidence': confidence
                })
        
        return detected_issues
    
    def _analyze_rating_context(self, feedback: FeedbackEntry) -> Dict[str, Any]:
        """Analyze rating in context of other data"""
        analysis = {
            'rating': feedback.rating,
            'category': 'poor' if feedback.rating <= 2 else 'average' if feedback.rating <= 3 else 'good'
        }
        
        # Get historical ratings for this workflow
        historical_ratings = self.db_manager.fetch_all("""
            SELECT rating FROM feedback_entries 
            WHERE workflow_id = ? AND rating IS NOT NULL
            ORDER BY created_at DESC LIMIT 10
        """, (feedback.workflow_id,))
        
        if historical_ratings:
            ratings = [r['rating'] for r in historical_ratings]
            avg_rating = sum(ratings) / len(ratings)
            analysis['historical_average'] = avg_rating
            analysis['trend'] = 'improving' if feedback.rating > avg_rating else 'declining'
        
        return analysis
    
    def get_feedback(self, feedback_id: str) -> Optional[FeedbackEntry]:
        """Get feedback entry by ID"""
        try:
            row = self.db_manager.fetch_one("""
                SELECT * FROM feedback_entries WHERE id = ?
            """, (feedback_id,))
            
            if not row:
                return None
            
            return FeedbackEntry(
                id=row['id'],
                execution_id=row['execution_id'],
                workflow_id=row['workflow_id'],
                feedback_type=FeedbackType(row['feedback_type']),
                source=FeedbackSource(row['source']),
                user_id=row['user_id'],
                rating=row['rating'],
                content=row['content'],
                suggested_improvement=row['suggested_improvement'],
                original_output=row['original_output'],
                improved_output=row['improved_output'],
                metadata=json.loads(row['metadata']) if row['metadata'] else None,
                status=FeedbackStatus(row['status']),
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                reviewed_at=datetime.fromisoformat(row['reviewed_at']) if row['reviewed_at'] else None,
                reviewed_by=row['reviewed_by'],
                implementation_notes=row['implementation_notes']
            )
            
        except Exception as e:
            log_error(logger, f"Failed to get feedback {feedback_id}: {e}")
            return None
    
    def get_feedback_for_execution(self, execution_id: str) -> List[FeedbackEntry]:
        """Get all feedback for a specific execution"""
        try:
            rows = self.db_manager.fetch_all("""
                SELECT * FROM feedback_entries 
                WHERE execution_id = ? 
                ORDER BY created_at DESC
            """, (execution_id,))
            
            feedback_list = []
            for row in rows:
                feedback = FeedbackEntry(
                    id=row['id'],
                    execution_id=row['execution_id'],
                    workflow_id=row['workflow_id'],
                    feedback_type=FeedbackType(row['feedback_type']),
                    source=FeedbackSource(row['source']),
                    user_id=row['user_id'],
                    rating=row['rating'],
                    content=row['content'],
                    suggested_improvement=row['suggested_improvement'],
                    original_output=row['original_output'],
                    improved_output=row['improved_output'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else None,
                    status=FeedbackStatus(row['status']),
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    reviewed_at=datetime.fromisoformat(row['reviewed_at']) if row['reviewed_at'] else None,
                    reviewed_by=row['reviewed_by'],
                    implementation_notes=row['implementation_notes']
                )
                feedback_list.append(feedback)
            
            return feedback_list
            
        except Exception as e:
            log_error(logger, f"Failed to get feedback for execution {execution_id}: {e}")
            return []
    
    def get_feedback_for_workflow(self, workflow_id: str, limit: int = 100) -> List[FeedbackEntry]:
        """Get feedback for a specific workflow"""
        try:
            rows = self.db_manager.fetch_all("""
                SELECT * FROM feedback_entries 
                WHERE workflow_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (workflow_id, limit))
            
            feedback_list = []
            for row in rows:
                feedback = FeedbackEntry(
                    id=row['id'],
                    execution_id=row['execution_id'],
                    workflow_id=row['workflow_id'],
                    feedback_type=FeedbackType(row['feedback_type']),
                    source=FeedbackSource(row['source']),
                    user_id=row['user_id'],
                    rating=row['rating'],
                    content=row['content'],
                    suggested_improvement=row['suggested_improvement'],
                    original_output=row['original_output'],
                    improved_output=row['improved_output'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else None,
                    status=FeedbackStatus(row['status']),
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    reviewed_at=datetime.fromisoformat(row['reviewed_at']) if row['reviewed_at'] else None,
                    reviewed_by=row['reviewed_by'],
                    implementation_notes=row['implementation_notes']
                )
                feedback_list.append(feedback)
            
            return feedback_list
            
        except Exception as e:
            log_error(logger, f"Failed to get feedback for workflow {workflow_id}: {e}")
            return []
    
    @cache_result(key_prefix="feedback_summary", ttl=300)
    def get_feedback_summary(self, workflow_id: Optional[str] = None, days: int = 30) -> FeedbackSummary:
        """Get comprehensive feedback summary"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            
            # Base query conditions
            where_conditions = ["created_at > ?"]
            params = [since_date.isoformat()]
            
            if workflow_id:
                where_conditions.append("workflow_id = ?")
                params.append(workflow_id)
            
            where_clause = " AND ".join(where_conditions)
            
            # Total feedback count
            total_result = self.db_manager.fetch_one(f"""
                SELECT COUNT(*) as total FROM feedback_entries WHERE {where_clause}
            """, params)
            total_feedback = total_result['total'] if total_result else 0
            
            # Average rating
            rating_result = self.db_manager.fetch_one(f"""
                SELECT AVG(rating) as avg_rating FROM feedback_entries 
                WHERE {where_clause} AND rating IS NOT NULL
            """, params)
            average_rating = rating_result['avg_rating'] if rating_result and rating_result['avg_rating'] else 0.0
            
            # Rating distribution
            rating_dist_results = self.db_manager.fetch_all(f"""
                SELECT rating, COUNT(*) as count FROM feedback_entries 
                WHERE {where_clause} AND rating IS NOT NULL
                GROUP BY rating
            """, params)
            rating_distribution = {r['rating']: r['count'] for r in rating_dist_results}
            
            # Feedback by type
            type_results = self.db_manager.fetch_all(f"""
                SELECT feedback_type, COUNT(*) as count FROM feedback_entries 
                WHERE {where_clause}
                GROUP BY feedback_type
            """, params)
            feedback_by_type = {r['feedback_type']: r['count'] for r in type_results}
            
            # Recent feedback (last 7 days)
            recent_date = datetime.now() - timedelta(days=7)
            recent_params = params + [recent_date.isoformat()]
            recent_result = self.db_manager.fetch_one(f"""
                SELECT COUNT(*) as count FROM feedback_entries 
                WHERE {where_clause} AND created_at > ?
            """, recent_params)
            recent_feedback_count = recent_result['count'] if recent_result else 0
            
            # Improvement suggestions
            improvement_result = self.db_manager.fetch_one(f"""
                SELECT COUNT(*) as count FROM feedback_entries 
                WHERE {where_clause} AND suggested_improvement IS NOT NULL
            """, params)
            improvement_suggestions = improvement_result['count'] if improvement_result else 0
            
            # Implemented improvements
            implemented_result = self.db_manager.fetch_one(f"""
                SELECT COUNT(*) as count FROM feedback_entries 
                WHERE {where_clause} AND status = 'implemented'
            """, params)
            implemented_improvements = implemented_result['count'] if implemented_result else 0
            
            # Common issues (from analysis)
            common_issues = self._get_common_issues(workflow_id, days)
            
            # Top workflows by feedback
            top_workflows = self._get_top_workflows_by_feedback(days)
            
            return FeedbackSummary(
                total_feedback=total_feedback,
                average_rating=float(average_rating),
                rating_distribution=rating_distribution,
                feedback_by_type=feedback_by_type,
                recent_feedback_count=recent_feedback_count,
                improvement_suggestions=improvement_suggestions,
                implemented_improvements=implemented_improvements,
                common_issues=common_issues,
                top_workflows_by_feedback=top_workflows
            )
            
        except Exception as e:
            log_error(logger, f"Failed to get feedback summary: {e}")
            return FeedbackSummary(
                total_feedback=0,
                average_rating=0.0,
                rating_distribution={},
                feedback_by_type={},
                recent_feedback_count=0,
                improvement_suggestions=0,
                implemented_improvements=0,
                common_issues=[],
                top_workflows_by_feedback=[]
            )
    
    def _get_common_issues(self, workflow_id: Optional[str], days: int) -> List[str]:
        """Get most common issues from feedback analysis"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            
            # Get issue patterns from analysis
            where_conditions = ["fa.created_at > ?", "fa.analysis_type = 'issue_patterns'"]
            params = [since_date.isoformat()]
            
            if workflow_id:
                where_conditions.append("fe.workflow_id = ?")
                params.append(workflow_id)
            
            where_clause = " AND ".join(where_conditions)
            
            results = self.db_manager.fetch_all(f"""
                SELECT fa.analysis_result FROM feedback_analysis fa
                JOIN feedback_entries fe ON fa.feedback_id = fe.id
                WHERE {where_clause}
            """, params)
            
            issue_counts = {}
            for result in results:
                try:
                    analysis = json.loads(result['analysis_result'])
                    for issue in analysis:
                        issue_type = issue.get('issue_type')
                        if issue_type:
                            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
                except:
                    continue
            
            # Return top 5 most common issues
            sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
            return [issue[0] for issue in sorted_issues[:5]]
            
        except Exception as e:
            log_error(logger, f"Failed to get common issues: {e}")
            return []
    
    def _get_top_workflows_by_feedback(self, days: int) -> List[Dict[str, Any]]:
        """Get workflows with most feedback"""
        try:
            since_date = datetime.now() - timedelta(days=days)
            
            results = self.db_manager.fetch_all("""
                SELECT 
                    workflow_id,
                    COUNT(*) as feedback_count,
                    AVG(rating) as avg_rating,
                    COUNT(CASE WHEN rating <= 2 THEN 1 END) as negative_feedback
                FROM feedback_entries 
                WHERE created_at > ?
                GROUP BY workflow_id
                ORDER BY feedback_count DESC
                LIMIT 10
            """, (since_date.isoformat(),))
            
            return [{
                'workflow_id': r['workflow_id'],
                'feedback_count': r['feedback_count'],
                'average_rating': float(r['avg_rating']) if r['avg_rating'] else 0.0,
                'negative_feedback_count': r['negative_feedback']
            } for r in results]
            
        except Exception as e:
            log_error(logger, f"Failed to get top workflows: {e}")
            return []
    
    def update_feedback_status(self, feedback_id: str, status: FeedbackStatus, 
                              reviewed_by: Optional[str] = None, 
                              implementation_notes: Optional[str] = None) -> bool:
        """Update feedback status"""
        try:
            self.db_manager.execute("""
                UPDATE feedback_entries 
                SET status = ?, reviewed_at = ?, reviewed_by = ?, implementation_notes = ?
                WHERE id = ?
            """, (
                status.value,
                datetime.now().isoformat(),
                reviewed_by,
                implementation_notes,
                feedback_id
            ))
            
            log_info(logger, f"Updated feedback {feedback_id} status to {status.value}")
            return True
            
        except Exception as e:
            log_error(logger, f"Failed to update feedback status: {e}")
            return False
    
    def get_pending_feedback(self, limit: int = 50) -> List[FeedbackEntry]:
        """Get feedback entries that need review"""
        try:
            rows = self.db_manager.fetch_all("""
                SELECT * FROM feedback_entries 
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT ?
            """, (limit,))
            
            feedback_list = []
            for row in rows:
                feedback = FeedbackEntry(
                    id=row['id'],
                    execution_id=row['execution_id'],
                    workflow_id=row['workflow_id'],
                    feedback_type=FeedbackType(row['feedback_type']),
                    source=FeedbackSource(row['source']),
                    user_id=row['user_id'],
                    rating=row['rating'],
                    content=row['content'],
                    suggested_improvement=row['suggested_improvement'],
                    original_output=row['original_output'],
                    improved_output=row['improved_output'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else None,
                    status=FeedbackStatus(row['status']),
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
                    reviewed_at=datetime.fromisoformat(row['reviewed_at']) if row['reviewed_at'] else None,
                    reviewed_by=row['reviewed_by'],
                    implementation_notes=row['implementation_notes']
                )
                feedback_list.append(feedback)
            
            return feedback_list
            
        except Exception as e:
            log_error(logger, f"Failed to get pending feedback: {e}")
            return []


# Create singleton instance
feedback_system = FeedbackSystem()


# Convenience functions for external use
def submit_feedback(execution_id: str, workflow_id: str, feedback_type: FeedbackType,
                   source: FeedbackSource, **kwargs) -> str:
    """Submit feedback entry"""
    return feedback_system.submit_feedback(
        execution_id, workflow_id, feedback_type, source, **kwargs
    )


def get_feedback_for_execution(execution_id: str) -> List[FeedbackEntry]:
    """Get feedback for execution"""
    return feedback_system.get_feedback_for_execution(execution_id)


def get_feedback_summary(workflow_id: Optional[str] = None, days: int = 30) -> FeedbackSummary:
    """Get feedback summary"""
    return feedback_system.get_feedback_summary(workflow_id, days)


def update_feedback_status(feedback_id: str, status: FeedbackStatus, 
                          reviewed_by: Optional[str] = None,
                          implementation_notes: Optional[str] = None) -> bool:
    """Update feedback status"""
    return feedback_system.update_feedback_status(
        feedback_id, status, reviewed_by, implementation_notes
    )


def get_pending_feedback(limit: int = 50) -> List[FeedbackEntry]:
    """Get pending feedback entries"""
    return feedback_system.get_pending_feedback(limit)