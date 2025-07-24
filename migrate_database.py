#!/usr/bin/env python3
"""
Database migration script to ensure proper database setup and data integrity.
This script will:
1. Check if the database exists and is accessible
2. Create missing tables if needed
3. Migrate any existing data from old formats
4. Verify data integrity
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_script_directory():
    """Get the directory where this script is located"""
    return Path(__file__).parent.absolute()

def get_database_path():
    """Get the database path"""
    script_dir = get_script_directory()
    config_dir = script_dir / "config"
    config_dir.mkdir(exist_ok=True)
    return config_dir / "config.db"

def check_database_exists():
    """Check if database file exists and is accessible"""
    db_path = get_database_path()
    logger.info(f"Checking database at: {db_path}")
    
    if not db_path.exists():
        logger.info("Database file does not exist, will be created")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        conn.close()
        logger.info("Database file exists and is accessible")
        return True
    except sqlite3.Error as e:
        logger.error(f"Database file exists but is not accessible: {e}")
        return False

def create_database_tables():
    """Create database tables if they don't exist"""
    db_path = get_database_path()
    logger.info("Creating database tables...")
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        cursor = conn.cursor()
        
        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=memory")
        
        # Create version history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS version_history (
                id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                created_by TEXT DEFAULT 'system',
                change_description TEXT DEFAULT '',
                UNIQUE(entity_type, entity_id, version)
            )
        """)
        
        # Create execution history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS execution_history (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                agent_id TEXT,
                prompt_id TEXT,
                input_data TEXT,
                output_data TEXT,
                execution_time REAL,
                status TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Create test results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                test_input TEXT,
                test_output TEXT,
                execution_time REAL,
                status TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        conn.commit()
        logger.info("Database tables created successfully")
        
    except sqlite3.Error as e:
        logger.error(f"Error creating database tables: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def migrate_legacy_data():
    """Migrate data from legacy formats (e.g., JSON files)"""
    script_dir = get_script_directory()
    logs_dir = script_dir / "logs"
    
    # Check for legacy execution history JSON file
    legacy_file = logs_dir / "execution_history.json"
    if legacy_file.exists():
        logger.info(f"Found legacy execution history file: {legacy_file}")
        try:
            with open(legacy_file, 'r') as f:
                legacy_data = json.load(f)
            
            if legacy_data:
                logger.info(f"Migrating {len(legacy_data)} legacy execution records...")
                migrate_execution_history(legacy_data)
                
                # Backup the legacy file
                backup_file = legacy_file.with_suffix('.json.backup')
                legacy_file.rename(backup_file)
                logger.info(f"Legacy file backed up to: {backup_file}")
                
        except Exception as e:
            logger.error(f"Error migrating legacy data: {e}")

def migrate_execution_history(legacy_data):
    """Migrate execution history from legacy JSON format"""
    db_path = get_database_path()
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        cursor = conn.cursor()
        
        migrated_count = 0
        for record in legacy_data:
            try:
                # Generate a unique ID for the record
                record_id = f"migrated_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{migrated_count}"
                
                # Extract data from legacy format
                workflow_id = record.get('workflow_name', 'unknown')
                agent_id = record.get('agent_id', 'unknown')
                prompt_id = record.get('prompt_id', 'unknown')
                input_data = json.dumps(record.get('input_data', {}))
                output_data = json.dumps(record.get('output', {}))
                execution_time = record.get('duration', 0.0)
                status = record.get('status', 'unknown')
                error_message = record.get('error_message', '')
                created_at = record.get('started_at', datetime.now().isoformat())
                
                # Check if record already exists
                cursor.execute(
                    "SELECT COUNT(*) FROM execution_history WHERE workflow_id = ? AND created_at = ?",
                    (workflow_id, created_at)
                )
                
                if cursor.fetchone()[0] == 0:
                    # Insert the record
                    cursor.execute("""
                        INSERT INTO execution_history (
                            id, workflow_id, agent_id, prompt_id, input_data, output_data,
                            execution_time, status, error_message, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record_id, workflow_id, agent_id, prompt_id, input_data, output_data,
                        execution_time, status, error_message, created_at
                    ))
                    migrated_count += 1
                    
            except Exception as e:
                logger.warning(f"Error migrating record: {e}")
                continue
        
        conn.commit()
        logger.info(f"Successfully migrated {migrated_count} execution history records")
        
    except sqlite3.Error as e:
        logger.error(f"Error during migration: {e}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def verify_database_integrity():
    """Verify database integrity and data accessibility"""
    db_path = get_database_path()
    logger.info("Verifying database integrity...")
    
    try:
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        cursor = conn.cursor()
        
        # Check table existence
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['version_history', 'execution_history', 'test_results']
        for table in expected_tables:
            if table in tables:
                logger.info(f"✓ Table '{table}' exists")
                
                # Count records
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"  - {count} records in {table}")
            else:
                logger.error(f"✗ Table '{table}' is missing")
        
        # Test basic operations
        cursor.execute("SELECT COUNT(*) FROM execution_history")
        execution_count = cursor.fetchone()[0]
        logger.info(f"Database verification complete. {execution_count} execution records available.")
        
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database integrity check failed: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main migration function"""
    logger.info("Starting database migration...")
    
    try:
        # Step 1: Check database existence
        db_exists = check_database_exists()
        
        # Step 2: Create tables
        create_database_tables()
        
        # Step 3: Migrate legacy data if database was newly created
        if not db_exists:
            migrate_legacy_data()
        
        # Step 4: Verify integrity
        if verify_database_integrity():
            logger.info("Database migration completed successfully!")
            return True
        else:
            logger.error("Database migration failed verification!")
            return False
            
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
