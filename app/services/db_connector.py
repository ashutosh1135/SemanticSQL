from sqlalchemy import create_engine, inspect
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session
from typing import List, Dict, Any, Tuple, Optional, Generator
from contextlib import contextmanager
import logging

from app.utils.db_utils import create_connection_string, get_schema_metadata
from app.models.connection_models import DatabaseConnection

# Configure logging
logger = logging.getLogger(__name__)

# Dictionary to store connection pools
connection_pools = {}

def get_or_create_engine(connection_string: str, pool_size: int = 5, max_overflow: int = 10):
    """
    Get or create a SQLAlchemy engine with connection pooling.
    
    Args:
        connection_string: The SQLAlchemy connection string
        pool_size: The size of the connection pool
        max_overflow: The maximum overflow of the pool
        
    Returns:
        Engine instance with connection pooling
    """
    if connection_string not in connection_pools:
        logger.info(f"Creating new connection pool for {connection_string.split('@')[1] if '@' in connection_string else 'database'}")
        engine = create_engine(
            connection_string,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=3600,
            pool_pre_ping=True,
            poolclass=QueuePool
        )
        connection_pools[connection_string] = engine
    
    return connection_pools[connection_string]

@contextmanager
def get_connection(connection_string: str):
    """
    Contextmanager for database connections.
    
    Args:
        connection_string: The SQLAlchemy connection string
        
    Yields:
        Database connection
    """
    engine = get_or_create_engine(connection_string)
    connection = engine.connect()
    try:
        yield connection
        connection.commit()
    except Exception as e:
        connection.rollback()
        logger.error(f"Database connection error: {str(e)}")
        raise
    finally:
        connection.close()

async def test_connection(connection: DatabaseConnection) -> Tuple[bool, str]:
    """
    Tests if the connection to the database works.
    
    Args:
        connection: DatabaseConnection object with connection details
        
    Returns:
        Tuple of (success_status, message)
    """
    try:
        conn_string = await create_connection_string(
            connection.db_type,
            connection.username,
            connection.password,
            connection.host,
            connection.port,
            connection.database
        )
        
        with get_connection(conn_string) as conn:
            conn.execute("SELECT 1")
            
        return True, "Connection successful"
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return False, f"Connection failed: {str(e)}"

@contextmanager
def get_db_session(connection_string: str) -> Generator[Session, None, None]:
    """
    Creates and returns a database session.
    
    Args:
        connection_string: The connection string
        
    Yields:
        SQLAlchemy session object
    """
    engine = get_or_create_engine(connection_string)
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_local()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()

async def extract_database_schema(connection: DatabaseConnection) -> List[Dict]:
    """
    Extracts the full database schema from the connected database.
    
    Args:
        connection: DatabaseConnection model object
        
    Returns:
        List of dictionaries containing schema metadata
    """
    conn_string = await create_connection_string(
        connection.db_type,
        connection.username,
        connection.password,
        connection.host,
        connection.port,
        connection.database
    )
    
    try:
        metadata = await get_schema_metadata(conn_string)
        return metadata
    except Exception as e:
        logger.error(f"Failed to extract database schema: {str(e)}")
        raise
