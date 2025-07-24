#!/usr/bin/env python3
"""
Database migration script to sync JSON data to database

This script ensures all execution data from the JSON file is properly
synchronized with the database using the ExecutionManager.
"""

import asyncio
import json
import logging
from pathlib import Path

from execution_manager import execution_manager
from logging_config import log_info, log_error

logger = logging.getLogger(__name__)

def migrate_json_to_database():
    """Migrate all JSON execution data to database"""
    
    print("🔄 Starting JSON to Database migration...")
    
    try:
        # Get all executions from ExecutionManager (which will load from JSON if DB is empty)
        json_executions = execution_manager._load_json_data()
        print(f"📁 Found {len(json_executions)} executions in JSON file")
        
        if not json_executions:
            print("✅ No JSON data to migrate")
            return True
        
        # Sync to database
        success = execution_manager.sync_json_to_database()
        
        if success:
            print("✅ All JSON data successfully synced to database")
            
            # Verify by checking database count
            db_executions = execution_manager.get_all_executions()
            print(f"🔍 Verification: Database now contains {len(db_executions)} executions")
            
            # Show sync status for each execution
            for exec_data in json_executions:
                exec_id = exec_data.get('id', 'unknown')
                db_exec = execution_manager.get_execution(exec_id)
                status = "✅ Synced" if db_exec else "❌ Failed"
                output_status = "📝 Has output" if db_exec and db_exec.get('output_data') else "📄 No output"
                print(f"  {exec_id}: {status} - {output_status}")
            
            return True
        else:
            print("❌ Failed to sync all JSON data to database")
            return False
            
    except Exception as e:
        log_error(logger, f"Migration failed: {e}")
        print(f"❌ Migration error: {e}")
        return False

def validate_database_consistency():
    """Validate that JSON and database are in sync"""
    
    print("\n🔍 Validating database consistency...")
    
    try:
        json_data = execution_manager._load_json_data()
        db_data = execution_manager.get_all_executions()
        
        print(f"📁 JSON file: {len(json_data)} executions")
        print(f"🗄️  Database: {len(db_data)} executions")
        
        # Check for missing executions
        json_ids = {exec_data.get('id') for exec_data in json_data if exec_data.get('id')}
        db_ids = {exec_data.get('id') for exec_data in db_data if exec_data.get('id')}
        
        missing_in_db = json_ids - db_ids
        missing_in_json = db_ids - json_ids
        
        if missing_in_db:
            print(f"⚠️  Missing in database: {missing_in_db}")
        
        if missing_in_json:
            print(f"⚠️  Missing in JSON: {missing_in_json}")
        
        # Check output_data consistency
        output_issues = []
        for exec_id in json_ids & db_ids:
            json_exec = next((e for e in json_data if e.get('id') == exec_id), {})
            db_exec = next((e for e in db_data if e.get('id') == exec_id), {})
            
            json_has_output = bool(json_exec.get('output') or json_exec.get('output_data'))
            db_has_output = bool(db_exec.get('output_data'))
            
            if json_has_output != db_has_output:
                output_issues.append(f"{exec_id} - JSON: {'✓' if json_has_output else '✗'}, DB: {'✓' if db_has_output else '✗'}")
        
        if output_issues:
            print("⚠️  Output data inconsistencies:")
            for issue in output_issues:
                print(f"    {issue}")
        
        if not missing_in_db and not missing_in_json and not output_issues:
            print("✅ Database and JSON are perfectly synchronized!")
            return True
        else:
            print("⚠️  Found consistency issues")
            return False
            
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False

def cleanup_duplicate_records():
    """Remove duplicate records that might exist in JSON"""
    
    print("\n🧹 Cleaning up duplicate records...")
    
    try:
        json_data = execution_manager._load_json_data()
        
        # Find duplicates by ID
        seen_ids = set()
        unique_data = []
        duplicates = []
        
        for exec_data in json_data:
            exec_id = exec_data.get('id')
            if exec_id in seen_ids:
                duplicates.append(exec_id)
            else:
                seen_ids.add(exec_id)
                unique_data.append(exec_data)
        
        if duplicates:
            print(f"🔍 Found {len(duplicates)} duplicate records: {duplicates}")
            
            # Save cleaned data
            execution_manager._save_json_data(unique_data)
            print(f"✅ Removed duplicates, saved {len(unique_data)} unique records")
        else:
            print("✅ No duplicate records found")
        
        return True
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ExecutionManager Database Migration Tool")
    print("=" * 50)
    
    # Step 1: Cleanup duplicates
    cleanup_duplicate_records()
    
    # Step 2: Migrate data
    migrate_success = migrate_json_to_database()
    
    # Step 3: Validate consistency
    validation_success = validate_database_consistency()
    
    print("\n" + "=" * 50)
    if migrate_success and validation_success:
        print("🎉 Migration completed successfully!")
        print("   JSON and database are now perfectly synchronized.")
    else:
        print("⚠️  Migration completed with issues.")
        print("   Please review the output above for details.")