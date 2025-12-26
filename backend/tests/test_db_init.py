"""
Test database initialization with updated error handling
"""
import sys
import os
import asyncio

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.database import DatabaseManager

async def test_db_init():
    """Test database initialization"""
    print("Testing database initialization...")
    
    try:
        db = DatabaseManager()
        result = await db.initialize_database()
        print(f"✓ Database initialization result: {result}")
        
        # Test user creation
        user = await db.get_user()
        print(f"Current user: {user}")
        
        if not user:
            print("Creating test user...")
            import hashlib
            password_hash = hashlib.sha256("testpass".encode()).hexdigest()
            new_user = await db.create_user("testuser", password_hash)
            print(f"✓ Created user: {new_user}")
        else:
            print(f"✓ User already exists: {user}")
        
        await db.close()
        return True
        
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_db_init())
    if success:
        print("🎉 Database initialization test passed!")
    else:
        print("❌ Database initialization test failed!")