"""
Simple test to verify error handling is working
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_basic_error_handling():
    """Test basic error handling functionality"""
    print("Testing basic error handling...")
    
    # Test OPTIONS request (should work)
    response = client.options("/api/goals")
    print(f"OPTIONS /api/goals: {response.status_code}")
    print(f"CORS headers: {dict(response.headers)}")
    
    # Test GET request without authentication (should return 401)
    response = client.get("/api/goals")
    print(f"GET /api/goals (no auth): {response.status_code}")
    print(f"Response: {response.json()}")
    print(f"CORS headers: {dict(response.headers)}")
    
    # Test nonexistent endpoint (should return 404)
    response = client.get("/api/nonexistent")
    print(f"GET /api/nonexistent: {response.status_code}")
    print(f"Response: {response.json()}")
    print(f"CORS headers: {dict(response.headers)}")
    
    # Test status endpoint (should work)
    response = client.get("/api/status")
    print(f"GET /api/status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    print("Basic error handling test completed!")

if __name__ == "__main__":
    test_basic_error_handling()