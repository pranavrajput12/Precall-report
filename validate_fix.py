#!/usr/bin/env python3
"""
Final validation script to confirm the database data recovery fix is working correctly.
This script performs comprehensive checks to ensure the issue is permanently resolved.
"""

import json
import logging
import requests
import sqlite3
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_database_direct_access():
    """Validate direct database access"""
    logger.info("🔍 Validating direct database access...")
    
    try:
        # Get database path
        script_dir = Path(__file__).parent.absolute()
        db_path = script_dir / "config" / "config.db"
        
        if not db_path.exists():
            logger.error(f"❌ Database file does not exist: {db_path}")
            return False
        
        # Connect to database
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        cursor = conn.cursor()
        
        # Check execution_history table
        cursor.execute("SELECT COUNT(*) FROM execution_history")
        count = cursor.fetchone()[0]
        
        if count == 0:
            logger.error("❌ No execution history records found in database")
            return False
        
        logger.info(f"✅ Database contains {count} execution history records")
        
        # Get sample record
        cursor.execute("SELECT id, workflow_id, status, created_at FROM execution_history LIMIT 1")
        sample = cursor.fetchone()
        
        if sample:
            logger.info(f"✅ Sample record: ID={sample[0]}, Workflow={sample[1]}, Status={sample[2]}")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Database validation failed: {e}")
        return False

def validate_api_endpoints():
    """Validate API endpoints are working"""
    logger.info("🔍 Validating API endpoints...")
    
    endpoints_to_test = [
        ("http://localhost:8100/api/execution-history", "Basic execution history"),
        ("http://localhost:8100/api/execution-history?page=1&page_size=5", "Paginated execution history"),
        ("http://localhost:8100/docs", "API documentation")
    ]
    
    all_passed = True
    
    for url, description in endpoints_to_test:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ {description}: OK")
                
                # For execution history endpoints, check data structure
                if "execution-history" in url:
                    data = response.json()
                    if "items" in data and len(data["items"]) > 0:
                        logger.info(f"   📊 Returned {len(data['items'])} records")
                        
                        # Check pagination info
                        if "pagination" in data:
                            pagination = data["pagination"]
                            logger.info(f"   📄 Total: {pagination.get('total', 'N/A')}, Page: {pagination.get('page', 'N/A')}")
                    else:
                        logger.warning(f"   ⚠️ No data items found in response")
            else:
                logger.error(f"❌ {description}: HTTP {response.status_code}")
                all_passed = False
                
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ {description}: Connection refused (server not running?)")
            all_passed = False
        except Exception as e:
            logger.error(f"❌ {description}: {e}")
            all_passed = False
    
    return all_passed

def validate_data_consistency():
    """Validate data consistency between database and API"""
    logger.info("🔍 Validating data consistency...")
    
    try:
        # Get count from database
        script_dir = Path(__file__).parent.absolute()
        db_path = script_dir / "config" / "config.db"
        conn = sqlite3.connect(str(db_path), timeout=30.0)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM execution_history")
        db_count = cursor.fetchone()[0]
        conn.close()
        
        # Get count from API
        response = requests.get("http://localhost:8100/api/execution-history?page=1&page_size=1", timeout=10)
        if response.status_code == 200:
            api_data = response.json()
            api_count = api_data.get("pagination", {}).get("total", 0)
            
            if db_count == api_count:
                logger.info(f"✅ Data consistency verified: {db_count} records in both database and API")
                return True
            else:
                logger.error(f"❌ Data inconsistency: Database has {db_count} records, API reports {api_count}")
                return False
        else:
            logger.error(f"❌ Could not get API count: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Data consistency check failed: {e}")
        return False

def validate_frontend_compatibility():
    """Validate that the API response format is compatible with frontend expectations"""
    logger.info("🔍 Validating frontend compatibility...")
    
    try:
        response = requests.get("http://localhost:8100/api/execution-history?page=1&page_size=1", timeout=10)
        if response.status_code != 200:
            logger.error(f"❌ API request failed: HTTP {response.status_code}")
            return False
        
        data = response.json()
        
        # Check required top-level fields
        required_fields = ["items", "pagination"]
        for field in required_fields:
            if field not in data:
                logger.error(f"❌ Missing required field: {field}")
                return False
        
        # Check pagination structure
        pagination = data["pagination"]
        pagination_fields = ["total", "page", "page_size", "total_pages", "has_next", "has_prev"]
        for field in pagination_fields:
            if field not in pagination:
                logger.error(f"❌ Missing pagination field: {field}")
                return False
        
        # Check record structure (if records exist)
        if data["items"]:
            record = data["items"][0]
            record_fields = ["id", "workflow_id", "workflow_name", "status", "created_at", "output"]
            for field in record_fields:
                if field not in record:
                    logger.error(f"❌ Missing record field: {field}")
                    return False
        
        logger.info("✅ Frontend compatibility validated")
        return True
        
    except Exception as e:
        logger.error(f"❌ Frontend compatibility check failed: {e}")
        return False

def validate_server_health():
    """Validate server health and configuration"""
    logger.info("🔍 Validating server health...")
    
    try:
        # Check if server is running on correct port
        response = requests.get("http://localhost:8100/docs", timeout=5)
        if response.status_code == 200:
            logger.info("✅ Server is running on port 8100")
        else:
            logger.error(f"❌ Server health check failed: HTTP {response.status_code}")
            return False
        
        # Check if frontend proxy is configured correctly
        try:
            with open("package.json", "r") as f:
                package_data = json.load(f)
                proxy = package_data.get("proxy")
                if proxy == "http://localhost:8100":
                    logger.info("✅ Frontend proxy correctly configured")
                else:
                    logger.warning(f"⚠️ Frontend proxy is set to: {proxy} (expected: http://localhost:8100)")
        except Exception as e:
            logger.warning(f"⚠️ Could not check frontend proxy configuration: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Server health check failed: {e}")
        return False

def main():
    """Main validation function"""
    logger.info("="*70)
    logger.info("🔧 DATABASE DATA RECOVERY - FINAL VALIDATION")
    logger.info("="*70)
    logger.info(f"Validation started at: {datetime.now().isoformat()}")
    logger.info("")
    
    validation_results = []
    
    # Run all validations
    validations = [
        ("Database Direct Access", validate_database_direct_access),
        ("API Endpoints", validate_api_endpoints),
        ("Data Consistency", validate_data_consistency),
        ("Frontend Compatibility", validate_frontend_compatibility),
        ("Server Health", validate_server_health)
    ]
    
    for name, validation_func in validations:
        logger.info(f"Running: {name}")
        result = validation_func()
        validation_results.append((name, result))
        logger.info("")
    
    # Summary
    logger.info("="*70)
    logger.info("📋 VALIDATION SUMMARY")
    logger.info("="*70)
    
    passed = 0
    total = len(validation_results)
    
    for name, result in validation_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{name:.<30} {status}")
        if result:
            passed += 1
    
    logger.info("")
    logger.info(f"Overall Result: {passed}/{total} validations passed")
    
    if passed == total:
        logger.info("🎉 ALL VALIDATIONS PASSED! The database data recovery fix is working correctly.")
        logger.info("🚀 The system is ready for use.")
        return True
    else:
        logger.error("❌ Some validations failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
