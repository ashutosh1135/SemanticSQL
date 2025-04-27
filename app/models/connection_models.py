from sqlmodel import SQLModel, Field
from typing import Optional
import uuid

# full model mapped to database
class DatabaseConnection(SQLModel, table=True):
    __tablename__ = "database_connections"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    db_type: str = Field(..., description="Database type")
    host: str
    port: str
    database: str
    username: str
    password: str
    created_at: Optional[str] = Field(default=None)
    updated_at: Optional[str] = Field(default=None)
    
# used for api 
class DatabaseConnectionCreate(SQLModel):
    db_type: str
    host: str
    port: str
    database: str
    username: str
    password: str
