"""
Debug FastAPI Backend Issues
"""
import httpx
import asyncio
import json

async def debug_endpoints():
    """Debug FastAPI endpoints to see what's causing 500 errors"""
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        
        print("=== DEBUGGING FASTAPI ENDPOINTS ===\n")
        
        # Test goals POST
        print("Testing Goals POST:")
        goal_data = {
            "title": "Test Goal",
            "description": "A test goal",
            "priority": 3,
            "priority_reasoning": "This is a test goal with medium priority",
            "target_date": "2024-12-31"
        }
        
        try:
            response = await client.post(f"{base_url}/api/goals", json=goal_data)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # Test tasks POST
        print("Testing Tasks POST:")
        task_data = {
            "title": "Test Task",
            "description": "A test task",
            "priority": 2,
            "priority_reasoning": "This is a test task with high priority",
            "estimated_duration": 60,
            "due_date": "2024-12-25"
        }
        
        try:
            response = await client.post(f"{base_url}/api/tasks", json=task_data)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # Test plans GET
        print("Testing Plans GET:")
        try:
            response = await client.get(f"{base_url}/api/plans")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
        
        print("\n" + "="*50 + "\n")
        
        # Test generate plan
        print("Testing Generate Plan:")
        plan_data = {"date": "2024-12-25"}
        try:
            response = await client.post(f"{base_url}/api/generate-plan", json=plan_data)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_endpoints())