"""
Standalone FastAPI Backend Tests
Tests the FastAPI backend independently to validate migration readiness
"""
import pytest
import pytest_asyncio
import asyncio
import httpx
import json
import os
from pathlib import Path
from typing import Dict, Any
import subprocess
import time
import sys

# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)

# Test configuration
FASTAPI_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30.0

class FastAPITester:
    """Standalone FastAPI backend tester"""
    
    def __init__(self):
        self.client = None
        self.test_user_created = False
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(base_url=FASTAPI_BASE_URL, timeout=TEST_TIMEOUT)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()
    
    async def wait_for_backend(self, max_attempts: int = 30) -> bool:
        """Wait for FastAPI backend to be available"""
        for attempt in range(max_attempts):
            try:
                response = await self.client.get("/")
                if response.status_code < 500:
                    return True
            except:
                pass
            await asyncio.sleep(1)
        return False
    
    async def initialize_test_user(self) -> bool:
        """Initialize test user if not already done"""
        if self.test_user_created:
            return True
            
        try:
            # Try to get status first
            status_response = await self.client.get("/api/status")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get("user"):
                    self.test_user_created = True
                    return True
            
            # Initialize user
            init_response = await self.client.post("/api/init", json={
                "username": "testuser",
                "password": "testpassword"
            })
            
            if init_response.status_code in [200, 201]:
                self.test_user_created = True
                return True
                
        except Exception as e:
            print(f"Error initializing test user: {e}")
            
        return False

@pytest_asyncio.fixture
async def fastapi_tester():
    """Fixture providing FastAPI tester"""
    async with FastAPITester() as tester:
        # Wait for backend to be available
        if not await tester.wait_for_backend():
            pytest.skip("FastAPI backend not available")
        
        # Initialize test user
        if not await tester.initialize_test_user():
            pytest.skip("Could not initialize test user")
            
        yield tester

