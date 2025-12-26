"""
System API endpoints
Status and initialization endpoints - identical to Next.js implementation
"""
from fastapi import APIRouter
from typing import Dict, Any, Optional
import hashlib
import os
import logging

from app.core.database import get_user, create_user, initialize_database
from app.core.exceptions import DatabaseError, SystemInitializationError
from app.models.schemas import UserCreate

router = APIRouter()
logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Hash password using SHA256 - identical to Next.js implementation"""
    return hashlib.sha256(password.encode()).hexdigest()

@router.get("/status")
async def get_status() -> Dict[str, Any]:
    """Get system status - identical to Next.js /api/status"""
    # Database errors are automatically handled by exception handlers
    # This matches Next.js behavior where database errors become 500 responses
    user = await get_user()
    
    # Check LLM connectivity if configured
    llm_status = "not_configured"
    if os.getenv("LLM_API_KEY"):
        try:
            from app.services.llm_client import LLMClient
            llm_client = LLMClient()
            # Simple test to verify LLM is working
            await llm_client.complete("You are a test.", "Respond with 'OK'", {"maxTokens": 10})
            llm_status = "working"
        except Exception as e:
            logger.warning(f"LLM connectivity test failed: {e}")
            llm_status = "error"
    
    # Return exact same format as Next.js with additional LLM status
    return {
        "status": "operational",
        "user": {
            "id": str(user["id"]),
            "username": user["username"]
        } if user else None,
        "llm_configured": bool(os.getenv("LLM_API_KEY")),
        "llm_status": llm_status
    }

@router.post("/init")
async def initialize_system(user_data: Optional[UserCreate] = None) -> Dict[str, Any]:
    """Initialize system with user - identical to Next.js /api/init"""
    # Check if user already exists
    existing_user = await get_user()
    if existing_user:
        # Return same response format as Next.js when user already exists
        return {
            "message": "User already initialized",
            "user": {
                "id": str(existing_user["id"]),
                "username": existing_user["username"]
            }
        }
    
    # Initialize database first - errors handled by exception handlers
    await initialize_database()
    
    # Use default values if no user data provided (matching Next.js behavior)
    username = user_data.username if user_data else "user"
    password = user_data.password if user_data else "password"
    
    # Hash password using same method as Next.js
    password_hash = hash_password(password)
    
    # Create user - database errors handled by exception handlers
    user = await create_user(username, password_hash)
    
    # Return same response format as Next.js
    return {
        "message": "User created",
        "user": {
            "id": str(user["id"]),
            "username": user["username"]
        }
    }