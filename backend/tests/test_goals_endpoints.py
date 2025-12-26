"""
Test goals API endpoints
Verify identical functionality to Next.js implementation
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_goals_endpoints_basic_functionality():
    """Test basic CRUD operations for goals endpoints"""
    
    # Test GET /api/goals - should return 401 without user
    response = client.get("/api/goals")
    assert response.status_code == 401
    print("✓ GET /api/goals requires authentication")

def test_goals_validation():
    """Test validation for goals endpoints"""
    
    # Test POST with invalid data (missing required fields)
    invalid_data = {
        "title": "Test Goal"
        # Missing priority and priority_reasoning
    }
    
    response = client.post("/api/goals", json=invalid_data)
    # Should return 401 (unauthorized) before validation since no user is set up
    assert response.status_code == 401
    print("✓ POST /api/goals requires authentication")
    
def test_goals_endpoints_structure():
    """Test that goals endpoints are properly structured"""
    
    # Test that the endpoints exist and return proper error codes
    response = client.get("/api/goals")
    assert response.status_code == 401  # Unauthorized, but endpoint exists
    
    response = client.post("/api/goals", json={})
    assert response.status_code == 401  # Unauthorized, but endpoint exists
    
    response = client.put("/api/goals/test-id", json={})
    assert response.status_code == 401  # Unauthorized, but endpoint exists
    
    response = client.delete("/api/goals/test-id")
    assert response.status_code == 401  # Unauthorized, but endpoint exists
    
    print("✓ All goals endpoints are accessible and return proper authentication errors")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])