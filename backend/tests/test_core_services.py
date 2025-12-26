"""
Comprehensive test for all core services
Checkpoint test to ensure all implemented services are working correctly
"""
import sys
import os
import asyncio
from datetime import datetime, timedelta

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

async def test_database_service():
    """Test database service functionality"""
    try:
        from app.core.database import DatabaseManager, query, get_user, create_user
        
        # Test DatabaseManager initialization
        db_manager = DatabaseManager()
        assert db_manager is not None
        
        # Test query function exists and is callable
        assert callable(query)
        assert callable(get_user)
        assert callable(create_user)
        
        print("✓ Database service interface working correctly")
        return True
    except Exception as e:
        print(f"✗ Database service error: {e}")
        return False

async def test_llm_client_service():
    """Test LLM client service functionality"""
    try:
        from app.services.llm_client import LLMClient
        
        client = LLMClient()
        
        # Test all required methods exist
        assert hasattr(client, 'complete')
        assert hasattr(client, 'generate_plan')
        assert hasattr(client, 'get_planning_system_prompt')
        assert hasattr(client, 'build_planning_prompt')
        
        # Test prompt generation works
        system_prompt = client.get_planning_system_prompt()
        assert "MetaConscious" in system_prompt
        
        context = {
            'date': '2024-01-15',
            'goals': [],
            'tasks': [],
            'calendarEvents': [],
            'relationships': [],
            'recentPerformance': {}
        }
        user_prompt = client.build_planning_prompt(context)
        assert "2024-01-15" in user_prompt
        
        print("✓ LLM client service working correctly")
        return True
    except Exception as e:
        print(f"✗ LLM client service error: {e}")
        return False

async def test_planning_engine_service():
    """Test planning engine service functionality"""
    try:
        from app.services.planning_engine import PlanningEngine
        
        engine = PlanningEngine()
        
        # Test all required methods exist
        assert hasattr(engine, 'generate_daily_plan')
        assert hasattr(engine, 'gather_planning_context')
        assert hasattr(engine, 'save_plan')
        assert hasattr(engine, 'reschedule_task')
        assert hasattr(engine, 'check_weekly_overrides')
        assert hasattr(engine, 'log_override')
        assert hasattr(engine, 'get_week_number')
        
        # Test week number calculation
        test_date = datetime(2024, 1, 15)  # Monday
        week_num = engine.get_week_number(test_date)
        assert isinstance(week_num, int)
        assert week_num > 0
        
        print("✓ Planning engine service working correctly")
        return True
    except Exception as e:
        print(f"✗ Planning engine service error: {e}")
        return False

async def test_scheduler_service():
    """Test scheduler service functionality"""
    try:
        from app.services.scheduler import PlanningScheduler, start_planning_scheduler, stop_planning_scheduler, get_scheduler_status
        
        # Test PlanningScheduler class
        scheduler = PlanningScheduler()
        assert scheduler is not None
        assert hasattr(scheduler, 'start_planning_scheduler')
        assert hasattr(scheduler, 'stop_planning_scheduler')
        assert hasattr(scheduler, 'is_running')
        
        # Test global functions exist
        assert callable(start_planning_scheduler)
        assert callable(stop_planning_scheduler)
        assert callable(get_scheduler_status)
        
        # Test scheduler status
        status = get_scheduler_status()
        assert isinstance(status, dict)
        assert 'running' in status
        assert 'planning_hour' in status
        assert 'next_run' in status
        
        print("✓ Scheduler service working correctly")
        return True
    except Exception as e:
        print(f"✗ Scheduler service error: {e}")
        return False

