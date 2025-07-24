"""
Initialize database tables
"""
from database import get_database_manager

def init_database():
    """Initialize all database tables"""
    print("Initializing database...")
    
    # Get database manager - this will create tables automatically
    db_manager = get_database_manager()
    
    # Test the connection
    if db_manager.test_connection():
        print("✅ Database initialized successfully!")
        
        # Get health status
        health = db_manager.get_health_status()
        print(f"Database type: {health['database_type']}")
        print(f"Status: {health['status']}")
    else:
        print("❌ Failed to initialize database")

if __name__ == "__main__":
    init_database()