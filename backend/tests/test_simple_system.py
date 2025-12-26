"""
Simple test for system endpoints
"""
import sys
import os
from unittest.mock import patch

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_status_simple():
    """Simple test for status endpoint"""
    print("Testing /api/status endpoint...")
    
    with patch('app.core.database.get_user', return_value=None):
        response = client.get("/api/status")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert data["user"] is None
        
    print("✓ Status endpoint test passed")

def test_init_simple():
    """Simple test for init endpoint"""
    print("Testing /api/init endpoint...")
    
    with patch('app.core.database.get_user', return_value=None), \
         patch('app.core.database.create_user', return_value={
             "id": "test-id",
             "username": "testuser"
         }), \
         patch('app.core.database.initialize_database', return_value=True):
        
        user_data = {"username": "testuser", "password": "testpass"}
        response = client.post("/api/init", json=user_data)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User created"
        assert data["user"]["username"] == "testuser"
        
    print("✓ Init endpoint test passed")

if __name__ == "__main__":
    try:
        test_status_simple()
        test_init_simple()
        print("🎉 All tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()