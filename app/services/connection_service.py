from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID
from datetime import datetime
import logging

from app.models.connection_models import DatabaseConnection, DatabaseConnectionCreate
from app.services.db_connector import test_connection, extract_database_schema
from app.services.metadata_extractor import save_schema_metadata, generate_embedding_texts
from app.services.embedder import batch_generate_and_store_embeddings

# Configure logging
logger = logging.getLogger(__name__)

async def create_db_connection(db: Session, connection_data: DatabaseConnectionCreate) -> Tuple[Optional[DatabaseConnection], str]:
    """
    Create a database connection and extract its schema.
    
    Args:
        db: Database session
        connection_data: Connection details
        
    Returns:
        Tuple of (connection object, message)
    """
    try:
        # Create connection record
        new_connection = DatabaseConnection(
            db_type=connection_data.db_type,
            host=connection_data.host,
            port=connection_data.port,
            database=connection_data.database,
            username=connection_data.username,
            password=connection_data.password,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
        # Test connection before saving
        is_valid, message = await test_connection(new_connection)
        if not is_valid:
            logger.warning(f"Connection test failed: {message}")
            return None, f"Failed to connect to database: {message}"
        
        # Save to database
        db.add(new_connection)
        db.commit()
        db.refresh(new_connection)
        
        logger.info(f"Created new database connection to {new_connection.db_type}://{new_connection.host}:{new_connection.port}/{new_connection.database}")
        return new_connection, "Connection created successfully"
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating database connection: {str(e)}")
        return None, f"Error creating connection: {str(e)}"

async def process_connection_schema(db: Session, connection: DatabaseConnection) -> str:
    """
    Process database schema extraction and embedding.
    
    Args:
        db: Database session
        connection: Database connection object
        
    Returns:
        Status message
    """
    try:
        logger.info(f"Starting schema extraction for connection {connection.id}")
        
        # 1. Extract raw schema metadata
        schema_metadata = await extract_database_schema(connection)
        logger.info(f"Extracted {len(schema_metadata)} schema items")
        
        # 2. Save schema metadata to database
        saved_metadata = await save_schema_metadata(db, connection.id, schema_metadata)
        logger.info(f"Saved {len(saved_metadata)} schema records")
        
        # 3. Generate embedding-ready texts
        embedding_texts = await generate_embedding_texts(schema_metadata)
        logger.info(f"Generated {len(embedding_texts)} embedding texts")
        
        # 4. Generate and store embeddings
        embeddings = await batch_generate_and_store_embeddings(db, connection.id, embedding_texts)
        logger.info(f"Generated and stored {len(embeddings)} embeddings")
        
        return "Schema processed successfully"
    except Exception as e:
        logger.error(f"Error processing schema: {str(e)}")
        # Delete the connection if metadata extraction fails
        try:
            db.delete(connection)
            db.commit()
            logger.info(f"Deleted connection {connection.id} due to schema processing failure")
        except Exception as delete_error:
            logger.error(f"Failed to delete connection after schema error: {str(delete_error)}")
            db.rollback()
        
        return f"Error processing schema: {str(e)}"

async def get_connection_by_id(db: Session, connection_id: UUID) -> Optional[DatabaseConnection]:
    """
    Get connection by ID.
    
    Args:
        db: Database session
        connection_id: UUID of the connection
        
    Returns:
        DatabaseConnection or None if not found
    """
    try:
        connection = db.query(DatabaseConnection).filter(DatabaseConnection.id == connection_id).first()
        return connection
    except Exception as e:
        logger.error(f"Error retrieving connection {connection_id}: {str(e)}")
        return None

async def get_all_connections(db: Session) -> List[DatabaseConnection]:
    """
    Get all connections.
    
    Args:
        db: Database session
        
    Returns:
        List of all database connections
    """
    try:
        return db.query(DatabaseConnection).all()
    except Exception as e:
        logger.error(f"Error retrieving all connections: {str(e)}")
        return [] 