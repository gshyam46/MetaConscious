"""
Test system API endpoints (/api/status and /api/init)
Verifies identical behavior to Next.js implementation
"""
import sys
import os
import asyncio
import json
from typing import Dict, Any
from unittest.mock import AsyncMock, patch

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fastapi.testclient import TestClient

# Mock database functions before importing app
with patch('app.core.database.get_user') as mock_get_user, \
     patch('app.core.database.create_user') as mock_create_user, \
     patch('app.core.database.initialize_database') as mock_init_db:
    
    # Set up mocks
    mock_get_user.return_value = None  # Initially no user
    mock_create_user.return_value = {
        "id": "test-user-id",
        "username": "testuser",
        "created_at": "2024-01-01T00:00:00"
    }
    mock_init_db.return_value = True
    
    from app.main import app

client = TestClient(app)

def test_status_endpoint_no_user():
    """Test /api/status endpoint when no user exists"""
    try:
        with patch('app.core.database.get_user', return_value=None):
            response = client.get("/api/status")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response format matches Next.js
            assert "status" in data
            assert "user" in data
            assert "llm_configured" in data
            
            assert data["status"] == "operational"
            assert data["user"] is None  # No user should exist initially
            assert isinstance(data["llm_configured"], bool)
            
            print("✓ /api/status endpoint working correctly (no user)")
            return True
    except Exception as e:
        print(f"✗ Status endpoint error: {e}")
        return False

def test_init_endpoint_create_user():
    """Test /api/init endpoint to create user"""
    try:
        # Mock no existing user and successful user creation
        with patch('app.core.database.get_user', return_value=None), \
             patch('app.core.database.create_user', return_value={
                 "id": "test-user-id",
                 "username": "testuser"
             }), \
             patch('app.core.database.initialize_database', return_value=True):
            
            # Test with custom user data
            user_data = {
                "username": "testuser",
                "password": "testpassword"
            }
            
            response = client.post("/api/init", json=user_data)
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response format matches Next.js
            assert "message" in data
            assert "user" in data
            
            assert data["message"] == "User created"
            assert data["user"]["username"] == "testuser"
            assert "id" in data["user"]
            
            print("✓ /api/init endpoint working correctly (create user)")
            return True
    except Exception as e:
        print(f"✗ Init endpoint error: {e}")
        return False

def test_status_endpoint_with_user():
    """Test /api/status endpoint when user exists"""
    try:
        with patch('app.core.database.get_user', return_value={
            "id": "test-user-id",
            "username": "testuser"
        }):
            response = client.get("/api/status")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response format matches Next.js
            assert data["status"] == "operational"
            assert data["user"] is not None
            assert data["user"]["username"] == "testuser"
            assert "id" in data["user"]
            
            print("✓ /api/status endpoint working correctly (with user)")
            return True
    except Exception as e:
        print(f"✗ Status endpoint error: {e}")
        return False

def test_init_endpoint_user_exists():
    """Test /api/init endpoint when user already exists"""
    try:
        with patch('app.core.database.get_user', return_value={
            "id": "existing-user-id",
            "username": "testuser"
        }):
            user_data = {
                "username": "anotheruser",
                "password": "anotherpassword"
            }
            
            response = client.post("/api/init", json=user_data)
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response format matches Next.js when user already exists
            assert "message" in data
            assert "user" in data
            
            assert data["message"] == "User already initialized"
            assert data["user"]["username"] == "testuser"  # Should return existing user
            
            print("✓ /api/init endpoint working correctly (user exists)")
            return True
    except Exception as e:
        print(f"✗ Init endpoint error: {e}")
        return False

def test_init_endpoint_no_data():
    """Test /api/init endpoint with no user data (should use defaults)"""
    try:
        with patch('app.core.database.get_user', return_value=None), \
             patch('app.core.database.create_user', return_value={
                 "id": "default-user-id",
                 "username": "user"
             }), \
             patch('app.core.database.initialize_database', return_value=True):
            
            # Test with no data (should use defaults)
            response = client.post("/api/init")
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify response format matches Next.js
            assert data["message"] == "User created"
            assert data["user"]["username"] == "user"  # Default username
            
            print("✓ /api/init endpoint working correctly (default values)")
            return True
    except Exception as e:
        print(f"✗ Init endpoint error: {e}")
        return False

def run_tests():
    """Run all system endpoint tests"""
    print("Testing system API endpoints...")
    print("=" * 50)
    
    tests = [
        test_status_endpoint_no_user,
        test_init_endpoint_create_user,
        test_status_endpoint_with_user,
        test_init_endpoint_user_exists,
        test_init_endpoint_no_data
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    return passed == total

if __name__ == "__main__":
    success = run_tests()
    
    if success:
        print("🎉 All system endpoint tests passed!")
        exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        exit(1)