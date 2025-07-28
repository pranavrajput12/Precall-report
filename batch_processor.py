"""
Batch Processing Module

This module handles bulk workflow operations, allowing users to process
multiple workflow inputs simultaneously with advanced queuing, progress tracking,
and result aggregation capabilities.
"""

import asyncio
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from workflow_executor import workflow_executor
from database import get_database_manager
from sqlalchemy import text
from logging_config import log_info, log_warning, log_debug, log_error
from config_system import config_system
from cache import cache_result
from input_validator import validate_workflow_inputs
from context_enricher import enrich_workflow_context

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


class BatchStatus(Enum):
    """Batch processing status"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class JobStatus(Enum):
    """Individual job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class BatchJob:
    """Individual job within a batch"""
    id: str
    batch_id: str
    input_data: Dict[str, Any]
    workflow_id: str
    status: JobStatus = JobStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: float = 0.0
    retry_count: int = 0
    priority: int = 0  # Higher numbers = higher priority


@dataclass
class BatchProcessingConfig:
    """Configuration for batch processing"""
    max_concurrent_jobs: int = 3
    max_retries: int = 2
    retry_delay: float = 5.0  # seconds
    timeout_per_job: float = 300.0  # 5 minutes
    enable_validation: bool = True
    enable_enrichment: bool = True
    save_intermediate_results: bool = True
    chunk_size: int = 100  # For very large batches
    priority_processing: bool = True


@dataclass 
class BatchResult:
    """Result of batch processing"""
    batch_id: str
    total_jobs: int
    completed_jobs: int
    failed_jobs: int
    skipped_jobs: int
    started_at: datetime
    completed_at: Optional[datetime]
    total_execution_time: float
    average_job_time: float
    success_rate: float
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    summary: Dict[str, Any]


