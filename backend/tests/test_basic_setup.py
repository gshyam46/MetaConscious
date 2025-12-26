"""
Basic setup test to verify FastAPI backend structure
"""
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_imports():
    """Test that all modules can be imported"""
    try:
        from app.main import app
        from app.core.config import settings
        from app.core.database import DatabaseManager
        from app.models.schemas import DailyPlan, GoalCreate, TaskCreate
        from app.models.database import User, Goal, Task
        from app.api.routes import system, goals, tasks, plans, calendar, relationships
        
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_fastapi_app():
    """Test FastAPI app creation"""
    try:
        from app.main import app
        assert app.title == "MetaConscious Backend"
        print("✓ FastAPI app created successfully")
        return True
    except Exception as e:
        print(f"✗ FastAPI app error: {e}")
        return False

def test_config():
    """Test configuration loading"""
    try:
        from app.core.config import settings
        assert hasattr(settings, 'database_url')
        assert hasattr(settings, 'llm_provider')
        assert hasattr(settings, 'max_weekly_overrides')
        print("✓ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

def test_pydantic_models():
    """Test Pydantic model validation"""
    try:
        from app.models.schemas import TimeBlock, GoalCreate
        
        # Test TimeBlock validation
        time_block = TimeBlock(
            start_time="09:00",
            end_time="10:00",
            activity="Test activity",
            priority=3,
            reasoning="Test reasoning"
        )
        assert time_block.start_time == "09:00"
        
        # Test GoalCreate validation
        goal = GoalCreate(
            title="Test Goal",
            priority=4,
            priority_reasoning="This is important for testing"
        )
        assert goal.title == "Test Goal"
        
        print("✓ Pydantic models working correctly")
        return True
    except Exception as e:
        print(f"✗ Pydantic model error: {e}")
        return False

def test_llm_client():
    """Test LLM client initialization and interface"""
    try:
        from app.services.llm_client import LLMClient
        
        # Test client initialization
        client = LLMClient()
        assert hasattr(client, 'provider')
        assert hasattr(client, 'model')
        assert hasattr(client, 'api_key')
        assert hasattr(client, 'base_url')
        
        # Test method existence
        assert hasattr(client, 'complete')
        assert hasattr(client, 'generate_plan')
        assert hasattr(client, 'get_planning_system_prompt')
        assert hasattr(client, 'build_planning_prompt')
        
        # Test prompt generation
        system_prompt = client.get_planning_system_prompt()
        assert "MetaConscious" in system_prompt
        assert "FINAL AUTHORITY" in system_prompt
        
        # Test planning prompt building
        context = {
            'date': '2024-01-01',
            'goals': [],
            'tasks': [],
            'calendarEvents': [],
            'relationships': [],
            'recentPerformance': {}
        }
        user_prompt = client.build_planning_prompt(context)
        assert "2024-01-01" in user_prompt
        assert "ACTIVE GOALS:" in user_prompt
        
        print("✓ LLM client initialized and interface working correctly")
        return True
    except Exception as e:
        print(f"✗ LLM client error: {e}")
        return False

if __name__ == "__main__":
    print("Testing FastAPI backend setup...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_fastapi_app,
        test_config,
        test_pydantic_models,
        test_llm_client
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! FastAPI backend setup is complete.")
        exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        exit(1)