class TestFastAPIEndpoints:
    """Test FastAPI endpoints functionality"""
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, fastapi_tester):
        """Test root endpoint"""
        response = await fastapi_tester.client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "status" in data
    
    async def test_status_endpoint(self, fastapi_tester):
        """Test status endpoint"""
        response = await fastapi_tester.client.get("/api/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "user" in data
        assert "llm_configured" in data
        
        # Should have user after initialization
        assert data["user"] is not None
        assert "id" in data["user"]
        assert "username" in data["user"]
    
    async def test_goals_crud(self, fastapi_tester):
        """Test goals CRUD operations"""
        
        # Test GET empty goals
        response = await fastapi_tester.client.get("/api/goals")
        assert response.status_code == 200
        
        data = response.json()
        assert "goals" in data
        assert isinstance(data["goals"], list)
        
        # Test POST create goal
        goal_data = {
            "title": "Test Goal",
            "description": "A test goal",
            "priority": 3,
            "priority_reasoning": "This is a test goal with medium priority",
            "target_date": "2024-12-31"
        }
        
        create_response = await fastapi_tester.client.post("/api/goals", json=goal_data)
        assert create_response.status_code == 200
        
        created_goal = create_response.json()["goal"]
        assert created_goal["title"] == goal_data["title"]
        assert created_goal["priority"] == goal_data["priority"]
        
        goal_id = created_goal["id"]
        
        # Test GET goals after creation
        response = await fastapi_tester.client.get("/api/goals")
        assert response.status_code == 200
        
        goals = response.json()["goals"]
        assert len(goals) > 0
        assert any(g["id"] == goal_id for g in goals)
        
        # Test PUT update goal
        update_data = {"title": "Updated Test Goal", "priority": 4}
        update_response = await fastapi_tester.client.put(f"/api/goals/{goal_id}", json=update_data)
        assert update_response.status_code == 200
        
        updated_goal = update_response.json()["goal"]
        assert updated_goal["title"] == update_data["title"]
        assert updated_goal["priority"] == update_data["priority"]
        
        # Test DELETE goal
        delete_response = await fastapi_tester.client.delete(f"/api/goals/{goal_id}")
        assert delete_response.status_code == 200
    
    async def test_tasks_crud(self, fastapi_tester):
        """Test tasks CRUD operations"""
        
        # Test GET empty tasks
        response = await fastapi_tester.client.get("/api/tasks")
        assert response.status_code == 200
        
        data = response.json()
        assert "tasks" in data
        assert isinstance(data["tasks"], list)
        
        # Test POST create task
        task_data = {
            "title": "Test Task",
            "description": "A test task",
            "priority": 2,
            "priority_reasoning": "This is a test task with high priority",
            "estimated_duration": 60,
            "due_date": "2024-12-25"
        }
        
        create_response = await fastapi_tester.client.post("/api/tasks", json=task_data)
        assert create_response.status_code == 200
        
        created_task = create_response.json()["task"]
        assert created_task["title"] == task_data["title"]
        assert created_task["priority"] == task_data["priority"]
        
        task_id = created_task["id"]
        
        # Test GET tasks with status filter
        response = await fastapi_tester.client.get("/api/tasks", params={"status": "pending"})
        assert response.status_code == 200
        
        tasks = response.json()["tasks"]
        assert any(t["id"] == task_id for t in tasks)
        
        # Test PUT update task
        update_data = {"status": "completed"}
        update_response = await fastapi_tester.client.put(f"/api/tasks/{task_id}", json=update_data)
        assert update_response.status_code == 200
        
        updated_task = update_response.json()["task"]
        assert updated_task["status"] == "completed"
        
        # Test DELETE task
        delete_response = await fastapi_tester.client.delete(f"/api/tasks/{task_id}")
        assert delete_response.status_code == 200
    
    async def test_plans_endpoint(self, fastapi_tester):
        """Test plans endpoints"""
        
        # Test GET plan (should return null for non-existent plan)
        response = await fastapi_tester.client.get("/api/plans")
        assert response.status_code == 200
        
        data = response.json()
        assert "plan" in data
        # Plan might be null if no plan exists for today
        
        # Test GET plan with specific date
        response = await fastapi_tester.client.get("/api/plans", params={"date": "2024-12-25"})
        assert response.status_code == 200
        
        data = response.json()
        assert "plan" in data
    
    async def test_calendar_crud(self, fastapi_tester):
        """Test calendar CRUD operations"""
        
        # Test GET empty calendar
        response = await fastapi_tester.client.get("/api/calendar")
        assert response.status_code == 200
        
        data = response.json()
        assert "events" in data
        assert isinstance(data["events"], list)
        
        # Test POST create event
        event_data = {
            "title": "Test Event",
            "description": "A test calendar event",
            "start_time": "2024-12-20T10:00:00Z",
            "end_time": "2024-12-20T11:00:00Z",
            "event_type": "internal",
            "is_blocking": True
        }
        
        create_response = await fastapi_tester.client.post("/api/calendar", json=event_data)
        assert create_response.status_code == 200
        
        created_event = create_response.json()["event"]
        assert created_event["title"] == event_data["title"]
        
        event_id = created_event["id"]
        
        # Test DELETE event
        delete_response = await fastapi_tester.client.delete(f"/api/calendar/{event_id}")
        assert delete_response.status_code == 200
    
    async def test_relationships_crud(self, fastapi_tester):
        """Test relationships CRUD operations"""
        
        # Test GET empty relationships
        response = await fastapi_tester.client.get("/api/relationships")
        assert response.status_code == 200
        
        data = response.json()
        assert "relationships" in data
        assert isinstance(data["relationships"], list)
        
        # Test POST create relationship
        relationship_data = {
            "name": "Test Person",
            "relationship_type": "friend",
            "priority": 3,
            "time_budget_hours": 5,
            "notes": "Test relationship"
        }
        
        create_response = await fastapi_tester.client.post("/api/relationships", json=relationship_data)
        assert create_response.status_code == 200
        
        created_relationship = create_response.json()["relationship"]
        assert created_relationship["name"] == relationship_data["name"]
        
        relationship_id = created_relationship["id"]
        
        # Test DELETE relationship
        delete_response = await fastapi_tester.client.delete(f"/api/relationships/{relationship_id}")
        assert delete_response.status_code == 200

class TestLLMIntegration:
    """Test LLM integration"""
    
    async def test_generate_plan_no_llm_key(self, fastapi_tester):
        """Test plan generation without LLM key"""
        
        # Temporarily remove LLM key if set
        original_key = os.environ.get('LLM_API_KEY')
        if original_key:
            del os.environ['LLM_API_KEY']
        
        try:
            plan_data = {"date": "2024-12-25"}
            response = await fastapi_tester.client.post("/api/generate-plan", json=plan_data)
            
            # Should return 400 error for missing LLM configuration
            assert response.status_code == 400
            
            error_data = response.json()
            assert "error" in error_data
            assert "LLM" in error_data["error"]
            
        finally:
            # Restore original key
            if original_key:
                os.environ['LLM_API_KEY'] = original_key
    
    @pytest.mark.skipif(not os.getenv('LLM_API_KEY'), reason="LLM_API_KEY not configured")
    async def test_generate_plan_with_llm(self, fastapi_tester):
        """Test plan generation with LLM configured"""
        
        plan_data = {"date": "2024-12-25"}
        response = await fastapi_tester.client.post("/api/generate-plan", json=plan_data)
        
        # Should succeed with LLM configured
        if response.status_code == 200:
            plan_response = response.json()
            assert "plan" in plan_response
            assert "message" in plan_response
        else:
            # LLM might fail for other reasons, but should not be a 400 config error
            assert response.status_code != 400 or "LLM" not in response.json().get("error", "")

class TestErrorHandling:
    """Test error handling"""
    
    async def test_not_found_errors(self, fastapi_tester):
        """Test 404 error handling"""
        
        response = await fastapi_tester.client.get("/api/nonexistent")
        assert response.status_code == 404
        
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data
    
    async def test_validation_errors(self, fastapi_tester):
        """Test validation error handling"""
        
        # Test invalid goal data
        invalid_goal = {"title": "", "priority": 10}  # Invalid priority
        
        response = await fastapi_tester.client.post("/api/goals", json=invalid_goal)
        
        # Should return validation error
        assert response.status_code >= 400
        
        error_data = response.json()
        assert "error" in error_data or "detail" in error_data

def run_standalone_tests():
    """Run standalone FastAPI tests"""
    print("Running standalone FastAPI tests...")
    
    # Run pytest
    result = subprocess.run([
        sys.executable, "-m", "pytest", 
        __file__, 
        "-v", 
        "--tb=short"
    ], capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0

if __name__ == "__main__":
    # Check if FastAPI backend is running
    try:
        response = httpx.get(FASTAPI_BASE_URL, timeout=5.0)
        print(f"FastAPI backend is running (status: {response.status_code})")
    except:
        print("FastAPI backend is not running. Please start it with:")
        print("uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
        sys.exit(1)
    
    # Run tests
    success = run_standalone_tests()
    sys.exit(0 if success else 1)