import uuid
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from researchmind.api.dependencies import get_db, get_vector_store, get_settings_dep
from researchmind.config.settings import Settings
from researchmind.db.vector_store import VectorStore
from researchmind.retrieval.lexical_retriever import LexicalRetriever
from researchmind.retrieval.semantic_retriever import SemanticRetriever
from researchmind.retrieval.hybrid_search import HybridSearchService
from researchmind.retrieval.base import SearchMetadataFilter, SearchResult
from researchmind.retrieval.embeddings.openai_provider import OpenAIEmbeddingProvider

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("/")
async def search_evidence(
    query: str = Query(..., description="The natural language query"),
    strategy: str = Query("hybrid", description="Search strategy: 'lexical', 'semantic', or 'hybrid'"),
    limit: int = Query(10, description="Max number of results to return"),
    document_ids: Optional[List[uuid.UUID]] = Query(None, description="Filter by document version IDs"),
    jurisdiction_ids: Optional[List[uuid.UUID]] = Query(None, description="Filter by jurisdiction IDs"),
    clause_types: Optional[List[str]] = Query(None, description="Filter by clause types"),
    session: AsyncSession = Depends(get_db),
    vector_store: VectorStore = Depends(get_vector_store),
    settings: Settings = Depends(get_settings_dep)
):
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    filters = SearchMetadataFilter(
        document_version_ids=document_ids,
        jurisdiction_ids=jurisdiction_ids,
        clause_types=clause_types
    )
    
    # Initialize components
    lexical = LexicalRetriever(session)
    embedding_provider = OpenAIEmbeddingProvider(
        model=settings.embedding_model,
        dimension=settings.embedding_dimension
    )
    semantic = SemanticRetriever(vector_store, embedding_provider, session)
    hybrid = HybridSearchService(lexical, semantic)
    
    try:
        results = await hybrid.search(query, filters=filters, limit=limit, strategy=strategy)
        
        # Format output
        return {
            "query": query,
            "strategy": strategy,
            "results": [
                {
                    "chunk_id": str(r.chunk_id),
                    "clause_id": str(r.clause_id) if r.clause_id else None,
                    "document_version_id": str(r.document_version_id) if r.document_version_id else None,
                    "clause_path": r.clause_path,
                    "content": r.content,
                    "hierarchy_context": r.hierarchy_context,
                    "score": r.score,
                    "retrieval_method": r.retrieval_method
                } for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

