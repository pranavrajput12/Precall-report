"""
Database configuration and connection management for CrewAI Workflow Platform.

This module provides database connectivity for both SQLite (development) and
PostgreSQL (production) with automatic migration support.
"""

import os
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, Boolean, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime

from config_system import config_system
from logging_config import log_info, log_error, log_warning, log_debug

logger = logging.getLogger(__name__)

Base = declarative_base()

class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self):
        """Initialize database configuration"""
        db_config = config_system.get("database", {})
        
        # Database type (sqlite, postgresql)
        self.db_type = db_config.get("type", "sqlite")
        
        # SQLite configuration
        self.sqlite_path = db_config.get("sqlite_path", "data/crewai.db")
        
        # PostgreSQL configuration
        self.postgres_host = db_config.get("postgres_host", "localhost")
        self.postgres_port = db_config.get("postgres_port", 5432)
        self.postgres_user = db_config.get("postgres_user", "crewai")
        self.postgres_password = db_config.get("postgres_password", "")
        self.postgres_database = db_config.get("postgres_database", "crewai_workflow")
        
        # Connection pool settings
        self.pool_size = db_config.get("pool_size", 10)
        self.max_overflow = db_config.get("max_overflow", 20)
        self.pool_timeout = db_config.get("pool_timeout", 30)
        self.pool_recycle = db_config.get("pool_recycle", 3600)
        
        # Migration settings
        self.auto_migrate = db_config.get("auto_migrate", True)
        self.backup_before_migrate = db_config.get("backup_before_migrate", True)
        
    def get_database_url(self) -> str:
        """
        Get database URL based on configuration
        
        Returns:
            str: Database connection URL
        """
        if self.db_type == "postgresql":
            # Get from environment variables first
            postgres_url = os.getenv("DATABASE_URL")
            if postgres_url:
                return postgres_url
                
            # Build from configuration
            password_part = f":{self.postgres_password}" if self.postgres_password else ""
            return (f"postgresql://{self.postgres_user}{password_part}@"
                   f"{self.postgres_host}:{self.postgres_port}/{self.postgres_database}")
        else:
            # SQLite
            os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
            return f"sqlite:///{self.sqlite_path}"


