from researchmind.retrieval.base import BaseRetriever, SearchMetadataFilter, SearchResult
from researchmind.retrieval.lexical_retriever import LexicalRetriever
from researchmind.retrieval.semantic_retriever import SemanticRetriever

class HybridSearchService:
    def __init__(
        self, 
        lexical_retriever: LexicalRetriever, 
        semantic_retriever: SemanticRetriever,
        rrf_k: int = 60
    ):
        self.lexical_retriever = lexical_retriever
        self.semantic_retriever = semantic_retriever
        self.rrf_k = rrf_k
        
    async def search(
        self, 
        query: str, 
        filters: SearchMetadataFilter | None = None, 
        limit: int = 10,
        strategy: str = "hybrid" # 'lexical', 'semantic', or 'hybrid'
    ) -> list[SearchResult]:
        if strategy == "lexical":
            return await self.lexical_retriever.retrieve(query, filters, limit)
        elif strategy == "semantic":
            return await self.semantic_retriever.retrieve(query, filters, limit)
            
        # Hybrid
        lexical_results = await self.lexical_retriever.retrieve(query, filters, limit=limit*2)
        semantic_results = await self.semantic_retriever.retrieve(query, filters, limit=limit*2)
        
        return self._apply_rrf(lexical_results, semantic_results, limit)
        
    def _apply_rrf(
        self, 
        lexical_results: list[SearchResult], 
        semantic_results: list[SearchResult],
        limit: int
    ) -> list[SearchResult]:
        """
        Applies Reciprocal Rank Fusion (RRF) to blend lexical and semantic results.
        """
        scores = {}
        items = {}
        
        # Rank lexical
        for rank, res in enumerate(lexical_results, start=1):
            chunk_id = res.chunk_id
            items[chunk_id] = res
            scores[chunk_id] = scores.get(chunk_id, 0.0) + (1.0 / (self.rrf_k + rank))
            
        # Rank semantic
        for rank, res in enumerate(semantic_results, start=1):
            chunk_id = res.chunk_id
            if chunk_id not in items:
                items[chunk_id] = res
            scores[chunk_id] = scores.get(chunk_id, 0.0) + (1.0 / (self.rrf_k + rank))
            
        # Sort by RRF score descending
        sorted_ids = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
        
        # Build final results
        final_results = []
        for chunk_id in sorted_ids[:limit]:
            res = items[chunk_id]
            # Replace score with RRF score and update retrieval_method
            res.score = scores[chunk_id]
            res.retrieval_method = "hybrid"
            final_results.append(res)
            
        return final_results

