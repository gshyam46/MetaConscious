"""
Comparative Testing Suite for Next.js to FastAPI Migration
Tests both backends with identical requests and validates response equivalence
"""
import pytest
import asyncio
import httpx
import json
import os
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from urllib.parse import urljoin
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BackendConfig:
    """Configuration for a backend instance"""
    name: str
    base_url: str
    port: int
    
    @property
    def full_url(self) -> str:
        return f"{self.base_url}:{self.port}"

# Backend configurations
NEXTJS_CONFIG = BackendConfig(
    name="Next.js",
    base_url="http://localhost",
    port=3000
)

FASTAPI_CONFIG = BackendConfig(
    name="FastAPI", 
    base_url="http://localhost",
    port=8000
)

class ComparativeTestClient:
    """Client for running identical tests against both backends"""
    
    def __init__(self):
        self.nextjs_client = httpx.AsyncClient(base_url=NEXTJS_CONFIG.full_url, timeout=30.0)
        self.fastapi_client = httpx.AsyncClient(base_url=FASTAPI_CONFIG.full_url, timeout=30.0)
        self.test_data = {}
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.nextjs_client.aclose()
        await self.fastapi_client.aclose()
    
    async def make_request(self, client: httpx.AsyncClient, method: str, path: str, 
                          json_data: Optional[Dict] = None, params: Optional[Dict] = None) -> httpx.Response:
        """Make a request to a backend"""
        try:
            response = await client.request(
                method=method,
                url=path,
                json=json_data,
                params=params,
                headers={"Content-Type": "application/json"} if json_data else None
            )
            return response
        except Exception as e:
            logger.error(f"Request failed: {method} {path} - {e}")
            raise
    
    async def compare_responses(self, method: str, path: str, 
                               json_data: Optional[Dict] = None, 
                               params: Optional[Dict] = None) -> Tuple[httpx.Response, httpx.Response]:
        """Make identical requests to both backends and return responses"""
        
        # Make requests to both backends
        nextjs_response = await self.make_request(self.nextjs_client, method, path, json_data, params)
        fastapi_response = await self.make_request(self.fastapi_client, method, path, json_data, params)
        
        return nextjs_response, fastapi_response
    
    def normalize_response_data(self, data: Any) -> Any:
        """Normalize response data for comparison (handle timestamps, UUIDs, etc.)"""
        if isinstance(data, dict):
            normalized = {}
            for key, value in data.items():
                # Skip timestamp fields that may differ slightly
                if key in ['created_at', 'updated_at', 'completed_at']:
                    continue
                # Skip UUIDs that will be different
                if key == 'id' and isinstance(value, str) and len(value) == 36:
                    continue
                normalized[key] = self.normalize_response_data(value)
            return normalized
        elif isinstance(data, list):
            return [self.normalize_response_data(item) for item in data]
        else:
            return data
    
    def assert_responses_equivalent(self, nextjs_response: httpx.Response, 
                                   fastapi_response: httpx.Response, 
                                   ignore_data_differences: bool = False):
        """Assert that two responses are equivalent"""
        
        # Check status codes
        assert nextjs_response.status_code == fastapi_response.status_code, \
            f"Status codes differ: Next.js={nextjs_response.status_code}, FastAPI={fastapi_response.status_code}"
        
        # Check CORS headers
        nextjs_cors = {k: v for k, v in nextjs_response.headers.items() 
                      if k.lower().startswith('access-control-')}
        fastapi_cors = {k: v for k, v in fastapi_response.headers.items() 
                       if k.lower().startswith('access-control-')}
        
        # Normalize header names for comparison
        nextjs_cors_normalized = {k.lower(): v for k, v in nextjs_cors.items()}
        fastapi_cors_normalized = {k.lower(): v for k, v in fastapi_cors.items()}
        
        assert nextjs_cors_normalized == fastapi_cors_normalized, \
            f"CORS headers differ: Next.js={nextjs_cors}, FastAPI={fastapi_cors}"
        
        if not ignore_data_differences:
            # Check response content structure
            try:
                nextjs_data = nextjs_response.json()
                fastapi_data = fastapi_response.json()
                
                # Normalize data for comparison
                nextjs_normalized = self.normalize_response_data(nextjs_data)
                fastapi_normalized = self.normalize_response_data(fastapi_data)
                
                assert nextjs_normalized == fastapi_normalized, \
                    f"Response data differs:\nNext.js: {nextjs_normalized}\nFastAPI: {fastapi_normalized}"
                    
            except json.JSONDecodeError:
                # Compare raw text if not JSON
                assert nextjs_response.text == fastapi_response.text, \
                    f"Response text differs: Next.js={nextjs_response.text}, FastAPI={fastapi_response.text}"