class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self):
        """Initialize database manager"""
        self.config = DatabaseConfig()
        self.engine = None
        self.SessionLocal = None
        self.metadata = MetaData()
        self._initialize_engine()
        self._create_tables()
        
    def _initialize_engine(self):
        """Initialize database engine"""
        database_url = self.config.get_database_url()
        
        try:
            if self.config.db_type == "postgresql":
                # PostgreSQL engine with connection pooling
                self.engine = create_engine(
                    database_url,
                    pool_size=self.config.pool_size,
                    max_overflow=self.config.max_overflow,
                    pool_timeout=self.config.pool_timeout,
                    pool_recycle=self.config.pool_recycle,
                    echo=config_system.get("app.debug", False)
                )
            else:
                # SQLite engine
                self.engine = create_engine(
                    database_url,
                    poolclass=StaticPool,
                    connect_args={"check_same_thread": False},
                    echo=config_system.get("app.debug", False)
                )
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            log_info(logger, f"Database engine initialized: {self.config.db_type}")
            
        except Exception as e:
            log_error(logger, f"Failed to initialize database engine: {str(e)}")
            raise
            
    def _create_tables(self):
        """Create database tables"""
        try:
            # Define core tables
            self._define_tables()
            
            # Create all tables
            self.metadata.create_all(bind=self.engine)
            
            log_info(logger, "Database tables created/verified")
            
        except Exception as e:
            log_error(logger, f"Failed to create database tables: {str(e)}")
            raise
    
    def _define_tables(self):
        """Define database table schemas"""
        
        # Configuration storage table
        self.config_table = Table(
            'configurations',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('key', String(255), unique=True, nullable=False),
            Column('value', JSON, nullable=False),
            Column('environment', String(50), nullable=False, default='default'),
            Column('version', Integer, nullable=False, default=1),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
            Column('created_by', String(100)),
            Column('description', Text)
        )
        
        # Execution history table
        self.execution_history_table = Table(
            'execution_history',
            self.metadata,
            Column('id', String(50), primary_key=True),
            Column('workflow_id', String(100), nullable=False),
            Column('workflow_name', String(255)),
            Column('status', String(50), nullable=False),
            Column('started_at', DateTime, nullable=False),
            Column('completed_at', DateTime),
            Column('duration', Integer),  # seconds
            Column('input_data', JSON),
            Column('output_data', JSON),
            Column('error_message', Text),
            Column('steps', JSON),
            Column('current_step', String(100)),
            Column('progress', Integer, default=0),
            Column('executed_by', String(100)),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        # FAQ knowledge base table
        self.faq_table = Table(
            'faq_entries',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('question', Text, nullable=False),
            Column('answer', Text, nullable=False),
            Column('category', String(100)),
            Column('keywords', Text),
            Column('embedding', JSON),  # Store embeddings as JSON
            Column('usage_count', Integer, default=0),
            Column('last_used', DateTime),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
            Column('created_by', String(100)),
            Column('is_active', Boolean, default=True)
        )
        
        # User management table
        self.users_table = Table(
            'users',
            self.metadata,
            Column('id', String(50), primary_key=True),
            Column('username', String(100), unique=True, nullable=False),
            Column('email', String(255), unique=True),
            Column('password_hash', String(255), nullable=False),
            Column('role', String(50), nullable=False, default='user'),
            Column('is_active', Boolean, default=True),
            Column('last_login', DateTime),
            Column('failed_login_attempts', Integer, default=0),
            Column('locked_until', DateTime),
            Column('created_at', DateTime, default=datetime.utcnow),
            Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        )
        
        # Performance metrics table
        self.metrics_table = Table(
            'performance_metrics',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('timestamp', DateTime, nullable=False, default=datetime.utcnow),
            Column('metric_type', String(100), nullable=False),
            Column('metric_name', String(255), nullable=False),
            Column('value', JSON, nullable=False),
            Column('tags', JSON),  # Additional metadata
            Column('workflow_id', String(100)),
            Column('agent_id', String(100))
        )
        
        # Evaluation history table
        self.evaluation_history_table = Table(
            'evaluation_history',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('execution_id', String(50), nullable=False),
            Column('workflow_id', String(100), nullable=False),
            Column('timestamp', DateTime, nullable=False, default=datetime.utcnow),
            Column('quality_score', Integer, nullable=False),
            Column('response_rate', JSON),  # Predicted response rate
            Column('criteria_scores', JSON),  # Detailed criteria scores
            Column('feedback', Text),
            Column('message_content', Text),
            Column('channel', String(50)),
            Column('word_count', Integer),
            Column('evaluated_by', String(100)),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        # Observability metrics table
        self.observability_metrics_table = Table(
            'observability_metrics',
            self.metadata,
            Column('id', Integer, primary_key=True),
            Column('execution_id', String(50), nullable=False),
            Column('workflow_id', String(100), nullable=False),
            Column('timestamp', DateTime, nullable=False, default=datetime.utcnow),
            Column('duration_ms', Integer),
            Column('token_usage', JSON),  # Input/output tokens
            Column('cache_hits', Integer, default=0),
            Column('cache_misses', Integer, default=0),
            Column('step_durations', JSON),  # Duration for each step
            Column('error_count', Integer, default=0),
            Column('warning_count', Integer, default=0),
            Column('memory_usage_mb', Integer),
            Column('cpu_usage_percent', JSON),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
    
    @contextmanager
    def get_session(self):
        """
        Get database session with automatic cleanup
        
        Yields:
            Session: SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            log_error(logger, f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            log_info(logger, "Database connection test successful")
            return True
        except Exception as e:
            log_error(logger, f"Database connection test failed: {str(e)}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get database health status
        
        Returns:
            Dict[str, Any]: Health status information
        """
        try:
            with self.get_session() as session:
                # Test basic connectivity
                session.execute(text("SELECT 1"))
                
                # Get basic statistics
                stats = {
                    "status": "healthy",
                    "database_type": self.config.db_type,
                    "connection_pool_size": self.config.pool_size if self.config.db_type == "postgresql" else "N/A",
                    "last_check": datetime.utcnow().isoformat()
                }
                
                # Add table counts if possible
                try:
                    if hasattr(self, 'execution_history_table'):
                        result = session.execute(text(f"SELECT COUNT(*) FROM {self.execution_history_table.name}"))
                        stats["execution_history_count"] = result.scalar()
                except Exception:
                    pass  # Ignore if tables don't exist yet
                
                return stats
                
        except Exception as e:
            log_error(logger, f"Database health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "database_type": self.config.db_type,
                "last_check": datetime.utcnow().isoformat()
            }
    
    def backup_database(self, backup_path: Optional[str] = None) -> bool:
        """
        Create database backup (SQLite only)
        
        Args:
            backup_path: Optional custom backup path
            
        Returns:
            bool: True if backup successful, False otherwise
        """
        if self.config.db_type != "sqlite":
            log_warning(logger, "Database backup only supported for SQLite")
            return False
            
        try:
            import shutil
            
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{self.config.sqlite_path}.backup.{timestamp}"
            
            shutil.copy2(self.config.sqlite_path, backup_path)
            log_info(logger, f"Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            log_error(logger, f"Database backup failed: {str(e)}")
            return False
    
    # Execution History Methods
    def save_execution_record(self, execution_data: Dict[str, Any]) -> bool:
        """Save execution record to database"""
        try:
            with self.get_session() as session:
                # Check if record already exists
                existing = session.execute(
                    self.execution_history_table.select().where(
                        self.execution_history_table.c.id == execution_data['id']
                    )
                ).first()
                
                if existing:
                    # Update existing record
                    session.execute(
                        self.execution_history_table.update().where(
                            self.execution_history_table.c.id == execution_data['id']
                        ).values(**execution_data)
                    )
                    log_info(logger, f"Updated existing execution record: {execution_data.get('id')}")
                else:
                    # Insert new record
                    session.execute(
                        self.execution_history_table.insert().values(**execution_data)
                    )
                    log_info(logger, f"Saved new execution record: {execution_data.get('id')}")
                
                session.commit()
                return True
        except Exception as e:
            log_error(logger, f"Failed to save execution record {execution_data.get('id', 'unknown')}: {str(e)}")
            # Log more details about the error
            if "UNIQUE constraint failed" in str(e):
                log_error(logger, f"Duplicate execution ID detected: {execution_data.get('id')}")
            return False
    
    def get_execution_history(self, limit: int = 100) -> list:
        """Get execution history from database"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    self.execution_history_table.select()
                    .order_by(self.execution_history_table.c.started_at.desc())
                    .limit(limit)
                )
                return [dict(row._mapping) for row in result]
        except Exception as e:
            log_error(logger, f"Failed to get execution history: {str(e)}")
            return []
    
    # Evaluation History Methods
    def save_evaluation_result(self, evaluation_data: Dict[str, Any]) -> bool:
        """Save evaluation result to database"""
        try:
            with self.get_session() as session:
                session.execute(
                    self.evaluation_history_table.insert().values(**evaluation_data)
                )
                session.commit()
                log_info(logger, f"Saved evaluation result for execution: {evaluation_data.get('execution_id')}")
                return True
        except Exception as e:
            log_error(logger, f"Failed to save evaluation result: {str(e)}")
            return False
    
    def get_evaluation_history(self, limit: int = 100) -> list:
        """Get evaluation history from database"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    self.evaluation_history_table.select()
                    .order_by(self.evaluation_history_table.c.timestamp.desc())
                    .limit(limit)
                )
                return [dict(row._mapping) for row in result]
        except Exception as e:
            log_error(logger, f"Failed to get evaluation history: {str(e)}")
            return []
    
    def get_evaluation_metrics(self) -> Dict[str, Any]:
        """Get aggregated evaluation metrics"""
        try:
            with self.get_session() as session:
                # Get average quality score
                avg_score_result = session.execute(
                    text(f"SELECT AVG(quality_score) as avg_score FROM {self.evaluation_history_table.name}")
                )
                avg_score = avg_score_result.scalar() or 0
                
                # Get count by channel
                channel_counts = session.execute(
                    text(f"SELECT channel, COUNT(*) as count FROM {self.evaluation_history_table.name} GROUP BY channel")
                )
                
                # Get recent evaluations
                recent_evals = session.execute(
                    self.evaluation_history_table.select()
                    .order_by(self.evaluation_history_table.c.timestamp.desc())
                    .limit(10)
                )
                
                return {
                    "average_quality_score": float(avg_score),
                    "total_evaluations": session.execute(text(f"SELECT COUNT(*) FROM {self.evaluation_history_table.name}")).scalar(),
                    "channel_distribution": {row.channel: row.count for row in channel_counts},
                    "recent_evaluations": [dict(row._mapping) for row in recent_evals]
                }
        except Exception as e:
            log_error(logger, f"Failed to get evaluation metrics: {str(e)}")
            return {
                "average_quality_score": 0,
                "total_evaluations": 0,
                "channel_distribution": {},
                "recent_evaluations": []
            }
    
    # Observability Metrics Methods
    def save_observability_metrics(self, metrics_data: Dict[str, Any]) -> bool:
        """Save observability metrics to database"""
        try:
            with self.get_session() as session:
                session.execute(
                    self.observability_metrics_table.insert().values(**metrics_data)
                )
                session.commit()
                log_info(logger, f"Saved observability metrics for execution: {metrics_data.get('execution_id')}")
                return True
        except Exception as e:
            log_error(logger, f"Failed to save observability metrics: {str(e)}")
            return False
    
    def get_observability_history(self, limit: int = 100) -> list:
        """Get observability history from database"""
        try:
            with self.get_session() as session:
                result = session.execute(
                    self.observability_metrics_table.select()
                    .order_by(self.observability_metrics_table.c.timestamp.desc())
                    .limit(limit)
                )
                return [dict(row._mapping) for row in result]
        except Exception as e:
            log_error(logger, f"Failed to get observability history: {str(e)}")
            return []
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get aggregated performance metrics"""
        try:
            with self.get_session() as session:
                # Get average duration
                avg_duration_result = session.execute(
                    text(f"SELECT AVG(duration_ms) as avg_duration FROM {self.observability_metrics_table.name}")
                )
                avg_duration = avg_duration_result.scalar() or 0
                
                # Get cache hit rate
                cache_stats = session.execute(
                    text(f"SELECT SUM(cache_hits) as hits, SUM(cache_misses) as misses FROM {self.observability_metrics_table.name}")
                ).first()
                
                cache_hit_rate = 0
                if cache_stats and cache_stats.hits and cache_stats.misses:
                    total_requests = cache_stats.hits + cache_stats.misses
                    cache_hit_rate = cache_stats.hits / total_requests if total_requests > 0 else 0
                
                # Get error rate
                error_stats = session.execute(
                    text(f"SELECT COUNT(*) as total, SUM(CASE WHEN error_count > 0 THEN 1 ELSE 0 END) as errors FROM {self.observability_metrics_table.name}")
                ).first()
                
                error_rate = 0
                if error_stats and error_stats.total > 0:
                    error_rate = error_stats.errors / error_stats.total
                
                return {
                    "average_duration_ms": float(avg_duration),
                    "cache_hit_rate": float(cache_hit_rate),
                    "error_rate": float(error_rate),
                    "total_executions": error_stats.total if error_stats else 0
                }
        except Exception as e:
            log_error(logger, f"Failed to get performance metrics: {str(e)}")
            return {
                "average_duration_ms": 0,
                "cache_hit_rate": 0,
                "error_rate": 0,
                "total_executions": 0
            }


# Global database manager instance
db_manager = None

def get_database_manager() -> DatabaseManager:
    """
    Get global database manager instance
    
    Returns:
        DatabaseManager: Database manager instance
    """
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def get_db_session():
    """
    FastAPI dependency for getting database session
    
    Yields:
        Session: Database session
    """
    manager = get_database_manager()
    with manager.get_session() as session:
        yield session