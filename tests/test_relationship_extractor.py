import pytest

from researchmind.ingestion.base import ExtractedClause
from researchmind.models.enums import ClauseType
from researchmind.ingestion.extractors.relationship_extractor import RegexRelationshipExtractor

@pytest.fixture
def extractor():
    return RegexRelationshipExtractor()

def make_clause(path: str, content: str) -> ExtractedClause:
    return ExtractedClause(
        path=path,
        clause_number=path,
        clause_type=ClauseType.CLAUSE,
        title="Title",
        content=content,
        depth=path.count("."),
        is_mandatory=False,
        start_page=1,
        end_page=1,
        children=[]
    )

@pytest.mark.asyncio
async def test_as_per_regulation(extractor):
    c = make_clause("1", "The parking space shall be provided as per Regulation 6.3.")
    rels = await extractor.extract([c])
    assert len(rels) == 1
    assert rels[0].target_reference == "6.3"

@pytest.mark.asyncio
async def test_in_accordance_with(extractor):
    c = make_clause("1", "This is in accordance with Clause 4.1.2.")
    rels = await extractor.extract([c])
    assert len(rels) == 1
    assert rels[0].target_reference == "4.1.2"

@pytest.mark.asyncio
async def test_subject_to(extractor):
    c = make_clause("1", "subject to provisions of Regulation 4.1")
    rels = await extractor.extract([c])
    assert len(rels) == 1
    assert rels[0].target_reference == "4.1"

@pytest.mark.asyncio
async def test_refer_table(extractor):
    c = make_clause("1", "refer Table 8-B for more details.")
    rels = await extractor.extract([c])
    assert len(rels) == 1
    assert rels[0].target_reference == "Table 8-B"

@pytest.mark.asyncio
async def test_see_regulation(extractor):
    c = make_clause("1", "see Regulation 10.2")
    rels = await extractor.extract([c])
    assert len(rels) == 1
    assert rels[0].target_reference == "10.2"

@pytest.mark.asyncio
async def test_no_false_positive_year(extractor):
    c = make_clause("1", "published in 2020 by the authority")
    rels = await extractor.extract([c])
    assert len(rels) == 0

@pytest.mark.asyncio
async def test_no_false_positive_area(extractor):
    c = make_clause("1", "area of 8.5 sq.m.")
    rels = await extractor.extract([c])
    assert len(rels) == 0

@pytest.mark.asyncio
async def test_no_false_positive_page(extractor):
    c = make_clause("1", "on page 42 of the document")
    rels = await extractor.extract([c])
    assert len(rels) == 0

@pytest.mark.asyncio
async def test_multiple_refs_one_clause(extractor):
    c = make_clause("1", "as per Regulation 6.3 and see Section 4.5.")
    rels = await extractor.extract([c])
    assert len(rels) == 2
    targets = {r.target_reference for r in rels}
    assert targets == {"6.3", "4.5"}

@pytest.mark.asyncio
async def test_deduplication(extractor):
    c = make_clause("1", "as per Regulation 6.3. Later we see Regulation 6.3 again.")
    rels = await extractor.extract([c])
    assert len(rels) == 1
    assert rels[0].target_reference == "6.3"

@pytest.mark.asyncio
async def test_context_captured(extractor):
    c = make_clause("1", "First sentence. This is the context where we refer Table 8-B for details. Third sentence.")
    rels = await extractor.extract([c])
    assert len(rels) == 1
    assert "refer Table 8-B for details." in rels[0].context
    assert "First sentence" not in rels[0].context
