#!/usr/bin/env python3
"""
Enhanced server startup script with database migration and health checks.
This script will:
1. Run database migration to ensure proper setup
2. Start the enhanced API server
3. Perform health checks
"""

import logging
import os
import subprocess
import sys
import time
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_database_migration():
    """Run database migration before starting the server"""
    logger.info("Running database migration...")
    
    try:
        result = subprocess.run([
            sys.executable, "migrate_database.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info("✓ Database migration completed successfully")
            return True
        else:
            logger.error(f"✗ Database migration failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("✗ Database migration timed out")
        return False
    except Exception as e:
        logger.error(f"✗ Database migration error: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available"""
    logger.info("Checking dependencies...")
    
    required_modules = [
        'fastapi',
        'uvicorn',
        'sqlite3',
        'pydantic'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        logger.error(f"✗ Missing required modules: {missing_modules}")
        logger.info("Install them with: pip install fastapi uvicorn pydantic")
        return False
    else:
        logger.info("✓ All required dependencies are available")
        return True

def start_enhanced_api_server():
    """Start the enhanced API server"""
    logger.info("Starting enhanced API server...")
    
    try:
        # Import and start the server
        from enhanced_api import app
        import uvicorn
        
        logger.info("✓ Enhanced API module loaded successfully")
        logger.info("Starting server on http://localhost:8100")
        
        # Start the server
        uvicorn.run(
            "enhanced_api:app",
            host="0.0.0.0",
            port=8100,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        logger.error(f"✗ Failed to import enhanced_api module: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Failed to start server: {e}")
        return False

def perform_health_check():
    """Perform a basic health check on the server"""
    logger.info("Performing health check...")
    
    import requests
    import time
    
    # Wait a bit for server to start
    time.sleep(2)
    
    try:
        response = requests.get("http://localhost:8100/docs", timeout=10)
        if response.status_code == 200:
            logger.info("✓ Server health check passed")
            return True
        else:
            logger.warning(f"Server health check returned status {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        return False

def main():
    """Main startup function"""
    logger.info("="*60)
    logger.info("ENHANCED API SERVER STARTUP")
    logger.info("="*60)
    
    # Step 1: Check dependencies
    if not check_dependencies():
        logger.error("❌ Dependency check failed. Cannot start server.")
        return False
    
    # Step 2: Run database migration
    if not run_database_migration():
        logger.error("❌ Database migration failed. Cannot start server.")
        return False
    
    # Step 3: Start the server
    logger.info("🚀 Starting enhanced API server...")
    logger.info("📊 Server will be available at: http://localhost:8100")
    logger.info("📖 API documentation: http://localhost:8100/docs")
    logger.info("🔍 Execution history: http://localhost:8100/api/execution-history")
    logger.info("")
    logger.info("Press Ctrl+C to stop the server")
    logger.info("="*60)
    
    try:
        start_enhanced_api_server()
        return True
    except KeyboardInterrupt:
        logger.info("\n🛑 Server stopped by user")
        return True
    except Exception as e:
        logger.error(f"❌ Server startup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
