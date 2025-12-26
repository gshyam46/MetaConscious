"""
Configuration management module
Handles environment variables and application settings
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# CRITICAL: Load .env file BEFORE creating Settings
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # Database configuration
    database_url: str = "postgresql://postgres:admin@localhost:5432/metaconscious"
    
    # LLM configuration
    llm_provider: str = "groq"
    llm_api_key: Optional[str] = None
    llm_model: str = "llama-3.3-70b-versatile"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    
    # System configuration
    max_weekly_overrides: int = 5
    planning_hour: int = 2
    
    # Database connection pool settings (matching Next.js)
    db_pool_max_connections: int = 20
    db_pool_idle_timeout: int = 30000  # milliseconds
    db_pool_connection_timeout: int = 2000  # milliseconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False

# Global settings instance
settings = Settings()

# Debug logging on import
import logging
logger = logging.getLogger(__name__)
logger.info("="*60)
logger.info("Configuration loaded:")
logger.info(f"  LLM Provider: {settings.llm_provider}")
logger.info(f"  LLM Model: {settings.llm_model}")
logger.info(f"  LLM API Key: {'SET' if settings.llm_api_key else 'NOT SET'}")
logger.info(f"  LLM Base URL: {settings.llm_base_url}")
logger.info("="*60)