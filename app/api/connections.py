from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime

from app.models.connection_models import DatabaseConnection, DatabaseConnectionCreate
from app.services.db_connector import test_connection, extract_database_schema
from app.services.metadata_extractor import save_schema_metadata, generate_embedding_texts
from app.services.embedder import batch_generate_and_store_embeddings
from app.config.config import settings
from app.db.database import get_db
from app.services.connection_service import create_db_connection, process_connection_schema, get_connection_by_id

router = APIRouter(
    prefix="/connections",
    tags=["connections"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def connect_database(
    connection_data: DatabaseConnectionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Connect to a database and extract its schema in the background.
    
    Args:
        connection_data: Connection details
        background_tasks: Background task manager
        db: Database session
    """
    connection, message = await create_db_connection(db, connection_data)
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    background_tasks.add_task(process_connection_schema, db, connection)
    
    return {
        "id": str(connection.id),
        "database": connection.database,
        "status": "connected",
        "message": "Connection created successfully. Schema processing started in background."
    }

@router.get("/", response_model=List[Dict[str, Any]])
async def list_connections(db: Session = Depends(get_db)):
    """
    List all database connections.
    
    Args:
        db: Database session
        
    Returns:
        List of connection details
    """
    connections = db.query(DatabaseConnection).all()
    result = []
    
    for connection in connections:
        # Count tables and columns
        schema_records = db.execute(
            "SELECT COUNT(DISTINCT table_name) as tables, COUNT(*) as columns FROM table_schemas WHERE db_id = :db_id",
            {"db_id": str(connection.id)}
        ).first()
        
        result.append({
            "id": str(connection.id),
            "db_type": connection.db_type,
            "host": connection.host,
            "database": connection.database,
            "metadata": {
                "tables_count": schema_records.tables if schema_records else 0,
                "columns_count": schema_records.columns if schema_records else 0
            },
            "created_at": connection.created_at
        })
    
    return result

@router.get("/{connection_id}", response_model=Dict[str, Any])
async def get_connection(connection_id: UUID, db: Session = Depends(get_db)):
    """
    Get a specific database connection details.
    
    Args:
        connection_id: UUID of the connection
        db: Database session
        
    Returns:
        Connection details
    """
    connection = db.query(DatabaseConnection).filter(DatabaseConnection.id == connection_id).first()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    schema_records = db.execute(
        "SELECT COUNT(DISTINCT table_name) as tables, COUNT(*) as columns FROM table_schemas WHERE db_id = :db_id",
        {"db_id": str(connection.id)}
    ).first()
    
    return {
        "id": str(connection.id),
        "db_type": connection.db_type,
        "host": connection.host,
        "port": connection.port,
        "database": connection.database,
        "username": connection.username,
        "created_at": connection.created_at,
        "updated_at": connection.updated_at,
        "metadata": {
            "tables_count": schema_records.tables if schema_records else 0,
            "columns_count": schema_records.columns if schema_records else 0
        }
    }

@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(connection_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a database connection and its metadata.
    
    Args:
        connection_id: UUID of the connection
        db: Database session
    """
    connection = db.query(DatabaseConnection).filter(DatabaseConnection.id == connection_id).first()
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    db.execute("DELETE FROM table_embeddings WHERE db_id = :db_id", {"db_id": str(connection_id)})
    db.execute("DELETE FROM table_schemas WHERE db_id = :db_id", {"db_id": str(connection_id)})
    db.delete(connection)
    db.commit()
    
    return None
