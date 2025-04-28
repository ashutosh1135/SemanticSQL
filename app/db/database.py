from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.config.config import settings
import logging

logger = logging.getLogger("semanticsql")

# Initialize Qdrant client
qdrant_client = QdrantClient(
    host=settings.QDRANT_HOST,
    port=settings.QDRANT_PORT
)

async def create_db_and_tables():
    """Initialize Qdrant collection."""
    try:
        # Create collection if it doesn't exist
        collections = qdrant_client.get_collections().collections
        collection_names = [collection.name for collection in collections]
        
        if settings.QDRANT_COLLECTION not in collection_names:
            qdrant_client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=models.VectorParams(
                    size=1536,  # Size of Gemini embeddings
                    distance=models.Distance.COSINE
                )
            )
            logger.info(f"Created Qdrant collection: {settings.QDRANT_COLLECTION}")
        else:
            logger.info(f"Using existing Qdrant collection: {settings.QDRANT_COLLECTION}")
            
    except Exception as e:
        logger.error(f"Qdrant initialization error: {e}")
        raise 