"""
Simple FastAPI Backend Tests
Tests the FastAPI backend functionality
"""
import pytest
import httpx
import asyncio
import os

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio

FASTAPI_BASE_URL = "http://localhost:8000"

class TestFastAPIBasic:
    """Basic FastAPI functionality tests"""
    
    async def test_root_endpoint(self):
        """Test root endpoint"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/")
            assert response.status_code == 200
            
            data = response.json()
            assert "message" in data
            print(f"✓ Root endpoint working: {data}")
    
    async def test_status_endpoint_before_init(self):
        """Test status endpoint before user initialization"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/api/status")
            
            # Should return 401 if no user is initialized
            if response.status_code == 401:
                print("✓ Status endpoint correctly returns 401 before init")
            elif response.status_code == 200:
                data = response.json()
                print(f"✓ Status endpoint working: {data}")
            else:
                pytest.fail(f"Unexpected status code: {response.status_code}")
    
    async def test_user_initialization(self):
        """Test user initialization"""
        async with httpx.AsyncClient() as client:
            # Try to initialize user
            init_data = {
                "username": "testuser",
                "password": "testpassword"
            }
            
            response = await client.post(f"{FASTAPI_BASE_URL}/api/init", json=init_data)
            
            # Should succeed (200) or indicate already initialized
            assert response.status_code in [200, 201]
            
            data = response.json()
            assert "user" in data
            print(f"✓ User initialization: {data}")
    
    async def test_status_endpoint_after_init(self):
        """Test status endpoint after user initialization"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{FASTAPI_BASE_URL}/api/status")
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert "user" in data
            assert "llm_configured" in data
            
            # Should have user after initialization
            assert data["user"] is not None
            print(f"✓ Status after init: {data}")
    
    async def test_goals_endpoint(self):
        """Test goals endpoint basic functionality"""
        async with httpx.AsyncClient() as client:
            # Test GET goals
            response = await client.get(f"{FASTAPI_BASE_URL}/api/goals")
            assert response.status_code == 200
            
            data = response.json()
            assert "goals" in data
            assert isinstance(data["goals"], list)
            print(f"✓ Goals GET working: {len(data['goals'])} goals")
            
            # Test POST create goal
            goal_data = {
                "title": "Test Goal",
                "description": "A test goal",
                "priority": 3,
                "priority_reasoning": "This is a test goal with medium priority",
                "target_date": "2024-12-31"
            }
            
            create_response = await client.post(f"{FASTAPI_BASE_URL}/api/goals", json=goal_data)
            assert create_response.status_code == 200
            
            created_goal = create_response.json()["goal"]
            assert created_goal["title"] == goal_data["title"]
            print(f"✓ Goal creation working: {created_goal['id']}")
            
            # Clean up - delete the test goal
            goal_id = created_goal["id"]
            delete_response = await client.delete(f"{FASTAPI_BASE_URL}/api/goals/{goal_id}")
            assert delete_response.status_code == 200
            print(f"✓ Goal deletion working")
    
    async def test_tasks_endpoint(self):
        """Test tasks endpoint basic functionality"""
        async with httpx.AsyncClient() as client:
            # Test GET tasks
            response = await client.get(f"{FASTAPI_BASE_URL}/api/tasks")
            assert response.status_code == 200
            
            data = response.json()
            assert "tasks" in data
            assert isinstance(data["tasks"], list)
            print(f"✓ Tasks GET working: {len(data['tasks'])} tasks")
            
            # Test POST create task
            task_data = {
                "title": "Test Task",
                "description": "A test task",
                "priority": 2,
                "priority_reasoning": "This is a test task with high priority",
                "estimated_duration": 60,
                "due_date": "2024-12-25"
            }
            
            create_response = await client.post(f"{FASTAPI_BASE_URL}/api/tasks", json=task_data)
            assert create_response.status_code == 200
            
            created_task = create_response.json()["task"]
            assert created_task["title"] == task_data["title"]
            print(f"✓ Task creation working: {created_task['id']}")
            
            # Clean up - delete the test task
            task_id = created_task["id"]
            delete_response = await client.delete(f"{FASTAPI_BASE_URL}/api/tasks/{task_id}")
            assert delete_response.status_code == 200
            print(f"✓ Task deletion working")
    
    async def test_plans_endpoint(self):
        """Test plans endpoint"""
        async with httpx.AsyncClient() as client:
            # Test GET plan
            response = await client.get(f"{FASTAPI_BASE_URL}/api/plans")
            assert response.status_code == 200
            
            data = response.json()
            assert "plan" in data
            print(f"✓ Plans GET working: plan exists = {data['plan'] is not None}")
    
    async def test_llm_integration_no_key(self):
        """Test LLM integration without API key"""
        # Temporarily remove LLM key if set
        original_key = os.environ.get('LLM_API_KEY')
        if original_key:
            del os.environ['LLM_API_KEY']
        
        try:
            async with httpx.AsyncClient() as client:
                plan_data = {"date": "2024-12-25"}
                response = await client.post(f"{FASTAPI_BASE_URL}/api/generate-plan", json=plan_data)
                
                # Should return 400 error for missing LLM configuration
                assert response.status_code == 400
                
                error_data = response.json()
                assert "error" in error_data
                assert "LLM" in error_data["error"]
                print(f"✓ LLM error handling working: {error_data['error']}")
                
        finally:
            # Restore original key
            if original_key:
                os.environ['LLM_API_KEY'] = original_key
    
    @pytest.mark.skipif(not os.getenv('LLM_API_KEY'), reason="LLM_API_KEY not configured")
    async def test_llm_integration_with_key(self):
        """Test LLM integration with API key"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            plan_data = {"date": "2024-12-25"}
            response = await client.post(f"{FASTAPI_BASE_URL}/api/generate-plan", json=plan_data)
            
            # Should succeed with LLM configured
            if response.status_code == 200:
                plan_response = response.json()
                assert "plan" in plan_response
                assert "message" in plan_response
                print(f"✓ LLM integration working: plan generated")
            else:
                # LLM might fail for other reasons, but should not be a 400 config error
                error_data = response.json()
                print(f"⚠️ LLM call failed (not config issue): {error_data}")
                assert response.status_code != 400 or "LLM" not in error_data.get("error", "")

if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])