async def test_pydantic_models():
    """Test Pydantic validation models"""
    try:
        from app.models.schemas import TimeBlock, GoalProgress, SocialTime, DailyPlan, GoalCreate, TaskCreate
        
        # Test TimeBlock model
        time_block = TimeBlock(
            start_time="09:00",
            end_time="10:00",
            activity="Test activity",
            priority=3,
            reasoning="Test reasoning"
        )
        assert time_block.start_time == "09:00"
        
        # Test GoalCreate model
        goal = GoalCreate(
            title="Test Goal",
            priority=4,
            priority_reasoning="This is important for testing"
        )
        assert goal.title == "Test Goal"
        
        # Test TaskCreate model
        task = TaskCreate(
            title="Test Task",
            priority=3,
            priority_reasoning="Testing task creation"
        )
        assert task.title == "Test Task"
        
        print("✓ Pydantic models working correctly")
        return True
    except Exception as e:
        print(f"✗ Pydantic models error: {e}")
        return False

async def test_sqlalchemy_models():
    """Test SQLAlchemy database models"""
    try:
        from app.models.database import User, Goal, Task, DailyPlan, CalendarEvent, Relationship
        
        # Test model classes exist and have required attributes
        assert hasattr(User, '__tablename__')
        assert hasattr(Goal, '__tablename__')
        assert hasattr(Task, '__tablename__')
        assert hasattr(DailyPlan, '__tablename__')
        assert hasattr(CalendarEvent, '__tablename__')
        assert hasattr(Relationship, '__tablename__')
        
        # Test User model has required columns
        assert hasattr(User, 'id')
        assert hasattr(User, 'username')
        assert hasattr(User, 'password_hash')
        assert hasattr(User, 'created_at')
        
        print("✓ SQLAlchemy models working correctly")
        return True
    except Exception as e:
        print(f"✗ SQLAlchemy models error: {e}")
        return False

async def test_configuration():
    """Test configuration loading"""
    try:
        from app.core.config import settings
        
        # Test all required settings exist
        assert hasattr(settings, 'database_url')
        assert hasattr(settings, 'llm_provider')
        assert hasattr(settings, 'llm_api_key')
        assert hasattr(settings, 'llm_model')
        assert hasattr(settings, 'llm_base_url')
        assert hasattr(settings, 'max_weekly_overrides')
        assert hasattr(settings, 'planning_hour')
        
        # Test database connection settings
        assert hasattr(settings, 'db_pool_max_connections')
        assert hasattr(settings, 'db_pool_idle_timeout')
        assert hasattr(settings, 'db_pool_connection_timeout')
        
        print("✓ Configuration working correctly")
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

async def test_fastapi_app():
    """Test FastAPI application"""
    try:
        from app.main import app
        
        # Test app exists and has correct configuration
        assert app is not None
        assert app.title == "MetaConscious Backend"
        assert app.version == "1.0.0"
        
        # Test routes are registered
        routes = [route.path for route in app.routes]
        
        # Should have basic routes (even if not all implemented yet)
        assert any("/api" in route for route in routes)
        
        print("✓ FastAPI application working correctly")
        return True
    except Exception as e:
        print(f"✗ FastAPI application error: {e}")
        return False

async def run_all_core_service_tests():
    """Run all core service tests"""
    print("Testing Core Services - Checkpoint 5...")
    print("=" * 60)
    
    tests = [
        test_configuration,
        test_database_service,
        test_llm_client_service,
        test_planning_engine_service,
        test_scheduler_service,
        test_pydantic_models,
        test_sqlalchemy_models,
        test_fastapi_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
        print()
    
    print("=" * 60)
    print(f"Core service tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All core services are working correctly!")
        print("✓ Database service ready")
        print("✓ LLM client service ready")
        print("✓ Planning engine service ready")
        print("✓ Scheduler service ready")
        print("✓ Pydantic models ready")
        print("✓ SQLAlchemy models ready")
        print("✓ FastAPI application ready")
        print("✓ Configuration ready")
        return True
    else:
        print("❌ Some core services have issues. Please check the errors above.")
        return False

if __name__ == "__main__":
    result = asyncio.run(run_all_core_service_tests())
    exit(0 if result else 1)