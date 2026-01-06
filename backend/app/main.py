"""
FastAPI MetaConscious Backend
Main application entry point
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import os
import logging
from dotenv import load_dotenv

from app.core.database import db_manager
from app.core.exceptions import (
    MetaConsciousException,
    SystemInitializationError,
    metaconscious_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from app.api.routes import goals, tasks, plans, calendar, relationships, system, chat, todos
from app.services.scheduler import start_planning_scheduler, stop_planning_scheduler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events with comprehensive error handling"""
    # Startup
    logger.info("Starting FastAPI MetaConscious Backend...")
    
    # Initialize database connection with proper error handling
    try:
        await db_manager.initialize_database()
        logger.info("✓ Database initialized successfully")
    except SystemInitializationError as e:
        logger.error(f"Database initialization failed: {e.message}")
        # Continue anyway - database might already be initialized
        # This matches Next.js behavior where initialization errors are logged but don't stop the server
    except Exception as e:
        logger.error(f"Unexpected database initialization error: {e}")
        # Continue anyway - database might already be initialized
    
    # Start planning scheduler with proper error handling
    try:
        await start_planning_scheduler()
        logger.info("✓ Planning scheduler started successfully")
    except Exception as e:
        logger.error(f"Planning scheduler startup failed: {e}")
        # Continue anyway - scheduler can be started manually if needed
        # This matches Next.js behavior where scheduler errors don't stop the server
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI MetaConscious Backend...")
    
    # Stop planning scheduler
    try:
        stop_planning_scheduler()
        logger.info("✓ Planning scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
    
    # Close database connections
    try:
        await db_manager.close()
        logger.info("✓ Database connections closed")
    except Exception as e:
        logger.error(f"Error during database shutdown: {e}")

# Create FastAPI application
app = FastAPI(
    title="MetaConscious Backend",
    description="Autonomous AI planning and productivity system backend",
    version="1.0.0",
    lifespan=lifespan
)

# Add exception handlers - identical error handling to Next.js
app.add_exception_handler(MetaConsciousException, metaconscious_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Configure CORS - identical to Next.js configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Match Next.js: Access-Control-Allow-Origin: '*'
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Match Next.js methods
    allow_headers=["Content-Type", "Authorization"],  # Match Next.js headers exactly
    expose_headers=["*"],  # Expose all headers
)

# Include API routes
app.include_router(system.router, prefix="/api", tags=["system"])
app.include_router(goals.router, prefix="/api", tags=["goals"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])
app.include_router(plans.router, prefix="/api", tags=["plans"])
app.include_router(calendar.router, prefix="/api", tags=["calendar"])
app.include_router(relationships.router, prefix="/api", tags=["relationships"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(todos.router, prefix="/api", tags=["todos"])

@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """
    Handle OPTIONS requests for CORS preflight
    Identical to Next.js OPTIONS handler
    """
    return {}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "MetaConscious FastAPI Backend", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    
    # Configure uvicorn server settings
    # Use environment variables for production deployment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True,
        # Use standard libraries for compatibility
        workers=1 if reload else int(os.getenv("WORKERS", "1")),
        loop="asyncio"
    )



