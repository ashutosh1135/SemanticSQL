from typing import List, Dict, Any, Optional
import uuid
import json
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime

from app.config.config import settings
from app.models.schema_models import TableEmbedding

async def create_vector_table(db_session: Session) -> bool:
    """
    Creates the table in the database to store vector embeddings if it doesn't exist.
    Also ensures the pgvector extension is enabled.
    
    Args:
        db_session: Database session
        
    Returns:
        Success status (True if created successfully)
    """
    try:
        # Enable pgvector extension if not already enabled
        db_session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        
        # Check if the table exists
        result = db_session.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'table_embeddings');"
        )).scalar()
        
        if not result:
            # Create the table manually if it doesn't exist
            db_session.execute(text("""
                CREATE TABLE table_embeddings (
                    id UUID PRIMARY KEY,
                    db_id UUID NOT NULL,
                    schema_name TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    column_name TEXT,
                    description TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    created_at TEXT
                );
                CREATE INDEX ON table_embeddings USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);
            """))
            
        db_session.commit()
        return True
    except Exception as e:
        db_session.rollback()
        raise Exception(f"Failed to create vector table: {str(e)}")

async def store_vector(
    db_session: Session, 
    db_id: uuid.UUID, 
    schema_name: str, 
    table_name: str, 
    description: str, 
    embedding: List[float],
    column_name: str = None
) -> TableEmbedding:
    """
    Stores a vector embedding and its associated metadata.
    
    Args:
        db_session: Database session
        db_id: Database connection ID
        schema_name: Schema name
        table_name: Table name
        description: Text description that was embedded
        embedding: Vector embedding
        column_name: Optional column name
        
    Returns:
        Stored TableEmbedding object
    """
    embedding_record = TableEmbedding(
        db_id=db_id,
        schema_name=schema_name,
        table_name=table_name,
        column_name=column_name,
        description=description,
        embedding_json=json.dumps(embedding),
        created_at=datetime.now().isoformat()
    )
    
    db_session.add(embedding_record)
    db_session.commit()
    db_session.refresh(embedding_record)
    
    return embedding_record

async def query_vector_store(
    db_session: Session, 
    query_embedding: List[float], 
    db_id: Optional[uuid.UUID] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Performs a simpler semantic search by calculating cosine similarity in Python.
    
    Args:
        db_session: Database session
        query_embedding: The embedding of the query text
        db_id: Optional filter by database ID
        limit: Number of results to return
        
    Returns:
        List of similar items with similarity scores
    """
    # Fetch all relevant embeddings
    query = "SELECT * FROM table_embeddings"
    params = {}
    
    if db_id:
        query += " WHERE db_id = :db_id"
        params["db_id"] = str(db_id)
    
    result = db_session.execute(text(query), params)
    
    # Convert to list of dicts
    records = []
    for row in result:
        embedding = json.loads(row.embedding_json)
        records.append({
            "id": row.id,
            "schema_name": row.schema_name,
            "table_name": row.table_name,
            "column_name": row.column_name,
            "description": row.description,
            "embedding": embedding,
        })
    
    # Calculate cosine similarity
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    
    if not records:
        return []
        
    embeddings = np.array([record["embedding"] for record in records])
    query_embedding_np = np.array(query_embedding).reshape(1, -1)
    
    similarities = cosine_similarity(embeddings, query_embedding_np).flatten()
    
    # Sort by similarity
    for i, similarity in enumerate(similarities):
        records[i]["similarity"] = float(similarity)
    
    records.sort(key=lambda x: x["similarity"], reverse=True)
    
    # Return top results
    return records[:limit]

async def get_table_context(
    db_session: Session,
    db_id: uuid.UUID,
    table_name: str,
    schema_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieves all embeddings related to a specific table.
    
    Args:
        db_session: Database session
        db_id: Database ID
        table_name: Table name
        schema_name: Optional schema name
        
    Returns:
        List of all embeddings for the specified table
    """
    query = """
        SELECT id, schema_name, table_name, column_name, description
        FROM table_embeddings
        WHERE db_id = :db_id AND table_name = :table_name
    """
    
    params = {
        "db_id": str(db_id),
        "table_name": table_name
    }
    
    if schema_name:
        query += " AND schema_name = :schema_name"
        params["schema_name"] = schema_name
    
    result = db_session.execute(text(query), params)
    
    # Format the results
    context = []
    for row in result:
        context.append({
            "id": row.id,
            "schema_name": row.schema_name,
            "table_name": row.table_name,
            "column_name": row.column_name,
            "description": row.description
        })
    
    return context
