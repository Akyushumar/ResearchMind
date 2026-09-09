import pytest

from researchmind.ingestion.base import DocumentStructure, DetectedSection
from researchmind.models.enums import ClauseType
from researchmind.ingestion.extractors.clause_extractor import DCRClauseExtractor

@pytest.fixture
def extractor():
    return DCRClauseExtractor()

@pytest.mark.asyncio
async def test_materialized_paths_decimal(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(
            title="8", content="", level=0, clause_number="8", clause_type=ClauseType.PART,
            start_page=1, end_page=1, children=[
                DetectedSection(
                    title="8.2", content="", level=1, clause_number="8.2", clause_type=ClauseType.SECTION,
                    start_page=1, end_page=1, children=[
                        DetectedSection(
                            title="8.2.1", content="", level=2, clause_number="8.2.1", clause_type=ClauseType.CLAUSE,
                            start_page=1, end_page=1, children=[]
                        )
                    ]
                )
            ]
        )
    ])
    
    clauses = await extractor.extract(struct)
    assert len(clauses) == 1
    root = clauses[0]
    assert root.path == "8"
    assert root.children[0].path == "8.2"
    assert root.children[0].children[0].path == "8.2.1"


@pytest.mark.asyncio
async def test_materialized_path_lettered(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(
            title="8.2.1", content="", level=2, clause_number="8.2.1", clause_type=ClauseType.CLAUSE,
            start_page=1, end_page=1, children=[
                DetectedSection(
                    title="a", content="", level=3, clause_number="a", clause_type=ClauseType.SUB_CLAUSE,
                    start_page=1, end_page=1, children=[]
                ),
                DetectedSection(
                    title="b", content="", level=3, clause_number="b", clause_type=ClauseType.SUB_CLAUSE,
                    start_page=1, end_page=1, children=[]
                )
            ]
        )
    ])
    
    clauses = await extractor.extract(struct)
    root = clauses[0]
    assert root.children[0].path == "8.2.1.a"
    assert root.children[1].path == "8.2.1.b"


@pytest.mark.asyncio
async def test_materialized_path_roman(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(
            title="a", content="", level=3, clause_number="a", clause_type=ClauseType.SUB_CLAUSE,
            start_page=1, end_page=1, children=[
                DetectedSection(
                    title="ii", content="", level=4, clause_number="ii", clause_type=ClauseType.SUB_CLAUSE,
                    start_page=1, end_page=1, children=[]
                )
            ]
        )
    ])
    # For testing, parent_path will start as "a" here
    clauses = await extractor.extract(struct)
    assert clauses[0].children[0].path == "a.ii"


@pytest.mark.asyncio
async def test_materialized_path_table(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(
            title="8.2", content="", level=1, clause_number="8.2", clause_type=ClauseType.SECTION,
            start_page=1, end_page=1, children=[
                DetectedSection(
                    title="Table 8-B", content="", level=2, clause_number="Table 8-B", clause_type=ClauseType.TABLE,
                    start_page=1, end_page=1, children=[]
                )
            ]
        )
    ])
    clauses = await extractor.extract(struct)
    assert clauses[0].children[0].path == "8.2.Table 8-B"


@pytest.mark.asyncio
async def test_materialized_path_proviso(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(
            title="8.2.1", content="", level=2, clause_number="8.2.1", clause_type=ClauseType.CLAUSE,
            start_page=1, end_page=1, children=[
                DetectedSection(
                    title="Proviso", content="", level=3, clause_number="Proviso", clause_type=ClauseType.PROVISO,
                    start_page=1, end_page=1, children=[]
                )
            ]
        )
    ])
    clauses = await extractor.extract(struct)
    assert clauses[0].children[0].path == "8.2.1.proviso.1"


@pytest.mark.asyncio
async def test_materialized_path_note(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(
            title="8.2", content="", level=2, clause_number="8.2", clause_type=ClauseType.CLAUSE,
            start_page=1, end_page=1, children=[
                DetectedSection(
                    title="Note", content="", level=3, clause_number="Note", clause_type=ClauseType.NOTE,
                    start_page=1, end_page=1, children=[]
                )
            ]
        )
    ])
    clauses = await extractor.extract(struct)
    assert clauses[0].children[0].path == "8.2.note.1"