class BatchProcessor:
    """Advanced batch processing engine"""
    
    def __init__(self):
        self.db_manager = DatabaseAdapter()
        self.config = self._load_config()
        self.active_batches: Dict[str, Dict[str, Any]] = {}
        self.job_queues: Dict[str, List[BatchJob]] = defaultdict(list)
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_jobs)
        self._lock = threading.Lock()
        
        # Initialize database tables
        self._init_database()
        
        # Load active batches from database
        self._load_active_batches()
    
    def _load_config(self) -> BatchProcessingConfig:
        """Load batch processing configuration"""
        batch_config = config_system.get("batch_processing", {})
        
        return BatchProcessingConfig(
            max_concurrent_jobs=batch_config.get("max_concurrent_jobs", 3),
            max_retries=batch_config.get("max_retries", 2),
            retry_delay=batch_config.get("retry_delay", 5.0),
            timeout_per_job=batch_config.get("timeout_per_job", 300.0),
            enable_validation=batch_config.get("enable_validation", True),
            enable_enrichment=batch_config.get("enable_enrichment", True),
            save_intermediate_results=batch_config.get("save_intermediate_results", True),
            chunk_size=batch_config.get("chunk_size", 100),
            priority_processing=batch_config.get("priority_processing", True)
        )
    
    def _init_database(self):
        """Initialize batch processing database tables"""
        try:
            # Batch metadata table
            self.db_manager.execute("""
                CREATE TABLE IF NOT EXISTS batch_processing (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    workflow_id TEXT,
                    status TEXT,
                    total_jobs INTEGER,
                    completed_jobs INTEGER DEFAULT 0,
                    failed_jobs INTEGER DEFAULT 0,
                    skipped_jobs INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    started_at DATETIME,
                    completed_at DATETIME,
                    config TEXT,
                    metadata TEXT
                )
            """)
            
            # Individual jobs table
            self.db_manager.execute("""
                CREATE TABLE IF NOT EXISTS batch_jobs (
                    id TEXT PRIMARY KEY,
                    batch_id TEXT,
                    workflow_id TEXT,
                    input_data TEXT,
                    status TEXT,
                    result TEXT,
                    error_message TEXT,
                    started_at DATETIME,
                    completed_at DATETIME,
                    execution_time REAL DEFAULT 0,
                    retry_count INTEGER DEFAULT 0,
                    priority INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (batch_id) REFERENCES batch_processing (id)
                )
            """)
            
            # Batch progress tracking
            self.db_manager.execute("""
                CREATE TABLE IF NOT EXISTS batch_progress (
                    batch_id TEXT PRIMARY KEY,
                    current_job_id TEXT,
                    progress_percentage REAL,
                    estimated_completion DATETIME,
                    average_job_time REAL,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (batch_id) REFERENCES batch_processing (id)
                )
            """)
            
            # Create indexes for performance
            self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_batch_jobs_batch_id 
                ON batch_jobs(batch_id)
            """)
            
            self.db_manager.execute("""
                CREATE INDEX IF NOT EXISTS idx_batch_jobs_status 
                ON batch_jobs(status)
            """)
            
            log_info(logger, "Batch processing database initialized")
            
        except Exception as e:
            log_error(logger, f"Failed to initialize batch processing database: {e}")
    
    def _load_active_batches(self):
        """Load active batches from database on startup"""
        try:
            active_batches = self.db_manager.fetch_all("""
                SELECT * FROM batch_processing 
                WHERE status IN ('pending', 'running', 'paused')
            """)
            
            for batch_row in active_batches:
                batch_id = batch_row['id']
                self.active_batches[batch_id] = {
                    'id': batch_id,
                    'name': batch_row['name'],
                    'status': BatchStatus(batch_row['status']),
                    'workflow_id': batch_row['workflow_id'],
                    'total_jobs': batch_row['total_jobs'],
                    'completed_jobs': batch_row['completed_jobs'],
                    'failed_jobs': batch_row['failed_jobs'],
                    'config': json.loads(batch_row['config']) if batch_row['config'] else {},
                    'metadata': json.loads(batch_row['metadata']) if batch_row['metadata'] else {}
                }
                
                # Load jobs for this batch
                jobs = self._load_batch_jobs(batch_id)
                self.job_queues[batch_id] = jobs
                
            log_info(logger, f"Loaded {len(active_batches)} active batches")
            
        except Exception as e:
            log_error(logger, f"Failed to load active batches: {e}")
    
    def _load_batch_jobs(self, batch_id: str) -> List[BatchJob]:
        """Load jobs for a specific batch"""
        try:
            job_rows = self.db_manager.fetch_all("""
                SELECT * FROM batch_jobs 
                WHERE batch_id = ? 
                ORDER BY priority DESC, created_at ASC
            """, (batch_id,))
            
            jobs = []
            for row in job_rows:
                job = BatchJob(
                    id=row['id'],
                    batch_id=row['batch_id'],
                    workflow_id=row['workflow_id'],
                    input_data=json.loads(row['input_data']),
                    status=JobStatus(row['status']),
                    result=json.loads(row['result']) if row['result'] else None,
                    error_message=row['error_message'],
                    started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
                    completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
                    execution_time=row['execution_time'],
                    retry_count=row['retry_count'],
                    priority=row['priority']
                )
                jobs.append(job)
            
            return jobs
            
        except Exception as e:
            log_error(logger, f"Failed to load jobs for batch {batch_id}: {e}")
            return []
    
    async def create_batch(self, 
                          name: str,
                          workflow_id: str, 
                          input_list: List[Dict[str, Any]], 
                          config_override: Optional[Dict[str, Any]] = None,
                          priority_map: Optional[Dict[int, int]] = None) -> str:
        """
        Create a new batch processing job
        
        Args:
            name: Human-readable name for the batch
            workflow_id: ID of the workflow to execute
            input_list: List of input dictionaries for each job
            config_override: Override default batch processing config
            priority_map: Map job indices to priority levels
            
        Returns:
            batch_id: Unique identifier for the batch
        """
        batch_id = str(uuid.uuid4())
        
        try:
            # Merge configuration
            config = asdict(self.config)
            if config_override:
                config.update(config_override)
            
            # Create batch jobs
            jobs = []
            for i, input_data in enumerate(input_list):
                job_id = f"{batch_id}_{i:04d}"
                priority = priority_map.get(i, 0) if priority_map else 0
                
                job = BatchJob(
                    id=job_id,
                    batch_id=batch_id,
                    input_data=input_data,
                    workflow_id=workflow_id,
                    priority=priority
                )
                jobs.append(job)
            
            # Save batch to database
            self.db_manager.execute("""
                INSERT INTO batch_processing 
                (id, name, workflow_id, status, total_jobs, config, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                batch_id, name, workflow_id, BatchStatus.PENDING.value,
                len(jobs), json.dumps(config), json.dumps({
                    'created_by': 'batch_processor',
                    'input_count': len(input_list)
                })
            ))
            
            # Save jobs to database
            for job in jobs:
                self.db_manager.execute("""
                    INSERT INTO batch_jobs 
                    (id, batch_id, workflow_id, input_data, status, priority)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    job.id, job.batch_id, job.workflow_id,
                    json.dumps(job.input_data), job.status.value, job.priority
                ))
            
            # Store in memory
            with self._lock:
                self.active_batches[batch_id] = {
                    'id': batch_id,
                    'name': name,
                    'status': BatchStatus.PENDING,
                    'workflow_id': workflow_id,
                    'total_jobs': len(jobs),
                    'completed_jobs': 0,
                    'failed_jobs': 0,
                    'config': config,
                    'metadata': {'created_by': 'batch_processor'}
                }
                self.job_queues[batch_id] = jobs
            
            log_info(logger, f"Created batch {batch_id} with {len(jobs)} jobs")
            return batch_id
            
        except Exception as e:
            log_error(logger, f"Failed to create batch: {e}")
            raise
    
    async def start_batch(self, batch_id: str) -> bool:
        """
        Start processing a batch
        
        Args:
            batch_id: ID of the batch to start
            
        Returns:
            bool: True if batch started successfully
        """
        if batch_id not in self.active_batches:
            raise ValueError(f"Batch {batch_id} not found")
        
        try:
            # Update batch status
            self._update_batch_status(batch_id, BatchStatus.RUNNING)
            
            # Start processing asynchronously
            asyncio.create_task(self._process_batch(batch_id))
            
            log_info(logger, f"Started batch processing for {batch_id}")
            return True
            
        except Exception as e:
            log_error(logger, f"Failed to start batch {batch_id}: {e}")
            return False
    
    async def _process_batch(self, batch_id: str):
        """Process all jobs in a batch"""
        start_time = time.time()
        
        try:
            batch_info = self.active_batches[batch_id]
            jobs = self.job_queues[batch_id]
            config = BatchProcessingConfig(**batch_info['config'])
            
            # Sort jobs by priority if enabled
            if config.priority_processing:
                jobs.sort(key=lambda x: (-x.priority, x.id))
            
            # Process jobs in chunks for memory efficiency
            chunk_size = min(config.chunk_size, len(jobs))
            completed_jobs = 0
            failed_jobs = 0
            
            # Update batch start time
            self.db_manager.execute("""
                UPDATE batch_processing 
                SET started_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (batch_id,))
            
            # Process jobs concurrently
            semaphore = asyncio.Semaphore(config.max_concurrent_jobs)
            
            async def process_job_with_semaphore(job):
                async with semaphore:
                    return await self._process_single_job(job, config)
            
            # Create tasks for all jobs
            tasks = [process_job_with_semaphore(job) for job in jobs if job.status == JobStatus.PENDING]
            
            # Process tasks as they complete
            for completed_task in asyncio.as_completed(tasks):
                try:
                    job_result = await completed_task
                    
                    if job_result['status'] == JobStatus.COMPLETED:
                        completed_jobs += 1
                    elif job_result['status'] == JobStatus.FAILED:
                        failed_jobs += 1
                    
                    # Update progress
                    total_processed = completed_jobs + failed_jobs
                    progress = (total_processed / len(jobs)) * 100
                    
                    self._update_batch_progress(batch_id, progress, job_result['job_id'])
                    
                    log_debug(logger, f"Batch {batch_id}: {total_processed}/{len(jobs)} jobs completed")
                    
                except Exception as e:
                    log_error(logger, f"Error processing job in batch {batch_id}: {e}")
                    failed_jobs += 1
            
            # Calculate final statistics
            execution_time = time.time() - start_time
            success_rate = (completed_jobs / len(jobs)) * 100 if jobs else 0
            
            # Update batch completion
            self.db_manager.execute("""
                UPDATE batch_processing 
                SET status = ?, completed_jobs = ?, failed_jobs = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (BatchStatus.COMPLETED.value, completed_jobs, failed_jobs, batch_id))
            
            # Update in-memory state
            with self._lock:
                self.active_batches[batch_id]['status'] = BatchStatus.COMPLETED
                self.active_batches[batch_id]['completed_jobs'] = completed_jobs
                self.active_batches[batch_id]['failed_jobs'] = failed_jobs
            
            log_info(logger, 
                    f"Batch {batch_id} completed: {completed_jobs} successful, "
                    f"{failed_jobs} failed, {success_rate:.1f}% success rate, "
                    f"execution time: {execution_time:.2f}s")
            
        except Exception as e:
            log_error(logger, f"Batch processing failed for {batch_id}: {e}")
            self._update_batch_status(batch_id, BatchStatus.FAILED)
    
    async def _process_single_job(self, job: BatchJob, config: BatchProcessingConfig) -> Dict[str, Any]:
        """Process a single job within a batch"""
        job.started_at = datetime.now()
        job.status = JobStatus.RUNNING
        
        # Update job status in database
        self._update_job_status(job)
        
        try:
            # Apply validation if enabled
            if config.enable_validation:
                validation_result = await validate_workflow_inputs(job.input_data)
                if not validation_result.get('is_valid', True):
                    raise ValueError(f"Validation failed: {validation_result.get('errors', [])}")
            
            # Apply context enrichment if enabled
            enriched_data = job.input_data
            if config.enable_enrichment:
                enriched_result = await enrich_workflow_context(job.input_data)
                enriched_data = enriched_result
            
            # Execute workflow with timeout
            start_time = time.time()
            
            try:
                # Run workflow with timeout
                result = await asyncio.wait_for(
                    workflow_executor.run_full_workflow(job.workflow_id, enriched_data),
                    timeout=config.timeout_per_job
                )
                
                job.execution_time = time.time() - start_time
                job.result = result
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                
                log_debug(logger, f"Job {job.id} completed successfully in {job.execution_time:.2f}s")
                
            except asyncio.TimeoutError:
                raise Exception(f"Job timed out after {config.timeout_per_job}s")
            
        except Exception as e:
            job.execution_time = time.time() - job.started_at.timestamp()
            job.error_message = str(e)
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now()
            
            # Retry logic
            if job.retry_count < config.max_retries:
                job.retry_count += 1
                job.status = JobStatus.RETRYING
                
                log_warning(logger, f"Job {job.id} failed, retrying ({job.retry_count}/{config.max_retries}): {e}")
                
                # Wait before retry
                await asyncio.sleep(config.retry_delay)
                
                # Retry the job
                return await self._process_single_job(job, config)
            else:
                log_error(logger, f"Job {job.id} failed after {config.max_retries} retries: {e}")
        
        # Update job in database
        self._update_job_status(job)
        
        return {
            'job_id': job.id,
            'status': job.status,
            'execution_time': job.execution_time,
            'result': job.result,
            'error': job.error_message
        }
    
    def _update_batch_status(self, batch_id: str, status: BatchStatus):
        """Update batch status in database and memory"""
        try:
            self.db_manager.execute("""
                UPDATE batch_processing SET status = ? WHERE id = ?
            """, (status.value, batch_id))
            
            with self._lock:
                if batch_id in self.active_batches:
                    self.active_batches[batch_id]['status'] = status
                    
        except Exception as e:
            log_error(logger, f"Failed to update batch status: {e}")
    
    def _update_job_status(self, job: BatchJob):
        """Update job status in database"""
        try:
            self.db_manager.execute("""
                UPDATE batch_jobs 
                SET status = ?, result = ?, error_message = ?, 
                    started_at = ?, completed_at = ?, execution_time = ?, retry_count = ?
                WHERE id = ?
            """, (
                job.status.value,
                json.dumps(job.result) if job.result else None,
                job.error_message,
                job.started_at.isoformat() if job.started_at else None,
                job.completed_at.isoformat() if job.completed_at else None,
                job.execution_time,
                job.retry_count,
                job.id
            ))
        except Exception as e:
            log_error(logger, f"Failed to update job status: {e}")
    
    def _update_batch_progress(self, batch_id: str, progress: float, current_job_id: str):
        """Update batch progress tracking"""
        try:
            # Calculate estimated completion time
            batch_info = self.active_batches.get(batch_id, {})
            jobs = self.job_queues.get(batch_id, [])
            
            completed_jobs = sum(1 for job in jobs if job.status == JobStatus.COMPLETED)
            if completed_jobs > 0:
                avg_job_time = sum(job.execution_time for job in jobs if job.status == JobStatus.COMPLETED) / completed_jobs
                remaining_jobs = batch_info.get('total_jobs', 0) - completed_jobs
                estimated_completion = datetime.now() + timedelta(seconds=avg_job_time * remaining_jobs)
            else:
                avg_job_time = 0
                estimated_completion = None
            
            # Update database
            self.db_manager.execute("""
                INSERT OR REPLACE INTO batch_progress 
                (batch_id, current_job_id, progress_percentage, estimated_completion, average_job_time, last_updated)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                batch_id, current_job_id, progress,
                estimated_completion.isoformat() if estimated_completion else None,
                avg_job_time
            ))
            
        except Exception as e:
            log_error(logger, f"Failed to update batch progress: {e}")
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a batch"""
        try:
            batch_row = self.db_manager.fetch_one("""
                SELECT bp.*, pr.progress_percentage, pr.estimated_completion, pr.average_job_time
                FROM batch_processing bp
                LEFT JOIN batch_progress pr ON bp.id = pr.batch_id
                WHERE bp.id = ?
            """, (batch_id,))
            
            if not batch_row:
                return None
            
            # Get job statistics
            job_stats = self.db_manager.fetch_one("""
                SELECT 
                    COUNT(*) as total_jobs,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_jobs,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_jobs,
                    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running_jobs,
                    AVG(execution_time) as avg_execution_time
                FROM batch_jobs 
                WHERE batch_id = ?
            """, (batch_id,))
            
            return {
                'batch_id': batch_id,
                'name': batch_row['name'],
                'workflow_id': batch_row['workflow_id'],
                'status': batch_row['status'],
                'total_jobs': job_stats['total_jobs'],
                'completed_jobs': job_stats['completed_jobs'],
                'failed_jobs': job_stats['failed_jobs'],
                'running_jobs': job_stats['running_jobs'],
                'progress_percentage': batch_row['progress_percentage'] or 0,
                'average_execution_time': job_stats['avg_execution_time'] or 0,
                'estimated_completion': batch_row['estimated_completion'],
                'created_at': batch_row['created_at'],
                'started_at': batch_row['started_at'],
                'completed_at': batch_row['completed_at']
            }
            
        except Exception as e:
            log_error(logger, f"Failed to get batch status: {e}")
            return None
    
    def get_batch_results(self, batch_id: str, include_details: bool = False) -> Optional[BatchResult]:
        """Get detailed results of a completed batch"""
        try:
            # Get batch info
            batch_info = self.get_batch_status(batch_id)
            if not batch_info:
                return None
            
            # Get all job results
            jobs = self.db_manager.fetch_all("""
                SELECT * FROM batch_jobs 
                WHERE batch_id = ? 
                ORDER BY created_at
            """, (batch_id,))
            
            results = []
            errors = []
            
            for job_row in jobs:
                job_data = {
                    'job_id': job_row['id'],
                    'status': job_row['status'],
                    'execution_time': job_row['execution_time'],
                    'retry_count': job_row['retry_count']
                }
                
                if include_details:
                    job_data['input_data'] = json.loads(job_row['input_data'])
                    job_data['result'] = json.loads(job_row['result']) if job_row['result'] else None
                
                if job_row['status'] == 'completed':
                    results.append(job_data)
                elif job_row['status'] == 'failed':
                    job_data['error_message'] = job_row['error_message']
                    errors.append(job_data)
            
            # Calculate statistics
            total_jobs = len(jobs)
            completed = len([j for j in jobs if j['status'] == 'completed'])
            failed = len([j for j in jobs if j['status'] == 'failed'])
            skipped = len([j for j in jobs if j['status'] == 'skipped'])
            
            total_time = sum(j['execution_time'] or 0 for j in jobs)
            avg_time = total_time / completed if completed > 0 else 0
            success_rate = (completed / total_jobs) * 100 if total_jobs > 0 else 0
            
            return BatchResult(
                batch_id=batch_id,
                total_jobs=total_jobs,
                completed_jobs=completed,
                failed_jobs=failed,
                skipped_jobs=skipped,
                started_at=datetime.fromisoformat(batch_info['started_at']) if batch_info['started_at'] else datetime.now(),
                completed_at=datetime.fromisoformat(batch_info['completed_at']) if batch_info['completed_at'] else None,
                total_execution_time=total_time,
                average_job_time=avg_time,
                success_rate=success_rate,
                results=results,
                errors=errors,
                summary={
                    'name': batch_info['name'],
                    'workflow_id': batch_info['workflow_id'],
                    'fastest_job': min((j['execution_time'] for j in jobs if j['execution_time']), default=0),
                    'slowest_job': max((j['execution_time'] for j in jobs if j['execution_time']), default=0),
                    'retry_rate': (sum(j['retry_count'] for j in jobs) / total_jobs) if total_jobs > 0 else 0
                }
            )
            
        except Exception as e:
            log_error(logger, f"Failed to get batch results: {e}")
            return None
    
    def list_batches(self, status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """List all batches with optional status filtering"""
        try:
            query = """
                SELECT bp.*, pr.progress_percentage
                FROM batch_processing bp
                LEFT JOIN batch_progress pr ON bp.id = pr.batch_id
            """
            params = []
            
            if status_filter:
                query += " WHERE bp.status = ?"
                params.append(status_filter)
            
            query += " ORDER BY bp.created_at DESC LIMIT ?"
            params.append(limit)
            
            batches = self.db_manager.fetch_all(query, params)
            
            return [{
                'batch_id': row['id'],
                'name': row['name'],
                'workflow_id': row['workflow_id'],
                'status': row['status'],
                'total_jobs': row['total_jobs'],
                'completed_jobs': row['completed_jobs'],
                'failed_jobs': row['failed_jobs'],
                'progress_percentage': row['progress_percentage'] or 0,
                'created_at': row['created_at'],
                'started_at': row['started_at'],
                'completed_at': row['completed_at']
            } for row in batches]
            
        except Exception as e:
            log_error(logger, f"Failed to list batches: {e}")
            return []
    
    async def cancel_batch(self, batch_id: str) -> bool:
        """Cancel a running batch"""
        try:
            if batch_id not in self.active_batches:
                return False
            
            self._update_batch_status(batch_id, BatchStatus.CANCELLED)
            
            # Cancel pending jobs
            self.db_manager.execute("""
                UPDATE batch_jobs 
                SET status = 'skipped' 
                WHERE batch_id = ? AND status = 'pending'
            """, (batch_id,))
            
            log_info(logger, f"Cancelled batch {batch_id}")
            return True
            
        except Exception as e:
            log_error(logger, f"Failed to cancel batch {batch_id}: {e}")
            return False
    
    def cleanup_old_batches(self, days_old: int = 30):
        """Clean up old batch data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # Get old batches
            old_batches = self.db_manager.fetch_all("""
                SELECT id FROM batch_processing 
                WHERE created_at < ? AND status IN ('completed', 'failed', 'cancelled')
            """, (cutoff_date.isoformat(),))
            
            for batch_row in old_batches:
                batch_id = batch_row['id']
                
                # Delete jobs
                self.db_manager.execute("DELETE FROM batch_jobs WHERE batch_id = ?", (batch_id,))
                
                # Delete progress
                self.db_manager.execute("DELETE FROM batch_progress WHERE batch_id = ?", (batch_id,))
                
                # Delete batch
                self.db_manager.execute("DELETE FROM batch_processing WHERE id = ?", (batch_id,))
                
                # Remove from memory
                with self._lock:
                    if batch_id in self.active_batches:
                        del self.active_batches[batch_id]
                    if batch_id in self.job_queues:
                        del self.job_queues[batch_id]
            
            log_info(logger, f"Cleaned up {len(old_batches)} old batches")
            
        except Exception as e:
            log_error(logger, f"Failed to cleanup old batches: {e}")


# Create singleton instance
batch_processor = BatchProcessor()


# Convenience functions for external use
async def create_batch(name: str, workflow_id: str, input_list: List[Dict[str, Any]], 
                      config_override: Optional[Dict[str, Any]] = None) -> str:
    """Create a new batch processing job"""
    return await batch_processor.create_batch(name, workflow_id, input_list, config_override)


async def start_batch(batch_id: str) -> bool:
    """Start processing a batch"""
    return await batch_processor.start_batch(batch_id)


def get_batch_status(batch_id: str) -> Optional[Dict[str, Any]]:
    """Get current status of a batch"""
    return batch_processor.get_batch_status(batch_id)


def get_batch_results(batch_id: str, include_details: bool = False) -> Optional[BatchResult]:
    """Get detailed results of a completed batch"""
    return batch_processor.get_batch_results(batch_id, include_details)


def list_batches(status_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """List all batches with optional status filtering"""
    return batch_processor.list_batches(status_filter, limit)


async def cancel_batch(batch_id: str) -> bool:
    """Cancel a running batch"""
    return await batch_processor.cancel_batch(batch_id)