"""
Add this to your plans.py router for testing the LLM connection
"""

@router.post("/test-llm")
async def test_llm() -> Dict[str, Any]:
    """
    Test LLM connection without authentication
    This endpoint is for debugging only - remove in production
    """
    import os
    from app.services.llm_client import LLMClient
    
    # Check environment variables
    provider = os.getenv("LLM_PROVIDER")
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL")
    base_url = os.getenv("LLM_BASE_URL")
    
    logger.info(f"Environment check:")
    logger.info(f"  LLM_PROVIDER: {provider}")
    logger.info(f"  LLM_API_KEY: {'Set' if api_key else 'NOT SET'}")
    logger.info(f"  LLM_MODEL: {model}")
    logger.info(f"  LLM_BASE_URL: {base_url}")
    
    if not api_key:
        return {
            "error": "LLM_API_KEY not set in environment",
            "provider": provider,
            "model": model,
            "base_url": base_url
        }
    
    try:
        # Initialize LLM client
        llm = LLMClient()
        
        # CRITICAL DEBUG INFO
        logger.info("="*60)
        logger.info("LLM CLIENT DEBUG INFO")
        logger.info(f"  Provider: {llm.provider}")
        logger.info(f"  Base Model: {llm.base_model}")
        logger.info(f"  Formatted Model: {llm.model}")
        logger.info(f"  Has '/' in model: {'/' in llm.model}")
        logger.info(f"  API Key Length: {len(llm.api_key) if llm.api_key else 0}")
        
        # Check environment variables
        import os
        groq_key = os.environ.get("GROQ_API_KEY")
        logger.info(f"  GROQ_API_KEY in env: {'Set' if groq_key else 'NOT SET'}")
        if groq_key:
            logger.info(f"  GROQ_API_KEY prefix: {groq_key[:10]}...")
        logger.info("="*60)
        
        # Make a simple test call
        response = await llm.complete(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say 'Hello, LLM is working!' and nothing else.",
            options={"temperature": 0.1, "maxTokens": 50}
        )
        
        return {
            "success": True,
            "provider": llm.provider,
            "model": llm.model,
            "response": response,
            "formatted_model": llm.model,
            "env_check": {
                "LLM_PROVIDER": provider,
                "LLM_MODEL": model,
                "LLM_API_KEY": f"{api_key[:10]}..." if api_key else None
            }
        }
        
    except Exception as error:
        logger.error(f"LLM test failed: {error}")
        import traceback
        return {
            "success": False,
            "error": str(error),
            "error_type": type(error).__name__,
            "traceback": traceback.format_exc(),
            "provider": provider,
            "model": model
        }