"""
Test LLM client error handling and retry logic
"""
import asyncio
import os
from unittest.mock import patch, AsyncMock
from app.services.llm_client import LLMClient
from app.core.exceptions import LLMError

async def test_llm_retry_logic():
    """Test LLM retry logic with rate limit errors"""
    print("Testing LLM retry logic...")
    
    # Test with API key not configured
    with patch.dict(os.environ, {}, clear=True):
        llm_client = LLMClient()
        
        try:
            await llm_client.complete("system prompt", "user prompt")
            print("❌ Should have raised LLMError for missing API key")
        except LLMError as e:
            print(f"✓ LLM API key error handled: {e.message}")
    
    # Test with configured API key but simulated rate limit error
    with patch.dict(os.environ, {"LLM_API_KEY": "test_key"}):
        llm_client = LLMClient()
        
        # Mock litellm to raise rate limit errors
        with patch('litellm.acompletion') as mock_completion:
            # Simulate rate limit error that should be retried
            mock_completion.side_effect = Exception("Rate limit exceeded (429)")
            
            try:
                await llm_client.complete("system prompt", "user prompt")
                print("❌ Should have raised LLMError after retries")
            except LLMError as e:
                print(f"✓ LLM retry logic handled rate limit: {e.message}")
                print(f"✓ Retry count: {e.retry_count}")
    
    print("LLM error handling tests completed!")

async def test_llm_json_parsing():
    """Test LLM JSON parsing error handling"""
    print("Testing LLM JSON parsing...")
    
    with patch.dict(os.environ, {"LLM_API_KEY": "test_key"}):
        llm_client = LLMClient()
        
        # Mock successful API call but invalid JSON response
        with patch('litellm.acompletion') as mock_completion:
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = "invalid json response"
            mock_completion.return_value = mock_response
            
            try:
                await llm_client.generate_plan({"date": "2024-01-01"})
                print("❌ Should have raised LLMError for invalid JSON")
            except LLMError as e:
                print(f"✓ JSON parsing error handled: {e.message}")
    
    print("JSON parsing tests completed!")

if __name__ == "__main__":
    asyncio.run(test_llm_retry_logic())
    asyncio.run(test_llm_json_parsing())