from sqlmodel import Field, SQLModel
from typing import Optional, List
import uuid
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, FLOAT
import json

# raw schema metadata (tables, columns, etc.)
class TableSchema(SQLModel, table=True):
    __tablename__ = "table_schemas"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    db_id: uuid.UUID = Field(index=True)
    schema_name: str
    table_name: str
    column_name: str
    is_primary_key: Optional[bool] = False
    is_foreign_key: Optional[bool] = False
    foreign_table: Optional[str] = None
    foreign_column: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = Field(default=None)

# vector embeddings (semantic search)
class TableEmbedding(SQLModel, table=True):
    __tablename__ = "table_embeddings"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    db_id: uuid.UUID = Field(index=True)
    schema_name: str
    table_name: str
    column_name: Optional[str] = None
    description: str  # This is the textual data we embedded
    embedding_json: str  # Store embeddings as JSON string
    created_at: Optional[str] = Field(default=None)
    
    # Properties to convert between string and list
    @property
    def embedding(self) -> List[float]:
        """Convert JSON string to list of floats."""
        return json.loads(self.embedding_json) if self.embedding_json else []
        
    @embedding.setter
    def embedding(self, value: List[float]):
        """Convert list of floats to JSON string."""
        self.embedding_json = json.dumps(value) if value is not None else None