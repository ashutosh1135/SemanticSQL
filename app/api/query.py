from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime

from app.services.query_service import generate_sql, execute_sql
from app.services.connection_service import get_connection_by_id
from app.db.database import get_db

router = APIRouter(
    prefix="/queries",
    tags=["queries"],
    responses={404: {"description": "Not found"}},
)

class NaturalLanguageQuery(BaseModel):
    """Natural language query request model."""
    query: str
    connection_id: UUID

class SQLExecuteRequest(BaseModel):
    """SQL execution request model."""
    sql: str
    connection_id: UUID
    parameters: Optional[Dict[str, Any]] = None

@router.post("/generate", response_model=Dict[str, Any])
async def generate_sql_query(
    query_data: NaturalLanguageQuery,
    db: Session = Depends(get_db)
):
    """Generate SQL query from natural language."""
    # Check if connection exists
    connection = await get_connection_by_id(db, query_data.connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Generate SQL from natural language
    sql_query, relevant_schema = await generate_sql(
        db=db,
        user_query=query_data.query,
        connection_id=query_data.connection_id
    )
    
    # Get unique tables from results
    relevant_tables = set()
    for item in relevant_schema:
        relevant_tables.add(f"{item['schema_name']}.{item['table_name']}")
    
    return {
        "query": query_data.query,
        "sql": sql_query,
        "tables": list(relevant_tables),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/execute", response_model=Dict[str, Any])
async def execute_sql_query(
    query_data: SQLExecuteRequest,
    db: Session = Depends(get_db)
):
    """Execute SQL query on database."""
    # Check if connection exists
    connection = await get_connection_by_id(db, query_data.connection_id)
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    try:
        # Execute query
        result = await execute_sql(
            connection=connection,
            sql=query_data.sql,
            parameters=query_data.parameters
        )
        
        # Add timestamp
        result["timestamp"] = datetime.now().isoformat()
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error executing SQL: {str(e)}"
        )
