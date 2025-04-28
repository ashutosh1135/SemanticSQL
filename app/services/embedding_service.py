from typing import Dict, Any, List, Optional
import logging

from app.utils.embedding import create_embeddings, store_embeddings
from app.db.database import qdrant_client
from app.config.config import settings

logger = logging.getLogger("semanticsql")

class EmbeddingService:
    def __init__(self):
        self.collection_name = settings.QDRANT_COLLECTION

    @staticmethod
    async def process_schema(schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """Process schema information and store embeddings."""
        try:
            # Create embeddings
            embeddings = await create_embeddings(schema_info)
            
            # Store embeddings
            await store_embeddings(embeddings)
            
            return {
                "message": "Schema processed and embeddings stored successfully",
                "embeddings_count": len(embeddings)
            }
        except Exception as e:
            logger.error(f"Schema processing error: {e}")
            raise

    @staticmethod
    async def search_similar(text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar schema information."""
        try:
            # Create embedding for search query
            embedding = await create_embeddings({"text": text})
            
            # Search in Qdrant
            search_result = qdrant_client.search(
                collection_name=settings.QDRANT_COLLECTION,
                query_vector=embedding[0]["embedding"],
                limit=limit
            )
            
            return [
                {
                    "text": hit.payload["text"],
                    "score": hit.score
                } for hit in search_result
            ]
        except Exception as e:
            logger.error(f"Similarity search error: {e}")
            raise

    async def create_and_store_embeddings(self, texts: List[str], metadata: Optional[List[dict]] = None) -> None:
        """Create and store embeddings for texts."""
        try:
            # Create embeddings
            embeddings = create_embeddings(texts)
            
            # Store embeddings
            await store_embeddings(self.collection_name, texts, metadata)
            
        except Exception as e:
            logger.error(f"Error in embedding service: {e}")
            raise 