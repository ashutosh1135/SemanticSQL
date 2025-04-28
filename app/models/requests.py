from pydantic import BaseModel, Field
from typing import Optional

class DatabaseConnectionRequest(BaseModel):
    """Request model for database connection."""
    db_type: str = Field(..., description="Database type (e.g., mysql, postgres)")
    db_name: str = Field(..., description="Database name identifier")
    host: str = Field(..., description="Database host address")
    port: str = Field(..., description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")

class GenerateQueryRequest(BaseModel):
    """Request model for generating SQL query."""
    question: str = Field(..., description="Natural language question to convert to SQL")

class ExecuteQueryRequest(BaseModel):
    """Request model for executing SQL query."""
    sql: str = Field(..., description="SQL query to execute") 