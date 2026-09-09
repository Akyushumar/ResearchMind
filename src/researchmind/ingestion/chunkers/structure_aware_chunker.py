from researchmind.ingestion.base import ClauseChunker, ExtractedClause, EvidenceChunkData
from researchmind.models.enums import ClauseType

class StructureAwareChunker(ClauseChunker):
    """
    Creates chunks that incorporate their structural hierarchy.
    """

    async def chunk(self, clauses: list[ExtractedClause]) -> list[EvidenceChunkData]:
        chunks = []
        for clause in clauses:
            self._chunk_recursive(clause, [], chunks)
        return chunks

    def _chunk_recursive(
        self, 
        clause: ExtractedClause, 
        ancestors: list[ExtractedClause], 
        chunks: list[EvidenceChunkData]
    ):
        # Build hierarchy context string (e.g., "Chapter 8 > 8.2 Parking > (a)")
        hierarchy_parts = []
        for a in ancestors:
            part = a.clause_number or ""
            if a.title:
                part += f" {a.title}"
            if part.strip():
                hierarchy_parts.append(part.strip())
        
        current_part = clause.clause_number or ""
        if clause.title:
            current_part += f" {clause.title}"
        if current_part.strip():
            hierarchy_parts.append(current_part.strip())
            
        hierarchy_context = " > ".join(hierarchy_parts) if hierarchy_parts else None

        # Build context-rich content
        content_parts = []
        if hierarchy_context:
            content_parts.append(f"Hierarchy: {hierarchy_context}")
        
        clause_id_str = f"Clause {clause.clause_number}" if clause.clause_number else "Clause"
        if clause.title:
            clause_id_str += f" ({clause.title})"
            
        if clause.content:
            content_parts.append(f"{clause_id_str}:\n{clause.content}")
            rich_content = "\n\n".join(content_parts)
            
            # Simple token estimate
            token_count = len(rich_content.split())
            
            chunk = EvidenceChunkData(
                clause_path=clause.path,
                chunk_index=0,
                content=rich_content,
                token_count=token_count,
                source_text=clause.content,
                start_page=clause.start_page,
                end_page=clause.end_page,
                bbox=None,
                hierarchy_context=hierarchy_context,
                chunk_type=clause.clause_type.value
            )
            chunks.append(chunk)

        # Recurse for children
        new_ancestors = ancestors + [clause]
        for child in clause.children:
            self._chunk_recursive(child, new_ancestors, chunks)

