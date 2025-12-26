"""
Authentication utilities
Placeholder for authentication functions
"""
import hashlib
from typing import Optional

def hash_password(password: str) -> str:
    """Hash password - placeholder implementation"""
    # In production, use proper bcrypt or similar
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password - placeholder implementation"""
    # In production, use proper bcrypt verification
    return hash_password(password) == hashed_password