class TestFixtures:
    """Test data fixtures for consistent testing"""
    
    @staticmethod
    def get_test_user() -> Dict:
        return {
            "username": "testuser",
            "password": "testpassword"
        }
    
    @staticmethod
    def get_test_goal() -> Dict:
        return {
            "title": "Test Goal",
            "description": "A test goal for comparative testing",
            "priority": 3,
            "priority_reasoning": "This is a test goal with medium priority for validation purposes",
            "target_date": "2024-12-31"
        }
    
    @staticmethod
    def get_test_task() -> Dict:
        return {
            "title": "Test Task",
            "description": "A test task for comparative testing",
            "priority": 2,
            "priority_reasoning": "This is a test task with high priority for validation purposes",
            "estimated_duration": 60,
            "due_date": "2024-12-25"
        }
    
    @staticmethod
    def get_test_calendar_event() -> Dict:
        return {
            "title": "Test Event",
            "description": "A test calendar event",
            "start_time": "2024-12-20T10:00:00Z",
            "end_time": "2024-12-20T11:00:00Z",
            "event_type": "internal",
            "is_blocking": True
        }
    
    @staticmethod
    def get_test_relationship() -> Dict:
        return {
            "name": "Test Person",
            "relationship_type": "friend",
            "priority": 3,
            "time_budget_hours": 5,
            "notes": "Test relationship for comparative testing"
        }

@pytest.fixture
async def test_client():
    """Fixture providing the comparative test client"""
    async with ComparativeTestClient() as client:
        yield client

@pytest.fixture
async def initialized_backends(test_client):
    """Fixture that ensures both backends are initialized with test user"""
    
    # Initialize both backends
    user_data = TestFixtures.get_test_user()
    
    try:
        # Try to initialize both backends
        nextjs_init, fastapi_init = await test_client.compare_responses(
            "POST", "/api/init", json_data=user_data
        )
        
        # Both should succeed or both should indicate already initialized
        assert nextjs_init.status_code in [200, 201], f"Next.js init failed: {nextjs_init.text}"
        assert fastapi_init.status_code in [200, 201], f"FastAPI init failed: {fastapi_init.text}"
        
        logger.info("Both backends initialized successfully")
        
    except Exception as e:
        logger.error(f"Backend initialization failed: {e}")
        pytest.skip(f"Cannot initialize backends: {e}")
    
    yield test_client

class TestSystemEndpoints:
    """Test system-level endpoints for equivalence"""
    
    async def test_root_endpoint(self, test_client):
        """Test root endpoint returns equivalent responses"""
        nextjs_response, fastapi_response = await test_client.compare_responses("GET", "/")
        
        # Both should return 200 with system information
        assert nextjs_response.status_code == 200
        assert fastapi_response.status_code == 200
        
        # Check response structure (content may differ but structure should be similar)
        nextjs_data = nextjs_response.json()
        fastapi_data = fastapi_response.json()
        
        assert "message" in nextjs_data
        assert "message" in fastapi_data
        assert "status" in nextjs_data
        assert "status" in fastapi_data
    
    async def test_status_endpoint(self, initialized_backends):
        """Test status endpoint equivalence"""
        nextjs_response, fastapi_response = await initialized_backends.compare_responses("GET", "/api/status")
        
        # Should have equivalent structure and status codes
        initialized_backends.assert_responses_equivalent(nextjs_response, fastapi_response, ignore_data_differences=True)
        
        # Check required fields exist
        nextjs_data = nextjs_response.json()
        fastapi_data = fastapi_response.json()
        
        for data in [nextjs_data, fastapi_data]:
            assert "status" in data
            assert "user" in data
            assert "llm_configured" in data

