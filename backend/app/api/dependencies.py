"""
Shared API dependencies
Authentication and common utilities
"""
from fastapi import Depends
from typing import Dict, Any

from app.core.database import get_user
from app.core.exceptions import AuthenticationError

async def get_current_user() -> Dict[str, Any]:
    """
    Get current user dependency
    Implements same single-user authentication logic as Next.js
    """
    user = await get_user()
    if not user:
        # Use custom exception with identical message to Next.js
        raise AuthenticationError("User not initialized. Call /api/init first")
    return user