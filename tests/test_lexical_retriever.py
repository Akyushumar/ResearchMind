import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from researchmind.retrieval.lexical_retriever import LexicalRetriever
from researchmind.models.evidence_chunk import EvidenceChunk
from researchmind.retrieval.base import SearchMetadataFilter

@pytest.mark.asyncio
@pytest.mark.skip(reason="FTS queries are PostgreSQL only and fail on SQLite test DB")
async def test_lexical_retriever(session: AsyncSession):
    # This might fail on SQLite if we don't compile websearch_to_tsquery
    
    # Just a placeholder test to see if it parses
    retriever = LexicalRetriever(session)
    results = await retriever.retrieve("parking spaces")
    
    # Assert it returns a list (empty if no data or no match)
    assert isinstance(results, list)
