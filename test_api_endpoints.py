#!/usr/bin/env python3
"""
Test script to verify API endpoints are working correctly.
This script will test the execution history endpoints and database connectivity.
"""

import json
import logging
import requests
import sys
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_endpoint(url, description):
    """Test a single API endpoint"""
    logger.info(f"Testing {description}: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✓ {description} - Status: {response.status_code}")
            
            # Log some basic info about the response
            if isinstance(data, dict):
                if 'data' in data:
                    if isinstance(data['data'], list):
                        logger.info(f"  - Returned {len(data['data'])} records")
                    else:
                        logger.info(f"  - Data type: {type(data['data'])}")
                
                if 'total' in data:
                    logger.info(f"  - Total records: {data['total']}")
                    
                if 'page' in data and 'page_size' in data:
                    logger.info(f"  - Page: {data['page']}, Page size: {data['page_size']}")
            
            return True, data
        else:
            logger.error(f"✗ {description} - Status: {response.status_code}")
            logger.error(f"  - Response: {response.text}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        logger.error(f"✗ {description} - Connection refused (server not running?)")
        return False, None
    except requests.exceptions.Timeout:
        logger.error(f"✗ {description} - Request timeout")
        return False, None
    except Exception as e:
        logger.error(f"✗ {description} - Error: {e}")
        return False, None

def test_execution_history_endpoints():
    """Test execution history related endpoints"""
    base_url = "http://localhost:8100"
    
    tests = [
        (f"{base_url}/api/execution-history", "Execution History (default)"),
        (f"{base_url}/api/execution-history?page=1&page_size=5", "Execution History (page 1, 5 items)"),
        (f"{base_url}/api/execution-history?page=2&page_size=5", "Execution History (page 2, 5 items)"),
        (f"{base_url}/api/execution-history?page=1&page_size=20", "Execution History (page 1, 20 items)"),
    ]
    
    results = []
    for url, description in tests:
        success, data = test_api_endpoint(url, description)
        results.append((description, success, data))
    
    return results

def analyze_execution_history_data(results):
    """Analyze the execution history data for consistency"""
    logger.info("\n" + "="*50)
    logger.info("ANALYZING EXECUTION HISTORY DATA")
    logger.info("="*50)
    
    for description, success, data in results:
        if success and data and 'data' in data:
            records = data['data']
            if records:
                logger.info(f"\n{description}:")
                logger.info(f"  - Records returned: {len(records)}")
                
                # Check first record structure
                first_record = records[0]
                logger.info(f"  - Sample record ID: {first_record.get('id', 'N/A')}")
                logger.info(f"  - Sample workflow: {first_record.get('workflow_name', 'N/A')}")
                logger.info(f"  - Sample status: {first_record.get('status', 'N/A')}")
                logger.info(f"  - Sample created_at: {first_record.get('created_at', 'N/A')}")
                
                # Check for required fields
                required_fields = ['id', 'workflow_id', 'status', 'created_at']
                missing_fields = []
                for field in required_fields:
                    if field not in first_record:
                        missing_fields.append(field)
                
                if missing_fields:
                    logger.warning(f"  - Missing fields: {missing_fields}")
                else:
                    logger.info(f"  - ✓ All required fields present")

def test_database_connectivity():
    """Test direct database connectivity"""
    logger.info("\n" + "="*50)
    logger.info("TESTING DIRECT DATABASE CONNECTIVITY")
    logger.info("="*50)
    
    try:
        from config_manager import ConfigManager
        
        # Test ConfigManager initialization
        config_manager = ConfigManager()
        logger.info("✓ ConfigManager initialized successfully")
        
        # Test getting execution history count
        count = config_manager.get_execution_history_count()
        logger.info(f"✓ Total execution history records: {count}")
        
        # Test getting execution history
        history = config_manager.get_execution_history(limit=5, offset=0)
        logger.info(f"✓ Retrieved {len(history)} execution history records")
        
        if history:
            sample_record = history[0]
            logger.info(f"  - Sample record: {sample_record.get('id', 'N/A')}")
            logger.info(f"  - Sample workflow: {sample_record.get('workflow_name', 'N/A')}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Database connectivity test failed: {e}")
        return False

def test_server_status():
    """Test if the server is running"""
    logger.info("\n" + "="*50)
    logger.info("TESTING SERVER STATUS")
    logger.info("="*50)
    
    try:
        response = requests.get("http://localhost:8100/docs", timeout=5)
        if response.status_code == 200:
            logger.info("✓ Server is running (FastAPI docs accessible)")
            return True
        else:
            logger.warning(f"Server responded with status {response.status_code}")
            return False
    except:
        logger.error("✗ Server is not accessible")
        return False

def main():
    """Main test function"""
    logger.info("Starting API endpoint tests...")
    logger.info(f"Test started at: {datetime.now().isoformat()}")
    
    # Test server status
    server_running = test_server_status()
    
    # Test database connectivity
    db_working = test_database_connectivity()
    
    # Test API endpoints (only if server is running)
    if server_running:
        results = test_execution_history_endpoints()
        analyze_execution_history_data(results)
        
        # Count successful tests
        successful_tests = sum(1 for _, success, _ in results if success)
        total_tests = len(results)
        
        logger.info(f"\n" + "="*50)
        logger.info("TEST SUMMARY")
        logger.info("="*50)
        logger.info(f"Server Status: {'✓ Running' if server_running else '✗ Not accessible'}")
        logger.info(f"Database Connectivity: {'✓ Working' if db_working else '✗ Failed'}")
        logger.info(f"API Tests: {successful_tests}/{total_tests} passed")
        
        if successful_tests == total_tests and db_working:
            logger.info("🎉 All tests passed! The API is working correctly.")
            return True
        else:
            logger.error("❌ Some tests failed. Check the logs above for details.")
            return False
    else:
        logger.error("❌ Server is not running. Cannot test API endpoints.")
        logger.info("💡 Try starting the server with: python3 run_enhanced_api.py")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
