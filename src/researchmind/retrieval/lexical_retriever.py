from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from researchmind.models.evidence_chunk import EvidenceChunk
from researchmind.models.document import DocumentVersion
from researchmind.retrieval.base import BaseRetriever, SearchMetadataFilter, SearchResult

class LexicalRetriever(BaseRetriever):
    """
    Retrieves evidence chunks using PostgreSQL Full-Text Search.
    Uses websearch_to_tsquery for natural language search queries.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def retrieve(
        self, 
        query: str, 
        filters: SearchMetadataFilter | None = None, 
        limit: int = 10
    ) -> list[SearchResult]:
        if not query.strip():
            return []
            
        # Parse query for websearch
        tsquery = func.websearch_to_tsquery('english', query)
        
        # We need to filter and score
        # The EvidenceChunk.search_vector is a TSVector column
        stmt = select(EvidenceChunk, func.ts_rank_cd(EvidenceChunk.search_vector, tsquery).label("rank"))
        
        # Match only where it matches the query
        stmt = stmt.where(EvidenceChunk.search_vector.op("@@")(tsquery))
        
        # Apply metadata filters
        if filters:
            if filters.document_version_ids:
                stmt = stmt.where(EvidenceChunk.document_version_id.in_(filters.document_version_ids))
            
            if filters.jurisdiction_ids:
                from researchmind.models.document import RegulatoryDocument
                stmt = stmt.join(EvidenceChunk.document_version).join(DocumentVersion.document)
                stmt = stmt.where(RegulatoryDocument.jurisdiction_id.in_(filters.jurisdiction_ids))
                
            if filters.clause_types:
                stmt = stmt.where(EvidenceChunk.chunk_type.in_(filters.clause_types))
                
        # Order by rank
        stmt = stmt.order_by(func.ts_rank_cd(EvidenceChunk.search_vector, tsquery).desc())
        stmt = stmt.limit(limit)
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        results = []
        for chunk, rank in rows:
            results.append(
                SearchResult(
                    chunk_id=chunk.id,
                    clause_id=chunk.clause_id,
                    document_version_id=chunk.document_version_id,
                    clause_path=chunk.clause_path,
                    content=chunk.content,
                    hierarchy_context=chunk.hierarchy_context,
                    score=float(rank),
                    retrieval_method="lexical"
                )
            )
            
        return results
