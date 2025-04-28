from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.services.database_service import DatabaseService
from app.services.background_service import BackgroundService
from app.services.query_service import QueryService
from app.models.requests import (
    DatabaseConnectionRequest,
    GenerateQueryRequest,
    ExecuteQueryRequest
)
from app.models.responses import (
    DatabaseConnectionResponse,
    ListConnectionsResponse,
    GenerateQueryResponse,
    ExecuteQueryResponse,
    ErrorResponse
)
import logging
import traceback
import json
from pathlib import Path
import re

logger = logging.getLogger("semanticsql")

router = APIRouter(
    prefix="/api",
    responses={400: {"model": ErrorResponse}}
)

# Initialize services
db_service = DatabaseService()
background_service = BackgroundService(db_service)
query_service = QueryService(db_service)

@router.post("/connect", response_model=DatabaseConnectionResponse)
async def connect_database(request: DatabaseConnectionRequest):
    """Connect to a database."""
    try:
        # Log the connection request (excluding password)
        safe_request = request.dict()
        safe_request["password"] = "***MASKED***"
        logger.info(f"Received connection request: {json.dumps(safe_request)}")
        
        # Connect to database
        connection = await db_service.connect(request)
        
        # Start background tasks
        await background_service.start_schema_exploration(connection["connection_id"])
        
        return DatabaseConnectionResponse(
            message="Database connected successfully",
            connection_id=connection["connection_id"]
        )
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/connections", response_model=ListConnectionsResponse)
async def list_connections():
    """List all database connections."""
    try:
        connections = await db_service.list_connections()
        logger.info(f"Listed {len(connections)} connections")
        return ListConnectionsResponse(connections=connections)
    except Exception as e:
        logger.error(f"Error listing connections: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/generate-query", response_model=GenerateQueryResponse)
async def generate_sql_query(request: GenerateQueryRequest):
    """Generate SQL query from natural language."""
    try:
        # Log the incoming request
        logger.info(f"Received query generation request: {request.question}")
        
        # Generate query using actual database tables
        sql_query = await query_service.generate_sql_query(request.question)
        logger.info(f"Generated SQL query: {sql_query}")
        
        return GenerateQueryResponse(query=sql_query)
    except Exception as e:
        logger.error(f"Error generating SQL query: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/execute-query", response_model=ExecuteQueryResponse)
async def execute_query(request: ExecuteQueryRequest):
    """Execute SQL query."""
    try:
        # Log the incoming request
        logger.info(f"Received query execution request: {request.sql}")
        
        # Get active connections for execution (this step needs a connection)
        connections = await db_service.list_connections()
        if not connections:
            logger.error("No active database connections found")
            raise HTTPException(status_code=400, detail="No active database connection found for execution")
        
        # Use the first active connection
        connection = connections[0]
        logger.info(f"Using connection: {connection.connection_id}")
        
        # Execute query
        try:
            results = await query_service.execute_query(connection.connection_id, request.sql)
            logger.info(f"Query executed successfully, returned {len(results)} rows")
            return ExecuteQueryResponse(results=results)
        except Exception as e:
            error_msg = str(e)
            # Extract the table that doesn't exist from the error message
            if "Table" in error_msg and "doesn't exist" in error_msg:
                import re
                table_match = re.search(r"Table '.*?\.([^']+)'", error_msg)
                non_existent_table = table_match.group(1) if table_match else "unknown"
                
                # Get the actual tables that do exist
                if connection.connection_id in db_service.engines:
                    engine = db_service.engines[connection.connection_id]
                    from sqlalchemy import inspect
                    actual_tables = inspect(engine).get_table_names()
                    
                    error_detail = {
                        "error": f"Table '{non_existent_table}' doesn't exist",
                        "available_tables": actual_tables,
                        "message": "Please modify your query to use only the available tables."
                    }
                else:
                    error_detail = {"error": error_msg}
                
                raise HTTPException(status_code=400, detail=error_detail)
            else:
                raise HTTPException(status_code=400, detail=error_msg)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=str(e)) 