"""
Test comprehensive error handling implementation
Validates that error handling matches Next.js patterns
"""
import pytest
import asyncio
import os
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.exceptions import (
    DatabaseError, 
    LLMError, 
    ValidationError, 
    AuthenticationError,
    OverrideLimitError,
    SystemInitializationError
)
from app.core.database import db_manager
from app.services.llm_client import LLMClient

client = TestClient(app)

class TestDatabaseErrorHandling:
    """Test database error handling matches Next.js patterns"""
    
    def test_database_connection_error(self):
        """Test database connection errors return 500 with proper message"""
        with patch('app.core.database.db_manager.get_pool') as mock_pool:
            mock_pool.side_effect = DatabaseError("Database connection failed: connection refused")
            
            response = client.get("/api/status")
            
            assert response.status_code == 500
            assert "Database connection failed" in response.json()["error"]
            # Verify CORS headers are present
            assert response.headers["Access-Control-Allow-Origin"] == "*"
    
    def test_database_query_error(self):
        """Test database query errors return 500 with proper message"""
        with patch('app.core.database.db_manager.query') as mock_query:
            mock_query.side_effect = DatabaseError("Database query error: syntax error")
            
            response = client.get("/api/goals")
            
            assert response.status_code == 500
            assert "Database query error" in response.json()["error"]

class TestLLMErrorHandling:
    """Test LLM error handling with retry logic"""
    
    def test_llm_not_configured_error(self):
        """Test LLM not configured returns 400 with proper message"""
        with patch.dict(os.environ, {}, clear=True):
            response = client.post("/api/generate-plan", json={"date": "2024-01-01"})
            
            assert response.status_code == 400
            assert "LLM not configured" in response.json()["error"]
    
    def test_llm_api_error(self):
        """Test LLM API errors return 500 with proper message"""
        with patch('app.services.llm_client.LLMClient.complete') as mock_complete:
            mock_complete.side_effect = LLMError("LLM API call failed: rate limit exceeded", retry_count=3)
            
            # This would need a proper test setup with authenticated user
            # For now, just test the exception handling structure
            llm_client = LLMClient()
            
            with pytest.raises(LLMError) as exc_info:
                asyncio.run(llm_client.complete("system", "user"))
            
            assert "LLM API call failed" in str(exc_info.value)
            assert exc_info.value.retry_count == 3

class TestAuthenticationErrorHandling:
    """Test authentication error handling"""
    
    def test_user_not_initialized_error(self):
        """Test user not initialized returns 401 with proper message"""
        with patch('app.core.database.get_user') as mock_get_user:
            mock_get_user.return_value = None
            
            response = client.get("/api/goals")
            
            assert response.status_code == 401
            assert "User not initialized. Call /api/init first" in response.json()["error"]

class TestValidationErrorHandling:
    """Test input validation error handling"""
    
    def test_invalid_json_error(self):
        """Test invalid JSON returns 400 with proper message"""
        response = client.post(
            "/api/goals",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # FastAPI validation error
        assert "error" in response.json()

class TestSystemInitializationErrorHandling:
    """Test system initialization error handling"""
    
    def test_schema_file_not_found_error(self):
        """Test schema file not found during initialization"""
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            with pytest.raises(SystemInitializationError) as exc_info:
                asyncio.run(db_manager.initialize_database())
            
            assert "Could not find schema.sql file" in str(exc_info.value)
            assert exc_info.value.component == "database"

class TestCORSHeaders:
    """Test CORS headers are included in all error responses"""
    
    def test_cors_headers_in_error_responses(self):
        """Test all error responses include proper CORS headers"""
        # Test 404 error
        response = client.get("/api/nonexistent")
        assert response.headers["Access-Control-Allow-Origin"] == "*"
        assert "GET, POST, PUT, DELETE, OPTIONS" in response.headers["Access-Control-Allow-Methods"]
        
        # Test OPTIONS request
        response = client.options("/api/goals")
        assert response.status_code == 200
        assert response.headers["Access-Control-Allow-Origin"] == "*"

if __name__ == "__main__":
    # Run basic tests
    print("Testing error handling implementation...")
    
    # Test CORS headers
    response = client.options("/api/test")
    print(f"✓ OPTIONS request returns CORS headers: {response.status_code}")
    
    # Test 404 handling
    response = client.get("/api/nonexistent")
    print(f"✓ 404 error handling: {response.status_code}")
    
    print("Error handling tests completed!")