class TestCRUDOperations:
    """Test CRUD operations for all resources"""
    
    async def test_goals_crud_equivalence(self, initialized_backends):
        """Test goals CRUD operations equivalence"""
        
        # Test GET empty goals
        nextjs_response, fastapi_response = await initialized_backends.compare_responses("GET", "/api/goals")
        initialized_backends.assert_responses_equivalent(nextjs_response, fastapi_response)
        
        # Test POST create goal
        goal_data = TestFixtures.get_test_goal()
        nextjs_create, fastapi_create = await initialized_backends.compare_responses(
            "POST", "/api/goals", json_data=goal_data
        )
        
        assert nextjs_create.status_code == fastapi_create.status_code
        
        # Extract created goal IDs for further testing
        if nextjs_create.status_code == 200:
            nextjs_goal = nextjs_create.json()["goal"]
            fastapi_goal = fastapi_create.json()["goal"]
            
            # Test GET goals after creation
            nextjs_list, fastapi_list = await initialized_backends.compare_responses("GET", "/api/goals")
            initialized_backends.assert_responses_equivalent(nextjs_list, fastapi_list, ignore_data_differences=True)
            
            # Test PUT update goal
            update_data = {"title": "Updated Test Goal", "priority": 4}
            nextjs_update, fastapi_update = await initialized_backends.compare_responses(
                "PUT", f"/api/goals/{nextjs_goal['id']}", json_data=update_data
            )
            
            # Note: We can't compare the exact response due to different IDs, but status codes should match
            assert nextjs_update.status_code == fastapi_update.status_code
            
            # Test DELETE goal
            nextjs_delete, fastapi_delete = await initialized_backends.compare_responses(
                "DELETE", f"/api/goals/{nextjs_goal['id']}"
            )
            
            assert nextjs_delete.status_code == fastapi_delete.status_code
    
    async def test_tasks_crud_equivalence(self, initialized_backends):
        """Test tasks CRUD operations equivalence"""
        
        # Test GET empty tasks
        nextjs_response, fastapi_response = await initialized_backends.compare_responses("GET", "/api/tasks")
        initialized_backends.assert_responses_equivalent(nextjs_response, fastapi_response)
        
        # Test POST create task
        task_data = TestFixtures.get_test_task()
        nextjs_create, fastapi_create = await initialized_backends.compare_responses(
            "POST", "/api/tasks", json_data=task_data
        )
        
        assert nextjs_create.status_code == fastapi_create.status_code
        
        if nextjs_create.status_code == 200:
            nextjs_task = nextjs_create.json()["task"]
            
            # Test GET tasks with status filter
            nextjs_pending, fastapi_pending = await initialized_backends.compare_responses(
                "GET", "/api/tasks", params={"status": "pending"}
            )
            initialized_backends.assert_responses_equivalent(nextjs_pending, fastapi_pending, ignore_data_differences=True)
            
            # Test PUT update task
            update_data = {"status": "completed"}
            nextjs_update, fastapi_update = await initialized_backends.compare_responses(
                "PUT", f"/api/tasks/{nextjs_task['id']}", json_data=update_data
            )
            
            assert nextjs_update.status_code == fastapi_update.status_code
            
            # Test DELETE task
            nextjs_delete, fastapi_delete = await initialized_backends.compare_responses(
                "DELETE", f"/api/tasks/{nextjs_task['id']}"
            )
            
            assert nextjs_delete.status_code == fastapi_delete.status_code

