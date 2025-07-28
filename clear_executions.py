#!/usr/bin/env python3
"""
Safe execution history cleanup script
Clears all execution data while preserving database schema and functionality
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

def clear_json_history():
    """Clear JSON execution history file"""
    json_file = "logs/execution_history.json"
    try:
        # Write empty array to maintain file structure
        with open(json_file, 'w') as f:
            json.dump([], f, indent=2)
        print("✅ Cleared JSON execution history")
        return True
    except Exception as e:
        print(f"❌ Failed to clear JSON: {e}")
        return False

def clear_database_tables():
    """Clear execution-related database tables while preserving schema"""
    db_file = "data/crewai.db"
    if not os.path.exists(db_file):
        print("⚠️  Database file not found, skipping database cleanup")
        return True
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Clear execution history but keep table structure
        cursor.execute("DELETE FROM execution_history")
        deleted_executions = cursor.rowcount
        print(f"✅ Cleared {deleted_executions} execution records from database")
        
        # Clear evaluation history
        cursor.execute("DELETE FROM evaluation_history")
        deleted_evaluations = cursor.rowcount
        print(f"✅ Cleared {deleted_evaluations} evaluation records")
        
        # Clear observability metrics
        cursor.execute("DELETE FROM observability_metrics")
        deleted_metrics = cursor.rowcount
        print(f"✅ Cleared {deleted_metrics} observability records")
        
        # Reset any auto-increment counters
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('execution_history', 'evaluation_history', 'observability_metrics')")
        
        conn.commit()
        conn.close()
        
        print("✅ Database cleanup completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database cleanup failed: {e}")
        return False

def verify_cleanup():
    """Verify that cleanup was successful"""
    print("\n🔍 Verifying cleanup...")
    
    # Check JSON file
    try:
        with open("logs/execution_history.json", 'r') as f:
            data = json.load(f)
            print(f"📄 JSON file: {len(data)} executions remaining")
    except:
        print("❌ Could not verify JSON file")
    
    # Check database
    try:
        conn = sqlite3.connect("data/crewai.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM execution_history")
        exec_count = cursor.fetchone()[0]
        print(f"🗄️  Database executions: {exec_count}")
        
        cursor.execute("SELECT COUNT(*) FROM evaluation_history")
        eval_count = cursor.fetchone()[0]
        print(f"📊 Database evaluations: {eval_count}")
        
        cursor.execute("SELECT COUNT(*) FROM observability_metrics")
        obs_count = cursor.fetchone()[0]
        print(f"📈 Database observability records: {obs_count}")
        
        conn.close()
        
        if exec_count == 0 and eval_count == 0 and obs_count == 0:
            print("✅ All execution data successfully cleared!")
            return True
        else:
            print("⚠️  Some data may remain")
            return False
            
    except Exception as e:
        print(f"❌ Could not verify database: {e}")
        return False

def main():
    print("🧹 Starting safe execution history cleanup...")
    print("=" * 50)
    
    # Step 1: Create backup
    backup_dir = backup_data()
    
    print("\n🗑️  Clearing execution data...")
    
    # Step 2: Clear JSON history
    json_success = clear_json_history()
    
    # Step 3: Clear database tables
    db_success = clear_database_tables()
    
    # Step 4: Verify cleanup
    print("\n" + "=" * 50)
    verification_success = verify_cleanup()
    
    print("\n" + "=" * 50)
    if json_success and db_success and verification_success:
        print("🎉 Cleanup completed successfully!")
        print(f"📁 Backup saved to: {backup_dir}")
        print("\n💡 Your system is now ready for fresh testing!")
        print("   - Database schema preserved")
        print("   - All APIs will continue to work")
        print("   - Frontend will show 0 executions")
    else:
        print("⚠️  Cleanup completed with some issues")
        print(f"📁 Backup available at: {backup_dir}")
        print("💡 You can restore from backup if needed")

if __name__ == "__main__":
    main()