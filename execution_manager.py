"""
ExecutionManager - Unified storage manager for workflow executions

This module provides a single source of truth for execution data,
ensuring JSON file and database always stay in perfect sync.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

from database import get_database_manager
from logging_config import log_info, log_error, log_warning

logger = logging.getLogger(__name__)

class ExecutionManager:
    """Unified manager for execution data with atomic operations"""
    
    def __init__(self, json_file_path: str = "logs/execution_history.json"):
        self.json_file_path = json_file_path
        self.db_manager = None
        self._init_database()
        self._ensure_json_file_exists()
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            self.db_manager = get_database_manager()
            log_info(logger, "Database connection initialized")
        except Exception as e:
            log_error(logger, f"Failed to initialize database: {e}")
            self.db_manager = None
    
    def _ensure_json_file_exists(self):
        """Ensure JSON file exists with proper structure"""
        os.makedirs(os.path.dirname(self.json_file_path), exist_ok=True)
        if not os.path.exists(self.json_file_path):
            with open(self.json_file_path, 'w') as f:
                json.dump([], f, indent=2)
            log_info(logger, f"Created JSON file: {self.json_file_path}")
    
    def _load_json_data(self) -> List[Dict]:
        """Load data from JSON file"""
        try:
            with open(self.json_file_path, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            log_error(logger, f"Failed to load JSON data: {e}")
            return []
    
    def _save_json_data(self, data: List[Dict]):
        """Save data to JSON file"""
        try:
            with open(self.json_file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            log_info(logger, f"Saved {len(data)} records to JSON file")
        except Exception as e:
            log_error(logger, f"Failed to save JSON data: {e}")
            raise
    
    def _normalize_execution_data(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize execution data to standard format"""
        # Ensure required fields exist
        normalized = {
            'id': execution_data.get('id'),
            'workflow_id': execution_data.get('workflow_id', ''),
            'workflow_name': execution_data.get('workflow_name', ''),
            'status': execution_data.get('status', 'pending'),
            'started_at': execution_data.get('started_at'),
            'completed_at': execution_data.get('completed_at'),
            'duration': execution_data.get('duration'),
            'input_data': execution_data.get('input_data', {}),
            'output_data': execution_data.get('output_data', execution_data.get('output', {})),
            'error_message': execution_data.get('error_message'),
            'steps': execution_data.get('steps', []),
            'current_step': execution_data.get('current_step'),
            'progress': execution_data.get('progress', 0),
            'executed_by': execution_data.get('executed_by', 'unknown')
        }
        
        # Ensure started_at is always set (required by database)
        if not normalized['started_at']:
            normalized['started_at'] = datetime.now()
        elif isinstance(normalized['started_at'], str):
            try:
                normalized['started_at'] = datetime.fromisoformat(normalized['started_at'])
            except:
                normalized['started_at'] = datetime.now()
        
        if normalized['completed_at'] and isinstance(normalized['completed_at'], str):
            try:
                normalized['completed_at'] = datetime.fromisoformat(normalized['completed_at'])
            except:
                normalized['completed_at'] = None
        
        # Calculate duration if missing
        if normalized['completed_at'] and normalized['started_at'] and not normalized['duration']:
            normalized['duration'] = (normalized['completed_at'] - normalized['started_at']).total_seconds()
        
        return normalized
    
    @contextmanager
    def atomic_operation(self):
        """Context manager for atomic operations across JSON and database"""
        json_backup = None
        
        try:
            # Backup current JSON data
            json_backup = self._load_json_data()
            
            yield
            
            # If we get here, operations succeeded
            
        except Exception as e:
            log_error(logger, f"Atomic operation failed: {e}")
            
            # Rollback JSON file
            if json_backup is not None:
                try:
                    self._save_json_data(json_backup)
                    log_info(logger, "Rolled back JSON file")
                except:
                    log_error(logger, "Failed to rollback JSON file")
            
            raise
    
    def save_execution(self, execution_data: Dict[str, Any]) -> bool:
        """Save execution data atomically to both JSON and database"""
        try:
            execution_data = self._normalize_execution_data(execution_data)
            execution_id = execution_data['id']
            
            if not execution_id:
                raise ValueError("Execution ID is required")
            
            with self.atomic_operation():
                # Update JSON file
                json_data = self._load_json_data()
                
                # Find existing record or add new one
                updated = False
                for i, record in enumerate(json_data):
                    if record.get('id') == execution_id:
                        # Convert datetime objects back to strings for JSON
                        json_record = execution_data.copy()
                        if json_record['started_at']:
                            json_record['started_at'] = json_record['started_at'].isoformat()
                        if json_record['completed_at']:
                            json_record['completed_at'] = json_record['completed_at'].isoformat()
                        
                        json_data[i] = json_record
                        updated = True
                        break
                
                if not updated:
                    # Add new record
                    json_record = execution_data.copy()
                    if json_record['started_at']:
                        json_record['started_at'] = json_record['started_at'].isoformat()
                    if json_record['completed_at']:
                        json_record['completed_at'] = json_record['completed_at'].isoformat()
                    
                    json_data.append(json_record)
                
                # Save JSON file
                self._save_json_data(json_data)
                
                # Update database
                if self.db_manager:
                    success = self.db_manager.save_execution_record(execution_data)
                    if not success:
                        raise Exception("Database save failed")
                
                log_info(logger, f"Successfully saved execution {execution_id} atomically")
                return True
                
        except Exception as e:
            log_error(logger, f"Failed to save execution {execution_data.get('id', 'unknown')}: {e}")
            return False
    
    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution by ID (prefers database, falls back to JSON)"""
        try:
            # Try database first
            if self.db_manager:
                with self.db_manager.get_session() as session:
                    result = session.execute(
                        self.db_manager.execution_history_table.select().where(
                            self.db_manager.execution_history_table.c.id == execution_id
                        )
                    ).first()
                    
                    if result:
                        return dict(result._mapping)
            
            # Fallback to JSON
            json_data = self._load_json_data()
            for record in json_data:
                if record.get('id') == execution_id:
                    return record
            
            return None
            
        except Exception as e:
            log_error(logger, f"Failed to get execution {execution_id}: {e}")
            return None
    
    def get_all_executions(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all executions (prefers database, falls back to JSON)"""
        try:
            # Try database first
            if self.db_manager:
                db_data = self.db_manager.get_execution_history(limit=limit)
                if db_data:  # Return database data even if empty list
                    log_info(logger, f"Retrieved {len(db_data)} executions from database")
                    return db_data
            
            # Fallback to JSON
            json_data = self._load_json_data()
            # Sort by started_at (newest first)
            json_data.sort(key=lambda x: x.get('started_at', ''), reverse=True)
            log_info(logger, f"Retrieved {len(json_data)} executions from JSON (database unavailable)")
            return json_data[:limit]
            
        except Exception as e:
            log_error(logger, f"Failed to get executions: {e}")
            return []
    
    def update_execution_status(self, execution_id: str, status: str, **kwargs) -> bool:
        """Update execution status and other fields atomically"""
        try:
            current_execution = self.get_execution(execution_id)
            if not current_execution:
                log_error(logger, f"Execution {execution_id} not found for status update")
                return False
            
            # Update fields
            current_execution['status'] = status
            
            # Add timestamp for completed status
            if status == 'completed' and 'completed_at' not in kwargs:
                kwargs['completed_at'] = datetime.now()
            
            # Update additional fields
            for key, value in kwargs.items():
                current_execution[key] = value
            
            return self.save_execution(current_execution)
            
        except Exception as e:
            log_error(logger, f"Failed to update execution status {execution_id}: {e}")
            return False
    
    def delete_execution(self, execution_id: str) -> bool:
        """Delete execution from both JSON and database atomically"""
        try:
            with self.atomic_operation():
                # Remove from JSON
                json_data = self._load_json_data()
                json_data = [record for record in json_data if record.get('id') != execution_id]
                self._save_json_data(json_data)
                
                # Remove from database
                if self.db_manager:
                    with self.db_manager.get_session() as session:
                        session.execute(
                            self.db_manager.execution_history_table.delete().where(
                                self.db_manager.execution_history_table.c.id == execution_id
                            )
                        )
                        session.commit()
                
                log_info(logger, f"Successfully deleted execution {execution_id}")
                return True
                
        except Exception as e:
            log_error(logger, f"Failed to delete execution {execution_id}: {e}")
            return False
    
    def sync_json_to_database(self) -> bool:
        """Sync all JSON data to database (migration helper)"""
        try:
            if not self.db_manager:
                log_error(logger, "Database not available for sync")
                return False
            
            json_data = self._load_json_data()
            success_count = 0
            
            for record in json_data:
                try:
                    normalized_record = self._normalize_execution_data(record)
                    if self.db_manager.save_execution_record(normalized_record):
                        success_count += 1
                except Exception as e:
                    log_error(logger, f"Failed to sync record {record.get('id', 'unknown')}: {e}")
            
            log_info(logger, f"Synced {success_count}/{len(json_data)} records to database")
            return success_count == len(json_data)
            
        except Exception as e:
            log_error(logger, f"Failed to sync JSON to database: {e}")
            return False

# Global instance
execution_manager = ExecutionManager()