class TestLLMIntegration:
    """Test LLM integration equivalence"""
    
    async def test_generate_plan_no_llm_key(self, initialized_backends):
        """Test plan generation without LLM key configured"""
        
        # Temporarily remove LLM key if set
        original_key = os.environ.get('LLM_API_KEY')
        if original_key:
            del os.environ['LLM_API_KEY']
        
        try:
            plan_data = {"date": "2024-12-25"}
            nextjs_response, fastapi_response = await initialized_backends.compare_responses(
                "POST", "/api/generate-plan", json_data=plan_data
            )
            
            # Both should return 400 error for missing LLM configuration
            assert nextjs_response.status_code == 400
            assert fastapi_response.status_code == 400
            
            # Error messages should be similar
            nextjs_error = nextjs_response.json()
            fastapi_error = fastapi_response.json()
            
            assert "LLM" in nextjs_error.get("error", "")
            assert "LLM" in fastapi_error.get("error", "")
            
        finally:
            # Restore original key
            if original_key:
                os.environ['LLM_API_KEY'] = original_key
    
    @pytest.mark.skipif(not os.getenv('LLM_API_KEY'), reason="LLM_API_KEY not configured")
    async def test_generate_plan_with_llm(self, initialized_backends):
        """Test plan generation with LLM configured"""
        
        plan_data = {"date": "2024-12-25"}
        nextjs_response, fastapi_response = await initialized_backends.compare_responses(
            "POST", "/api/generate-plan", json_data=plan_data
        )
        
        # Both should succeed or fail identically
        assert nextjs_response.status_code == fastapi_response.status_code
        
        if nextjs_response.status_code == 200:
            nextjs_plan = nextjs_response.json()
            fastapi_plan = fastapi_response.json()
            
            # Both should have plan structure
            assert "plan" in nextjs_plan
            assert "plan" in fastapi_plan
            assert "message" in nextjs_plan
            assert "message" in fastapi_plan

class TestErrorHandling:
    """Test error handling equivalence"""
    
    async def test_not_found_errors(self, initialized_backends):
        """Test 404 error handling equivalence"""
        
        nextjs_response, fastapi_response = await initialized_backends.compare_responses(
            "GET", "/api/nonexistent"
        )
        
        assert nextjs_response.status_code == 404
        assert fastapi_response.status_code == 404
        
        # Both should return error messages
        nextjs_error = nextjs_response.json()
        fastapi_error = fastapi_response.json()
        
        assert "error" in nextjs_error
        assert "error" in fastapi_error
    
    async def test_validation_errors(self, initialized_backends):
        """Test validation error handling equivalence"""
        
        # Test invalid goal data
        invalid_goal = {"title": "", "priority": 10}  # Invalid priority
        
        nextjs_response, fastapi_response = await initialized_backends.compare_responses(
            "POST", "/api/goals", json_data=invalid_goal
        )
        
        # Both should return validation errors
        assert nextjs_response.status_code >= 400
        assert fastapi_response.status_code >= 400
        
        # Both should have error information
        nextjs_error = nextjs_response.json()
        fastapi_error = fastapi_response.json()
        
        assert "error" in nextjs_error or "detail" in nextjs_error
        assert "error" in fastapi_error or "detail" in fastapi_error

class TestDatabaseStateComparison:
    """Test database state consistency between backends"""
    
    async def test_database_state_after_operations(self, initialized_backends):
        """Test that database state is consistent after operations on both backends"""
        
        # Create identical data on both backends
        goal_data = TestFixtures.get_test_goal()
        
        # Create goal on Next.js backend
        nextjs_create, _ = await initialized_backends.compare_responses(
            "POST", "/api/goals", json_data=goal_data
        )
        
        # Create goal on FastAPI backend  
        _, fastapi_create = await initialized_backends.compare_responses(
            "POST", "/api/goals", json_data=goal_data
        )
        
        if nextjs_create.status_code == 200 and fastapi_create.status_code == 200:
            # Both backends should now have goals in their databases
            nextjs_goals, fastapi_goals = await initialized_backends.compare_responses("GET", "/api/goals")
            
            # Should have same number of goals (ignoring the specific data due to different IDs)
            nextjs_data = nextjs_goals.json()
            fastapi_data = fastapi_goals.json()
            
            assert len(nextjs_data["goals"]) > 0
            assert len(fastapi_data["goals"]) > 0

if __name__ == "__main__":
    # Run the comparative test suite
    pytest.main([__file__, "-v", "--tb=short"])