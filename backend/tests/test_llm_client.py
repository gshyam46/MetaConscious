"""
Comprehensive test for LLM client functionality
Tests interface compatibility with Next.js version
"""
import sys
import os
import asyncio
import json
from unittest.mock import patch, AsyncMock

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

async def test_llm_client_interface():
    """Test LLM client has identical interface to Next.js version"""
    from app.services.llm_client import LLMClient
    
    client = LLMClient()
    
    # Test all required methods exist
    assert hasattr(client, 'complete'), "Missing complete method"
    assert hasattr(client, 'generate_plan'), "Missing generate_plan method"
    assert hasattr(client, 'get_planning_system_prompt'), "Missing get_planning_system_prompt method"
    assert hasattr(client, 'build_planning_prompt'), "Missing build_planning_prompt method"
    
    # Test all required attributes exist
    assert hasattr(client, 'provider'), "Missing provider attribute"
    assert hasattr(client, 'api_key'), "Missing api_key attribute"
    assert hasattr(client, 'model'), "Missing model attribute"
    assert hasattr(client, 'base_url'), "Missing base_url attribute"
    
    print("✓ LLM client interface matches Next.js version")
    return True

async def test_planning_prompts():
    """Test planning prompt generation matches Next.js version"""
    from app.services.llm_client import LLMClient
    
    client = LLMClient()
    
    # Test system prompt
    system_prompt = client.get_planning_system_prompt()
    
    # Verify key elements from Next.js version
    assert "MetaConscious" in system_prompt
    assert "FINAL AUTHORITY" in system_prompt
    assert "autonomous AI planning system" in system_prompt
    assert "Factual and confrontational" in system_prompt
    assert "Science-based, no generic motivation" in system_prompt
    assert "You MUST return valid JSON" in system_prompt
    
    # Verify JSON structure requirements
    assert '"date": "YYYY-MM-DD"' in system_prompt
    assert '"reasoning":' in system_prompt
    assert '"priority_analysis":' in system_prompt
    assert '"time_blocks":' in system_prompt
    assert '"social_time_allocation":' in system_prompt
    assert '"goal_progress_assessment":' in system_prompt
    assert '"warnings":' in system_prompt
    
    # Test user prompt building
    context = {
        'date': '2024-01-15',
        'goals': [{'id': 'goal1', 'title': 'Test Goal'}],
        'tasks': [{'id': 'task1', 'title': 'Test Task'}],
        'calendarEvents': [{'id': 'event1', 'title': 'Meeting'}],
        'relationships': [{'name': 'John', 'time_budget': 60}],
        'recentPerformance': {'completed_tasks': 5}
    }
    
    user_prompt = client.build_planning_prompt(context)
    
    # Verify all context sections are included
    assert "DATE: 2024-01-15" in user_prompt
    assert "ACTIVE GOALS:" in user_prompt
    assert "PENDING TASKS:" in user_prompt
    assert "CALENDAR EVENTS (TOMORROW):" in user_prompt
    assert "RELATIONSHIPS & TIME BUDGETS:" in user_prompt
    assert "RECENT PERFORMANCE:" in user_prompt
    assert "CONSTRAINTS:" in user_prompt
    
    # Verify constraints match Next.js version
    assert "Max 3-5 active goals" in user_prompt
    assert "Social time has hard cap" in user_prompt
    assert "Everything is a trade-off" in user_prompt
    assert "No non-negotiables" in user_prompt
    
    print("✓ Planning prompts match Next.js version exactly")
    return True

async def test_complete_method_signature():
    """Test complete method has correct signature and error handling"""
    from app.services.llm_client import LLMClient
    
    client = LLMClient()
    
    # Test method without API key raises correct error
    try:
        await client.complete("system", "user")
        assert False, "Should have raised exception for missing API key"
    except Exception as e:
        assert "LLM_API_KEY not configured" in str(e)
    
    print("✓ Complete method signature and error handling correct")
    return True

async def test_generate_plan_method():
    """Test generate_plan method behavior"""
    from app.services.llm_client import LLMClient
    
    client = LLMClient()
    
    context = {
        'date': '2024-01-15',
        'goals': [],
        'tasks': [],
        'calendarEvents': [],
        'relationships': [],
        'recentPerformance': {}
    }
    
    # Test method without API key raises correct error
    try:
        await client.generate_plan(context)
        assert False, "Should have raised exception for missing API key"
    except Exception as e:
        assert "LLM_API_KEY not configured" in str(e)
    
    print("✓ Generate plan method behavior correct")
    return True

async def test_configuration_loading():
    """Test configuration loading matches Next.js defaults"""
    from app.services.llm_client import LLMClient
    
    client = LLMClient()
    
    # Test default values match Next.js
    assert client.model == "mixtral-8x7b-32768", f"Expected mixtral-8x7b-32768, got {client.model}"
    assert client.base_url == "https://api.groq.com/openai/v1", f"Expected Groq URL, got {client.base_url}"
    
    print("✓ Configuration loading matches Next.js defaults")
    return True

async def test_json_parsing_error_handling():
    """Test JSON parsing error handling in generate_plan"""
    from app.services.llm_client import LLMClient
    
    # Mock the complete method to return invalid JSON
    with patch.object(LLMClient, 'complete', new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = "invalid json response"
        
        client = LLMClient()
        context = {'date': '2024-01-15'}
        
        try:
            await client.generate_plan(context)
            assert False, "Should have raised exception for invalid JSON"
        except Exception as e:
            assert "LLM returned invalid JSON" in str(e)
    
    print("✓ JSON parsing error handling correct")
    return True

async def run_all_tests():
    """Run all LLM client tests"""
    print("Testing LLM Client Implementation...")
    print("=" * 50)
    
    tests = [
        test_llm_client_interface,
        test_planning_prompts,
        test_complete_method_signature,
        test_generate_plan_method,
        test_configuration_loading,
        test_json_parsing_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed: {e}")
        print()
    
    print("=" * 50)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All LLM client tests passed! Implementation matches Next.js version.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    result = asyncio.run(run_all_tests())
    exit(0 if result else 1)