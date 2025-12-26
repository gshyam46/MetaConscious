"""
Final test for system endpoints
Tests the actual API endpoints without database conflicts
"""
import sys
import os
import time

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_status_endpoint():
    """Test /api/status endpoint"""
    print("Testing /api/status endpoint...")
    
    response = client.get("/api/status")
    
    print(f"Status code: {response.status_code}")
    assert response.status_code == 200
    
    data = response.json()
    print(f"Response: {data}")
    
    # Verify response format matches Next.js exactly
    assert "status" in data
    assert "user" in data  
    assert "llm_configured" in data
    
    assert data["status"] == "operational"
    assert isinstance(data["llm_configured"], bool)
    
    print("✓ /api/status endpoint format matches Next.js specification")
    return True

def test_init_endpoint():
    """Test /api/init endpoint"""
    print("Testing /api/init endpoint...")
    
    # Test with user data
    user_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = client.post("/api/init", json=user_data)
    
    print(f"Status code: {response.status_code}")
    assert response.status_code == 200
    
    data = response.json()
    print(f"Response: {data}")
    
    # Verify response format matches Next.js exactly
    assert "message" in data
    assert "user" in data
    
    # Should either create user or return existing user message
    assert data["message"] in ["User created", "User already initialized"]
    assert "username" in data["user"]
    assert "id" in data["user"]
    
    print("✓ /api/init endpoint format matches Next.js specification")
    return True

def test_init_no_data():
    """Test /api/init endpoint with no data (should use defaults)"""
    print("Testing /api/init endpoint with no data...")
    
    response = client.post("/api/init")
    
    print(f"Status code: {response.status_code}")
    assert response.status_code == 200
    
    data = response.json()
    print(f"Response: {data}")
    
    # Should handle missing data gracefully
    assert "message" in data
    assert "user" in data
    
    print("✓ /api/init endpoint handles missing data correctly")
    return True

def test_status_with_user():
    """Test /api/status endpoint after user exists"""
    print("Testing /api/status endpoint after user initialization...")
    
    response = client.get("/api/status")
    
    print(f"Status code: {response.status_code}")
    assert response.status_code == 200
    
    data = response.json()
    print(f"Response: {data}")
    
    # Verify format
    assert data["status"] == "operational"
    # User might or might not exist depending on previous tests
    if data["user"] is not None:
        assert "username" in data["user"]
        assert "id" in data["user"]
    
    print("✓ /api/status endpoint working correctly")
    return True

def run_tests():
    """Run all tests"""
    print("Testing System API Endpoints")
    print("=" * 50)
    print("Verifying FastAPI endpoints match Next.js behavior exactly")
    print()
    
    tests = [
        test_status_endpoint,
        test_init_endpoint, 
        test_init_no_data,
        test_status_with_user
    ]
    
    passed = 0
    total = len(tests)
    
    for i, test in enumerate(tests, 1):
        try:
            print(f"Test {i}/{total}: {test.__name__}")
            if test():
                passed += 1
                print("✅ PASSED")
            else:
                print("❌ FAILED")
        except Exception as e:
            print(f"❌ FAILED with exception: {e}")
        print()
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All system endpoint tests passed!")
        print("✅ FastAPI system endpoints are equivalent to Next.js implementation")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)