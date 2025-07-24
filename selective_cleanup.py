#!/usr/bin/env python3
"""
Selective cleanup script - keeps only exec_003 and removes all other executions
"""

import json
import sqlite3
import os
from datetime import datetime

def backup_data():
    """Create backup of current data before clearing"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    print(f"📁 Creating backup in {backup_dir}/")
    
    # Backup JSON file
    json_file = "logs/execution_history.json"
    if os.path.exists(json_file):
        os.system(f"cp {json_file} {backup_dir}/execution_history.json")
        print("✅ Backed up JSON execution history")
    
    # Backup database
    db_file = "data/crewai.db"
    if os.path.exists(db_file):
        os.system(f"cp {db_file} {backup_dir}/crewai.db")
        print("✅ Backed up SQLite database")
    
    return backup_dir

def clean_json_keep_exec_003():
    """Clean JSON execution history but keep exec_003"""
    json_file = "logs/execution_history.json"
    try:
        # Load current data
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Find exec_003
        exec_003 = None
        for execution in data:
            if execution.get('id') == 'exec_003':
                exec_003 = execution
                break
        
        if exec_003:
            # Keep only exec_003
            filtered_data = [exec_003]
            print(f"✅ Found exec_003, preserving it")
        else:
            # If exec_003 not found, clear everything
            filtered_data = []
            print("⚠️  exec_003 not found in JSON, clearing all")
        
        # Write filtered data
        with open(json_file, 'w') as f:
            json.dump(filtered_data, f, indent=2, default=str)
        
        print(f"✅ JSON cleanup complete - kept {len(filtered_data)} executions")
        return True
        
    except Exception as e:
        print(f"❌ Failed to clean JSON: {e}")
        return False

def clean_database_keep_exec_003():
    """Clean database but keep exec_003"""
    db_file = "data/crewai.db"
    if not os.path.exists(db_file):
        print("⚠️  Database file not found, skipping database cleanup")
        return True
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Delete all executions except exec_003
        cursor.execute("DELETE FROM execution_history WHERE id != 'exec_003'")
        deleted_executions = cursor.rowcount
        print(f"✅ Deleted {deleted_executions} execution records (kept exec_003)")
        
        # Check if exec_003 exists in database
        cursor.execute("SELECT COUNT(*) FROM execution_history WHERE id = 'exec_003'")
        exec_003_count = cursor.fetchone()[0]
        print(f"📊 exec_003 in database: {'Found' if exec_003_count > 0 else 'Not found'}")
        
        # Clear evaluation history (can be regenerated)
        cursor.execute("DELETE FROM evaluation_history")
        deleted_evaluations = cursor.rowcount
        print(f"✅ Cleared {deleted_evaluations} evaluation records")
        
        # Clear observability metrics (can be regenerated)
        cursor.execute("DELETE FROM observability_metrics")
        deleted_metrics = cursor.rowcount
        print(f"✅ Cleared {deleted_metrics} observability records")
        
        # Don't reset auto-increment since we're keeping exec_003
        
        conn.commit()
        conn.close()
        
        print("✅ Database selective cleanup completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database cleanup failed: {e}")
        return False

def verify_cleanup():
    """Verify that cleanup preserved exec_003"""
    print("\n🔍 Verifying selective cleanup...")
    
    # Check JSON file
    try:
        with open("logs/execution_history.json", 'r') as f:
            data = json.load(f)
            print(f"📄 JSON file: {len(data)} executions remaining")
            if data:
                for execution in data:
                    print(f"   - {execution.get('id', 'unknown')}")
    except:
        print("❌ Could not verify JSON file")
    
    # Check database
    try:
        conn = sqlite3.connect("data/crewai.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM execution_history")
        executions = cursor.fetchall()
        print(f"🗄️  Database executions: {len(executions)}")
        for execution in executions:
            print(f"   - {execution[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM evaluation_history")
        eval_count = cursor.fetchone()[0]
        print(f"📊 Database evaluations: {eval_count}")
        
        cursor.execute("SELECT COUNT(*) FROM observability_metrics")
        obs_count = cursor.fetchone()[0]
        print(f"📈 Database observability records: {obs_count}")
        
        conn.close()
        
        # Success if we have exactly 1 execution (exec_003) and 0 eval/obs records
        success = len(executions) == 1 and executions[0][0] == 'exec_003' and eval_count == 0 and obs_count == 0
        
        if success:
            print("✅ Selective cleanup successful - only exec_003 remains!")
            return True
        else:
            print("⚠️  Cleanup may not have worked as expected")
            return False
            
    except Exception as e:
        print(f"❌ Could not verify database: {e}")
        return False

def main():
    print("🧹 Starting selective cleanup - preserving exec_003...")
    print("=" * 60)
    
    # Step 1: Create backup
    backup_dir = backup_data()
    
    print("\n🗑️  Performing selective cleanup...")
    
    # Step 2: Clean JSON but keep exec_003
    json_success = clean_json_keep_exec_003()
    
    # Step 3: Clean database but keep exec_003
    db_success = clean_database_keep_exec_003()
    
    # Step 4: Verify cleanup
    print("\n" + "=" * 60)
    verification_success = verify_cleanup()
    
    print("\n" + "=" * 60)
    if json_success and db_success and verification_success:
        print("🎉 Selective cleanup completed successfully!")
        print(f"📁 Backup saved to: {backup_dir}")
        print("\n💡 System is ready for fresh testing:")
        print("   - exec_003 preserved as reference")
        print("   - All other executions removed")
        print("   - Evaluation and observability data cleared")
    else:
        print("⚠️  Cleanup completed with some issues")
        print(f"📁 Backup available at: {backup_dir}")
        print("💡 You can restore from backup if needed")

if __name__ == "__main__":
    main()