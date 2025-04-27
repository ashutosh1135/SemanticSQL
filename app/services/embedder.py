from typing import List, Dict, Any
from datetime import datetime
import uuid
import json
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer

from app.models.schema_models import TableEmbedding
from app.config.config import settings

# Load the embedding model
_model = None

def get_embedding_model():
    """
    Loads and returns the embedding model (singleton pattern).
    
    Returns:
        SentenceTransformer model instance
    """
    global _model
    if _model is None:
        _model = SentenceTransformer('BAAI/bge-large-en-v1.5')
    return _model

async def generate_embeddings(text: str) -> List[float]:
    """
    Generates embeddings for the given text using a sentence transformer model.
    
    Args:
        text: The text to embed
        
    Returns:
        List of embedding values (vector)
    """
    model = get_embedding_model()
    embeddings = model.encode(text, normalize_embeddings=True)
    return embeddings.tolist()

async def store_embeddings(
    db_session: Session, 
    db_id: uuid.UUID, 
    schema_name: str, 
    table_name: str, 
    description: str, 
    embedding: List[float],
    column_name: str = None
) -> TableEmbedding:
    """
    Stores embeddings and metadata in the database.
    
    Args:
        db_session: Database session
        db_id: ID of the database connection
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

async def batch_generate_and_store_embeddings(
    db_session: Session,
    db_id: uuid.UUID,
    metadata_texts: List[Dict[str, Any]]
) -> List[TableEmbedding]:
    """
    Generates and stores embeddings for multiple schema objects at once.
    
    Args:
        db_session: Database session
        db_id: ID of the database connection
        metadata_texts: List of dictionaries with keys: schema_name, table_name, 
                        column_name (optional), description
        
    Returns:
        List of stored TableEmbedding objects
    """
    stored_embeddings = []
    
    for item in metadata_texts:
        embeddings = await generate_embeddings(item["description"])
        embedding_record = await store_embeddings(
            db_session=db_session,
            db_id=db_id,
            schema_name=item["schema_name"],
            table_name=item["table_name"],
            column_name=item.get("column_name"),
            description=item["description"],
            embedding=embeddings
        )
        stored_embeddings.append(embedding_record)
    
    return stored_embeddings
