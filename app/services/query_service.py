from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID
import sqlalchemy
import logging

from app.services.query_generator import generate_query_from_search
from app.services.db_connector import get_connection
from app.models.connection_models import DatabaseConnection
from app.utils.db_utils import create_connection_string

# Configure logging
logger = logging.getLogger(__name__)

async def generate_sql(db: Session, user_query: str, connection_id: UUID) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Generate SQL from natural language query.
    
    Args:
        db: Database session
        user_query: Natural language query
        connection_id: Connection ID
        
    Returns:
        Tuple of (SQL query, relevant schema)
    """
    try:
        return await generate_query_from_search(
            user_query=user_query,
            db_session=db,
            db_id=connection_id
        )
    except Exception as e:
        logger.error(f"SQL generation error: {str(e)}")
        return f"/* Error generating SQL: {str(e)} */", []

async def execute_sql(connection: DatabaseConnection, sql: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Execute SQL query against database.
    
    Args:
        connection: Database connection
        sql: SQL query to execute
        parameters: Optional query parameters
        
    Returns:
        Query results
    """
    # Create connection string
    conn_string = await create_connection_string(
        connection.db_type,
        connection.username,
        connection.password,
        connection.host,
        connection.port,
        connection.database
    )
    
    # Use context manager for safe connection handling
    try:
        with get_connection(conn_string) as conn:
            if parameters:
                result = conn.execute(sqlalchemy.text(sql), parameters)
            else:
                result = conn.execute(sqlalchemy.text(sql))
            
            # For SELECT queries, fetch results
            if sql.strip().lower().startswith("select"):
                columns = result.keys()
                rows = result.fetchall()
                
                # Convert to list of dicts
                data = [dict(zip(columns, row)) for row in rows]
                
                return {
                    "success": True,
                    "rows_affected": len(data),
                    "data": data[:100],
                    "has_more": len(data) > 100
                }
            # For non-SELECT queries
            else:
                return {
                    "success": True,
                    "rows_affected": result.rowcount,
                    "data": None
                }
    except Exception as e:
        logger.error(f"SQL execution error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "sql": sql
        } 