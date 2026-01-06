"""
Database connection and utilities module
Implements identical functionality to Next.js db.js
"""
import asyncpg
import asyncio
import os
from typing import List, Dict, Optional, Any
from contextlib import asynccontextmanager
import logging

from .config import settings
from .exceptions import DatabaseError, SystemInitializationError

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager with connection pooling - identical to Next.js implementation"""
    
    def __init__(self):
        self._pool: Optional[asyncpg.Pool] = None
    
    async def get_pool(self) -> asyncpg.Pool:
        """Get database connection pool with same parameters as Next.js"""
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    settings.database_url,
                    max_size=settings.db_pool_max_connections,  # max: 20
                    max_inactive_connection_lifetime=settings.db_pool_idle_timeout / 1000,  # 30 seconds
                    command_timeout=settings.db_pool_connection_timeout / 1000,  # 2 seconds
                )
                logger.info("Database connection pool created successfully")
                
                # Set up error handler identical to Next.js
                def on_pool_error(connection, error):
                    logger.error(f"Unexpected error on idle client: {error}")
                
            except asyncpg.PostgresError as error:
                logger.error(f"PostgreSQL error creating database pool: {error}")
                raise DatabaseError(f"Database connection failed: {str(error)}", error)
            except Exception as error:
                logger.error(f"Unexpected error creating database pool: {error}")
                raise DatabaseError(f"Unexpected database error: {str(error)}", error)
        
        return self._pool
    
    async def query(self, text: str, params: List[Any] = None) -> List[Dict[str, Any]]:
        """Execute database query - identical interface to Next.js query function"""
        try:
            pool = await self.get_pool()
            
            async with pool.acquire() as connection:
                if params is None:
                    params = []
                
                result = await connection.fetch(text, *params)
                
                # Convert asyncpg.Record to dict (matching Next.js result.rows format)
                return [dict(record) for record in result]
                
        except asyncpg.PostgresError as error:
            logger.error(f"Database query error: {error}")
            # Re-raise as DatabaseError with same message format as Next.js
            raise DatabaseError(f"Database query error: {str(error)}", error)
        except Exception as error:
            logger.error(f"Database query error: {error}")
            raise DatabaseError(f"Database query error: {str(error)}", error)
    
    async def query_one(self, text: str, params: List[Any] = None) -> Optional[Dict[str, Any]]:
        """Execute query and return single result"""
        results = await self.query(text, params)
        return results[0] if results else None
    
    async def execute(self, text: str, params: List[Any] = None) -> str:
        """Execute query without returning results (for INSERT/UPDATE/DELETE)"""
        try:
            pool = await self.get_pool()
            
            async with pool.acquire() as connection:
                if params is None:
                    params = []
                
                result = await connection.execute(text, *params)
                return result
                
        except asyncpg.PostgresError as error:
            logger.error(f"Database execute error: {error}")
            raise DatabaseError(f"Database execute error: {str(error)}", error)
        except Exception as error:
            logger.error(f"Database execute error: {error}")
            raise DatabaseError(f"Database execute error: {str(error)}", error)
    
    async def initialize_database(self) -> bool:
        """Initialize database with schema.sql - identical to Next.js initializeDatabase"""
        try:
            # Read schema.sql file from the backend directory
            # Try different possible paths based on where the script is run from
            possible_paths = [
                os.path.join(os.getcwd(), 'schema.sql'),  # From backend directory
                os.path.join(os.path.dirname(__file__), '..', '..', 'schema.sql'),  # From backend/app/core
                os.path.join(os.getcwd(), 'backend', 'schema.sql'),  # From root
            ]
            
            schema_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    schema_path = path
                    break
            
            if not schema_path:
                raise SystemInitializationError(
                    "Could not find schema.sql file", 
                    "database", 
                    FileNotFoundError("schema.sql not found")
                )
            
            with open(schema_path, 'r', encoding='utf-8') as file:
                schema = file.read()
            
            # Execute schema using execute method for multiple statements
            # Split schema into individual statements to handle "already exists" errors gracefully
            statements = [stmt.strip() for stmt in schema.split(';') if stmt.strip()]
            
            pool = await self.get_pool()
            async with pool.acquire() as connection:
                for statement in statements:
                    try:
                        await connection.execute(statement)
                    except asyncpg.PostgresError as error:
                        # Ignore "already exists" errors for tables and indexes - identical to Next.js
                        error_msg = str(error).lower()
                        if any(phrase in error_msg for phrase in [
                            'already exists',
                            'relation already exists',
                            'index already exists'
                        ]):
                            logger.info(f"Skipping existing database object: {error}")
                            continue
                        else:
                            # Re-raise other PostgreSQL errors
                            raise DatabaseError(f"Database initialization error: {str(error)}", error)
                    except Exception as error:
                        # Re-raise other errors
                        raise SystemInitializationError(
                            f"Error initializing database: {str(error)}", 
                            "database", 
                            error
                        )
            
            logger.info("Database initialized successfully")
            return True
            
        except (SystemInitializationError, DatabaseError):
            # Re-raise our custom errors
            raise
        except Exception as error:
            logger.error(f"Error initializing database: {error}")
            raise SystemInitializationError(
                f"Error initializing database: {str(error)}", 
                "database", 
                error
            )
    
    async def get_user(self) -> Optional[Dict[str, Any]]:
        """Get single user - identical to Next.js getUser function"""
        result = await self.query_one('SELECT * FROM users LIMIT 1', [])
        return result
    
    async def create_user(self, username: str, password_hash: str) -> Dict[str, Any]:
        """Create new user - identical to Next.js createUser function"""
        result = await self.query(
            'INSERT INTO users (username, password_hash) VALUES ($1, $2) RETURNING *',
            [username, password_hash]
        )
        return result[0]
    
    async def close(self):
        """Close database connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed")

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions matching Next.js exports
async def query(text: str, params: List[Any] = None) -> List[Dict[str, Any]]:
    """Global query function - matches Next.js export"""
    return await db_manager.query(text, params)

async def get_user() -> Optional[Dict[str, Any]]:
    """Global get_user function - matches Next.js export"""
    return await db_manager.get_user()

async def create_user(username: str, password_hash: str) -> Dict[str, Any]:
    """Global create_user function - matches Next.js export"""
    return await db_manager.create_user(username, password_hash)

async def initialize_database() -> bool:
    """Global initialize_database function - matches Next.js export"""
    return await db_manager.initialize_database()