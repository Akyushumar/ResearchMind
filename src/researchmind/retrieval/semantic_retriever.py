from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from researchmind.db.vector_store import VectorStore
from researchmind.retrieval.embeddings.base import BaseEmbeddingProvider
from researchmind.models.evidence_chunk import EvidenceChunk
from researchmind.retrieval.base import BaseRetriever, SearchMetadataFilter, SearchResult
from researchmind.models.document import DocumentVersion, RegulatoryDocument

class SemanticRetriever(BaseRetriever):
    """
    Retrieves evidence chunks using dense embeddings from Qdrant.
    """
    
    def __init__(
        self, 
        vector_store: VectorStore, 
        embedding_provider: BaseEmbeddingProvider,
        session: AsyncSession
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.session = session
        
    async def retrieve(
        self, 
        query: str, 
        filters: SearchMetadataFilter | None = None, 
        limit: int = 10
    ) -> list[SearchResult]:
        if not query.strip():
            return []
            
        # 1. Embed query
        query_embeddings = await self.embedding_provider.get_embeddings([query])
        if not query_embeddings:
            return []
        query_vector = query_embeddings[0]
        
        # 2. Build Qdrant metadata filters
        qdrant_filter = None
        if filters:
            must_conditions = []
            
            if filters.document_version_ids:
                # Need MatchAny, but since Qdrant client python wrapper doesn't have it natively in older versions
                # we can use multiple FieldCondition with Should, but actually MatchAny is supported
                must_conditions.append(
                    FieldCondition(
                        key="document_version_id",
                        match={"any": [str(d) for d in filters.document_version_ids]}
                    )
                )
                
            if filters.clause_types:
                must_conditions.append(
                    FieldCondition(
                        key="chunk_type",
                        match={"any": filters.clause_types}
                    )
                )
                
            # If jurisdiction filtering is needed, we need to resolve doc_versions first from PG
            if filters.jurisdiction_ids:
                stmt = select(DocumentVersion.id).join(RegulatoryDocument).where(RegulatoryDocument.jurisdiction_id.in_(filters.jurisdiction_ids))
                res = await self.session.execute(stmt)
                doc_version_ids = [row[0] for row in res.all()]
                if not doc_version_ids:
                    return [] # No docs for this jurisdiction
                must_conditions.append(
                    FieldCondition(
                        key="document_version_id",
                        match={"any": [str(d) for d in doc_version_ids]}
                    )
                )
                
            if must_conditions:
                qdrant_filter = Filter(must=must_conditions)
                
        # 3. Search VectorStore
        scored_points = self.vector_store.search(
            query_vector=query_vector,
            limit=limit,
            query_filter=qdrant_filter
        )
        
        # 4. Map back to SearchResult
        results = []
        for point in scored_points:
            import uuid
            results.append(
                SearchResult(
                    chunk_id=uuid.UUID(point.id),
                    clause_id=uuid.UUID(point.payload.get("clause_id")) if point.payload.get("clause_id") else None,
                    document_version_id=uuid.UUID(point.payload.get("document_version_id")) if point.payload.get("document_version_id") else None,
                    clause_path=point.payload.get("clause_path"),
                    content=point.payload.get("content", ""),
                    hierarchy_context=point.payload.get("hierarchy_context"),
                    score=point.score,
                    retrieval_method="semantic"
                )
            )
            
        return results
