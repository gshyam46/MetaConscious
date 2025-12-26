"""
Custom exceptions and error handling for FastAPI backend
Matches Next.js error handling patterns exactly
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import traceback

logger = logging.getLogger(__name__)

class MetaConsciousException(Exception):
    """Base exception for MetaConscious application"""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class DatabaseError(MetaConsciousException):
    """Database operation errors"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.original_error = original_error
        super().__init__(message, status_code=500)

class LLMError(MetaConsciousException):
    """LLM API errors"""
    
    def __init__(self, message: str, original_error: Optional[Exception] = None, retry_count: int = 0):
        self.original_error = original_error
        self.retry_count = retry_count
        super().__init__(message, status_code=500)

class ValidationError(MetaConsciousException):
    """Input validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(message, status_code=400)

class AuthenticationError(MetaConsciousException):
    """Authentication errors"""
    
    def __init__(self, message: str = "User not initialized. Call /api/init first"):
        super().__init__(message, status_code=401)

class NotFoundError(MetaConsciousException):
    """Resource not found errors"""
    
    def __init__(self, message: str = "Not found"):
        super().__init__(message, status_code=404)

class OverrideLimitError(MetaConsciousException):
    """Weekly override limit exceeded"""
    
    def __init__(self, message: str, override_status: Dict[str, Any]):
        self.override_status = override_status
        super().__init__(message, status_code=403, details={"overrides": override_status})

class SystemInitializationError(MetaConsciousException):
    """System initialization errors"""
    
    def __init__(self, message: str, component: str, original_error: Optional[Exception] = None):
        self.component = component
        self.original_error = original_error
        super().__init__(message, status_code=500)

# CORS headers function - identical to Next.js
def get_cors_headers() -> Dict[str, str]:
    """Get CORS headers identical to Next.js implementation"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    }

# Exception handlers
async def metaconscious_exception_handler(request: Request, exc: MetaConsciousException) -> JSONResponse:
    """Handle MetaConscious custom exceptions"""
    logger.error(f"MetaConscious error: {exc.message}")
    
    response_data = {"error": exc.message}
    if exc.details:
        response_data.update(exc.details)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=get_cors_headers()
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors - match Next.js format"""
    logger.error(f"Validation error: {exc.errors()}")
    
    # Format validation errors to match Next.js style
    error_messages = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        error_messages.append(f"{field}: {message}")
    
    return JSONResponse(
        status_code=400,
        content={"error": "; ".join(error_messages)},
        headers=get_cors_headers()
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    
    # Handle different HTTP exception formats
    if isinstance(exc.detail, dict):
        content = exc.detail
    else:
        content = {"error": exc.detail}
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=get_cors_headers()
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions - identical to Next.js 500 errors"""
    logger.error(f"Unexpected error: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)},
        headers=get_cors_headers()
    )