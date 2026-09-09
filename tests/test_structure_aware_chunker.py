import pytest
from researchmind.ingestion.base import ExtractedClause
from researchmind.models.enums import ClauseType
from researchmind.ingestion.chunkers.structure_aware_chunker import StructureAwareChunker

@pytest.mark.asyncio
async def test_structure_aware_chunker_hierarchy():
    chunker = StructureAwareChunker()
    
    # Root clause
    root = ExtractedClause(
        clause_number="8.0",
        title="Parking Requirements",
        content="General parking rules.",
        depth=1,
        path="8.0",
        clause_type=ClauseType.PART
    )
    
    # Child clause
    child = ExtractedClause(
        clause_number="8.2",
        title="Residential",
        content="Parking for residential buildings.",
        depth=2,
        path="8.2",
        clause_type=ClauseType.SECTION
    )
    
    # Grandchild clause
    grandchild = ExtractedClause(
        clause_number="(b)",
        title=None,
        content="Buildings above 15m require 2 spaces.",
        depth=3,
        path="8.2.b",
        clause_type=ClauseType.CLAUSE
    )
    
    child.children = [grandchild]
    root.children = [child]
    
    chunks = await chunker.chunk([root])
    
    assert len(chunks) == 3
    
    # Root chunk
    root_chunk = next(c for c in chunks if c.clause_path == "8.0")
    assert root_chunk.hierarchy_context == "8.0 Parking Requirements"
    assert "Hierarchy: 8.0 Parking Requirements" in root_chunk.content
    assert "Clause 8.0 (Parking Requirements):" in root_chunk.content
    assert "General parking rules." in root_chunk.content
    
    # Child chunk
    child_chunk = next(c for c in chunks if c.clause_path == "8.2")
    assert child_chunk.hierarchy_context == "8.0 Parking Requirements > 8.2 Residential"
    assert "Hierarchy: 8.0 Parking Requirements > 8.2 Residential" in child_chunk.content
    assert "Clause 8.2 (Residential):" in child_chunk.content
    
    # Grandchild chunk
    grandchild_chunk = next(c for c in chunks if c.clause_path == "8.2.b")
    assert grandchild_chunk.hierarchy_context == "8.0 Parking Requirements > 8.2 Residential > (b)"
    assert "Hierarchy: 8.0 Parking Requirements > 8.2 Residential > (b)" in grandchild_chunk.content
    assert "Clause (b):" in grandchild_chunk.content
    assert "Buildings above 15m require 2 spaces." in grandchild_chunk.content

