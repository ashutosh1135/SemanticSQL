from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class DatabaseConnectionResponse(BaseModel):
    """Response model for database connection."""
    message: str = Field(..., description="Connection status message")
    connection_id: str = Field(..., description="Unique identifier for the connection")

class DatabaseConnection(BaseModel):
    """Model for a database connection."""
    connection_id: str = Field(..., description="Unique identifier for the connection")
    db_type: str = Field(..., description="Database type")
    db_name: str = Field(..., description="Database name identifier")
    host: str = Field(..., description="Database host address")
    port: str = Field(..., description="Database port")
    database: str = Field(..., description="Database name")

class ListConnectionsResponse(BaseModel):
    """Response model for listing database connections."""
    connections: List[DatabaseConnection] = Field(..., description="List of database connections")

class GenerateQueryResponse(BaseModel):
    """Response model for generating SQL query."""
    query: str = Field(..., description="Generated SQL query")

class ExecuteQueryResponse(BaseModel):
    """Response model for executing SQL query."""
    results: List[Dict[str, Any]] = Field(..., description="Query results as a list of dictionaries")

class ErrorResponse(BaseModel):
    """Response model for errors."""
    detail: str = Field(..., description="Error message") 