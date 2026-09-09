from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, Filter, PointStruct, ScoredPoint, VectorParams
from researchmind.config.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Wrapper for Qdrant vector store operations."""

    def __init__(self, host: str, port: int, collection_name: str):
        self._client = QdrantClient(host=host, port=port)
        self._collection_name = collection_name

    def ensure_collection(self, vector_size: int, distance: Distance = Distance.COSINE) -> None:
        """Create collection if it doesn't exist."""
        try:
            if not self.collection_exists():
                logger.info(f"Creating collection {self._collection_name} with size {vector_size}")
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=distance),
                )
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise

    def collection_exists(self) -> bool:
        """Check if the collection exists."""
        try:
            collections = self._client.get_collections().collections
            return any(c.name == self._collection_name for c in collections)
        except Exception as e:
            logger.error(f"Error checking collection existence: {e}")
            raise

    def upsert(self, points: list[PointStruct]) -> None:
        """Upsert vectors into the collection."""
        try:
            self._client.upsert(
                collection_name=self._collection_name,
                points=points,
            )
        except Exception as e:
            logger.error(f"Error upserting points: {e}")
            raise

    def upsert_chunks(self, chunks: list[Any], embeddings: list[list[float]]) -> None:
        """Upsert EvidenceChunk objects and their embeddings."""
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match")
            
        points = []
        for chunk, embedding in zip(chunks, embeddings):
            # chunk.id is a UUID, we can use str(chunk.id) for Qdrant
            payload = {
                "clause_id": str(chunk.clause_id) if chunk.clause_id else None,
                "document_version_id": str(chunk.document_version_id) if chunk.document_version_id else None,
                "clause_path": chunk.clause_path,
                "chunk_type": chunk.chunk_type,
                "content": chunk.content,
                "hierarchy_context": chunk.hierarchy_context,
                "start_page": chunk.start_page,
                "end_page": chunk.end_page
            }
            points.append(
                PointStruct(
                    id=str(chunk.id),
                    vector=embedding,
                    payload={k: v for k, v in payload.items() if v is not None}
                )
            )
            
        self.upsert(points)

    def search(
        self, query_vector: list[float], limit: int = 10, query_filter: Filter | None = None
    ) -> list[ScoredPoint]:
        """Search for similar vectors."""
        try:
            return self._client.search(
                collection_name=self._collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=query_filter,
            )
        except Exception as e:
            logger.error(f"Error searching points: {e}")
            raise

    def delete(self, point_ids: list[str]) -> None:
        """Delete vectors by point IDs."""
        try:
            self._client.delete(
                collection_name=self._collection_name,
                points_selector=point_ids,
            )
        except Exception as e:
            logger.error(f"Error deleting points: {e}")
            raise

    def count(self) -> int:
        """Count vectors in the collection."""
        try:
            return self._client.count(collection_name=self._collection_name).count
        except Exception as e:
            logger.error(f"Error counting points: {e}")
            raise

    def health_check(self) -> bool:
        """Check if Qdrant is accessible."""
        try:
            collections = self._client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
