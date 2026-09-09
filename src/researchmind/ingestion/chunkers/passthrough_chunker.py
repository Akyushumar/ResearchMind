from researchmind.ingestion.base import ClauseChunker, ExtractedClause, EvidenceChunkData

class PassthroughChunker(ClauseChunker):
    """
    Creates one chunk per clause. Does not split clauses.
    """
    
    async def chunk(self, clauses: list[ExtractedClause]) -> list[EvidenceChunkData]:
        chunks = []
        for clause in clauses:
            self._chunk_recursive(clause, chunks)
        return chunks
        
    def _chunk_recursive(self, clause: ExtractedClause, chunks: list[EvidenceChunkData]):
        if clause.content:
            # simple token estimate
            token_count = len(clause.content.split())
            
            chunk = EvidenceChunkData(
                clause_path=clause.path,
                chunk_index=0,
                content=clause.content,
                token_count=token_count,
                source_text=clause.content,
                start_page=clause.start_page,
                end_page=clause.end_page,
                bbox=None
            )
            chunks.append(chunk)
            
        for child in clause.children:
            self._chunk_recursive(child, chunks)

