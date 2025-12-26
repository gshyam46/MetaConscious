"""
Test system endpoints with actual database connection
"""
import sys
import os
import asyncio
import asyncpg

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

async def ensure_database_exists():
    """Ensure the metaconscious database exists"""
    try:
        # Parse the database URL to get connection details
        import urllib.parse
        parsed = urllib.parse.urlparse(settings.database_url)
        
        # Connect to postgres database to create metaconscious if needed
        postgres_url = f"postgresql://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
        
        conn = await asyncpg.connect(postgres_url)
        
        # Check if database exists
        result = await conn.fetch("SELECT 1 FROM pg_database WHERE datname = 'metaconscious'")
        
        if not result:
            print("Creating metaconscious database...")
            await conn.execute("CREATE DATABASE metaconscious")
            print("✓ Database created successfully")
        else:
            print("✓ Database already exists")
            
        await conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Database setup error: {e}")
        return False

def test_status_endpoint():
    """Test /api/status endpoint"""
    try:
        print("Testing /api/status endpoint...")
        response = client.get("/api/status")
        
        print(f"Status code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error response: {response.json()}")
            return False
            
        data = response.json()
        print(f"Response: {data}")
        
        # Verify response format matches Next.js
        assert "status" in data
        assert "user" in data
        assert "llm_configured" in data
        
        assert data["status"] == "operational"
        assert isinstance(data["llm_configured"], bool)
        
        print("✓ /api/status endpoint working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Status endpoint error: {e}")
        return False

def test_init_endpoint():
    """Test /api/init endpoint"""
    try:
        print("Testing /api/init endpoint...")
        
        # Test with custom user data
        user_data = {
            "username": "testuser",
            "password": "testpassword"
        }
        
        response = client.post("/api/init", json=user_data)
        
        print(f"Status code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error response: {response.json()}")
            return False
            
        data = response.json()
        print(f"Response: {data}")
        
        # Verify response format matches Next.js
        assert "message" in data
        assert "user" in data
        
        # Should either create user or return existing user message
        assert data["message"] in ["User created", "User already initialized"]
        assert "username" in data["user"]
        assert "id" in data["user"]
        
        print("✓ /api/init endpoint working correctly")
        return True
        
    except Exception as e:
        print(f"✗ Init endpoint error: {e}")
        return False

def test_status_after_init():
    """Test /api/status endpoint after user initialization"""
    try:
        print("Testing /api/status endpoint after init...")
        response = client.get("/api/status")
        
        print(f"Status code: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        # Now user should exist
        assert data["status"] == "operational"
        assert data["user"] is not None
        assert "username" in data["user"]
        
        print("✓ /api/status endpoint working correctly after init")
        return True
        
    except Exception as e:
        print(f"✗ Status endpoint error: {e}")
        return False

async def run_tests():
    """Run all tests"""
    print("Testing system API endpoints with database...")
    print("=" * 60)
    
    # Ensure database exists
    if not await ensure_database_exists():
        return False
    
    # Wait a moment for database to be ready
    await asyncio.sleep(1)
    
    tests = [
        test_status_endpoint,
        test_init_endpoint,
        test_status_after_init
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 60)
    print(f"Tests passed: {passed}/{total}")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    
    if success:
        print("🎉 All system endpoint tests passed!")
        exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        exit(1)