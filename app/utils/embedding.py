from typing import List, Optional
from qdrant_client import models
from app.db.database import qdrant_client
from app.config.config import settings
from app.utils.llm import embeddings_model
import logging

logger = logging.getLogger("semanticsql")

def create_embeddings(texts: List[str]) -> List[List[float]]:
    """Create embeddings for a list of texts."""
    try:
        embeddings = embeddings_model.embed_documents(texts)
        return embeddings
    except Exception as e:
        logger.error(f"Error creating embeddings: {e}")
        raise

def store_embeddings(collection_name: str, texts: List[str], metadata: Optional[List[dict]] = None) -> None:
    """Store embeddings in Qdrant."""
    try:
        # Create embeddings
        embeddings = create_embeddings(texts)
        
        # Prepare points
        points = []
        for i, (text, embedding) in enumerate(zip(texts, embeddings)):
            point = models.PointStruct(
                id=i,
                vector=embedding,
                payload={
                    "text": text,
                    "metadata": metadata[i] if metadata else {}
                }
            )
            points.append(point)
        
        # Store in Qdrant
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )
        
    except Exception as e:
        logger.error(f"Error storing embeddings: {e}")
        raise 