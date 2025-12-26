"""
Integration test for LLM client usage in other modules
"""
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_llm_client_import_from_services():
    """Test LLM client can be imported from services module"""
    try:
        from app.services import LLMClient
        
        client = LLMClient()
        assert client is not None
        
        print("✓ LLM client can be imported from services module")
        return True
    except Exception as e:
        print(f"✗ Import from services failed: {e}")
        return False

def test_llm_client_direct_import():
    """Test LLM client can be imported directly"""
    try:
        from app.services.llm_client import LLMClient
        
        client = LLMClient()
        assert client is not None
        
        print("✓ LLM client can be imported directly")
        return True
    except Exception as e:
        print(f"✗ Direct import failed: {e}")
        return False

def test_configuration_consistency():
    """Test configuration is consistent across imports"""
    try:
        from app.services.llm_client import LLMClient
        from app.core.config import settings
        
        client = LLMClient()
        
        # Verify client uses settings correctly
        assert client.provider == settings.llm_provider
        assert client.api_key == settings.llm_api_key
        assert client.model == settings.llm_model
        assert client.base_url == settings.llm_base_url
        
        print("✓ Configuration is consistent")
        return True
    except Exception as e:
        print(f"✗ Configuration consistency failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing LLM Client Integration...")
    print("=" * 40)
    
    tests = [
        test_llm_client_import_from_services,
        test_llm_client_direct_import,
        test_configuration_consistency
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Integration tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 LLM client integration successful!")
        exit(0)
    else:
        print("❌ Some integration tests failed.")
        exit(1)