@pytest.mark.asyncio
async def test_mandatory_language_shall(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(title="1", content="shall provide", level=0, clause_number="1", clause_type=ClauseType.CLAUSE, start_page=1, end_page=1, children=[])
    ])
    clauses = await extractor.extract(struct)
    assert clauses[0].is_mandatory is True

@pytest.mark.asyncio
async def test_mandatory_language_must(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(title="1", content="it must comply", level=0, clause_number="1", clause_type=ClauseType.CLAUSE, start_page=1, end_page=1, children=[])
    ])
    clauses = await extractor.extract(struct)
    assert clauses[0].is_mandatory is True

@pytest.mark.asyncio
async def test_advisory_language_may(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(title="1", content="may be permitted", level=0, clause_number="1", clause_type=ClauseType.CLAUSE, start_page=1, end_page=1, children=[])
    ])
    clauses = await extractor.extract(struct)
    assert clauses[0].is_mandatory is False

@pytest.mark.asyncio
async def test_advisory_language_should(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(title="1", content="should consider this", level=0, clause_number="1", clause_type=ClauseType.CLAUSE, start_page=1, end_page=1, children=[])
    ])
    clauses = await extractor.extract(struct)
    assert clauses[0].is_mandatory is False

@pytest.mark.asyncio
async def test_complex_qualifier_limitation(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(title="1", content="shall not exceed", level=0, clause_number="1", clause_type=ClauseType.CLAUSE, start_page=1, end_page=1, children=[])
    ])
    clauses = await extractor.extract(struct)
    # The heuristic looks for 'shall', so 'shall not' will flag as mandatory. This is documented behavior.
    assert clauses[0].is_mandatory is True

@pytest.mark.asyncio
async def test_content_whitespace_collapsed(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(title="1", content="this \n\n has   spaces", level=0, clause_number="1", clause_type=ClauseType.CLAUSE, start_page=1, end_page=1, children=[])
    ])
    clauses = await extractor.extract(struct)
    assert clauses[0].content == "this has spaces"

@pytest.mark.asyncio
async def test_clause_type_chapter(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(title="1", content="", level=0, clause_number="1", clause_type=ClauseType.PART, start_page=1, end_page=1, children=[])
    ])
    clauses = await extractor.extract(struct)
    assert clauses[0].clause_type == ClauseType.PART

@pytest.mark.asyncio
async def test_clause_type_table(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(title="Table 8-B", content="", level=0, clause_number="Table 8-B", clause_type=ClauseType.TABLE, start_page=1, end_page=1, children=[])
    ])
    clauses = await extractor.extract(struct)
    assert clauses[0].clause_type == ClauseType.TABLE

@pytest.mark.asyncio
async def test_clause_type_note(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(title="Note", content="", level=0, clause_number="Note", clause_type=ClauseType.NOTE, start_page=1, end_page=1, children=[])
    ])
    clauses = await extractor.extract(struct)
    assert clauses[0].clause_type == ClauseType.NOTE

@pytest.mark.asyncio
async def test_clause_type_proviso(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(title="Proviso", content="", level=0, clause_number="Proviso", clause_type=ClauseType.PROVISO, start_page=1, end_page=1, children=[])
    ])
    clauses = await extractor.extract(struct)
    assert clauses[0].clause_type == ClauseType.PROVISO

@pytest.mark.asyncio
async def test_children_populated(extractor):
    struct = DocumentStructure(title="Doc", metadata={}, sections=[
        DetectedSection(
            title="1", content="", level=0, clause_number="1", clause_type=ClauseType.CLAUSE, start_page=1, end_page=1,
            children=[
                DetectedSection(title="1.1", content="", level=1, clause_number="1.1", clause_type=ClauseType.CLAUSE, start_page=1, end_page=1, children=[])
            ]
        )
    ])
    clauses = await extractor.extract(struct)
    assert len(clauses[0].children) == 1
    assert clauses[0].children[0].path == "1.1"
