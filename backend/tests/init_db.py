"""
Initialize database schema manually
"""
import sys
import os
import asyncio

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.database import db_manager

async def init_database():
    """Initialize the database schema"""
    try:
        print("Initializing database schema...")
        result = await db_manager.initialize_database()
        
        if result:
            print("✓ Database schema initialized successfully")
            
            # Test basic query
            users = await db_manager.query("SELECT * FROM users LIMIT 1", [])
            print(f"✓ Users table accessible, found {len(users)} users")
            
        return result
        
    except Exception as e:
        print(f"✗ Database initialization error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await db_manager.close()

if __name__ == "__main__":
    success = asyncio.run(init_database())
    
    if success:
        print("🎉 Database initialization complete!")
        exit(0)
    else:
        print("❌ Database initialization failed.")
        exit(1)