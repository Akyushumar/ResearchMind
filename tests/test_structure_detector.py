import pytest
from researchmind.ingestion.base import ParsedDocument, PageContent, TextBlock
from researchmind.models.enums import ClauseType
from researchmind.ingestion.detectors import DCRStructureDetector


def make_block(text, size=11.0, is_bold=False, page=1):
    return TextBlock(
        text=text, page_number=page, block_index=0,
        x0=0, y0=0, x1=10, y1=10, font_size=size, font_name="", is_bold=is_bold
    )


@pytest.fixture
def detector():
    return DCRStructureDetector()


@pytest.mark.asyncio
async def test_single_chapter(detector):
    blocks = [
        make_block("CHAPTER 1", size=16.0, is_bold=True),
        make_block("Body text", size=11.0)
    ]
    doc = ParsedDocument(file_path="", total_pages=1, metadata={}, pages=[PageContent(page_number=1, text="", width=100, height=100, blocks=blocks)])
    struct = await detector.detect(doc)
    assert len(struct.sections) == 1
    assert struct.sections[0].title == "CHAPTER 1"
    assert struct.sections[0].content == "Body text"
    assert struct.sections[0].level == 0


@pytest.mark.asyncio
async def test_nested_hierarchy(detector):
    blocks = [
        make_block("8", size=16.0, is_bold=True),
        make_block("8.1 General", size=13.0, is_bold=True),
        make_block("8.2 Parking", size=13.0, is_bold=True),
        make_block("8.2.1 Res", size=11.0, is_bold=True),
        make_block("body", size=11.0),
        make_block("body", size=11.0),
        make_block("body", size=11.0),
        make_block("body", size=11.0),
        make_block("body", size=11.0)
    ]
    doc = ParsedDocument(file_path="", total_pages=1, metadata={}, pages=[PageContent(page_number=1, text="", width=100, height=100, blocks=blocks)])
    struct = await detector.detect(doc)
    
    # 8
    assert len(struct.sections) == 1
    assert struct.sections[0].clause_number == "8"
    
    # 8.1, 8.2
    assert len(struct.sections[0].children) == 2
    assert struct.sections[0].children[0].clause_number == "8.1"
    assert struct.sections[0].children[1].clause_number == "8.2"
    
    # 8.2.1
    assert len(struct.sections[0].children[1].children) == 1
    assert struct.sections[0].children[1].children[0].clause_number == "8.2.1"


@pytest.mark.asyncio
async def test_sibling_sections(detector):
    blocks = [
        make_block("8.1", size=13.0, is_bold=True),
        make_block("8.2", size=13.0, is_bold=True)
    ]
    doc = ParsedDocument(file_path="", total_pages=1, metadata={}, pages=[PageContent(page_number=1, text="", width=100, height=100, blocks=blocks)])
    struct = await detector.detect(doc)
    assert len(struct.sections) == 2
    assert struct.sections[0].clause_number == "8.1"
    assert struct.sections[1].clause_number == "8.2"


@pytest.mark.asyncio
async def test_lettered_items_nested(detector):
    blocks = [
        make_block("8.2.1", size=11.0, is_bold=True),
        make_block("(a) Item A", size=11.0),
        make_block("(b) Item B", size=11.0)
    ]
    doc = ParsedDocument(file_path="", total_pages=1, metadata={}, pages=[PageContent(page_number=1, text="", width=100, height=100, blocks=blocks)])
    struct = await detector.detect(doc)
    assert len(struct.sections) == 1
    assert len(struct.sections[0].children) == 2
    assert struct.sections[0].children[0].clause_number == "a"
    assert struct.sections[0].children[1].clause_number == "b"


@pytest.mark.asyncio
async def test_proviso_as_child(detector):
    blocks = [
        make_block("8.2.1", size=11.0, is_bold=True),
        make_block("Provided that", size=11.0, is_bold=True),
        make_block("body", size=11.0)
    ]
    doc = ParsedDocument(file_path="", total_pages=1, metadata={}, pages=[PageContent(page_number=1, text="", width=100, height=100, blocks=blocks)])
    struct = await detector.detect(doc)
    assert len(struct.sections[0].children) == 1
    assert struct.sections[0].children[0].clause_type == ClauseType.PROVISO
    assert struct.sections[0].children[0].content == "body"


@pytest.mark.asyncio
async def test_table_as_child_typed_table(detector):
    blocks = [
        make_block("8.2", size=13.0, is_bold=True),
        make_block("Table 8-B", size=11.0, is_bold=True)
    ]
    doc = ParsedDocument(file_path="", total_pages=1, metadata={}, pages=[PageContent(page_number=1, text="", width=100, height=100, blocks=blocks)])
    struct = await detector.detect(doc)
    assert len(struct.sections[0].children) == 1
    assert struct.sections[0].children[0].clause_type == ClauseType.TABLE


@pytest.mark.asyncio
async def test_body_text_accumulation(detector):
    blocks = [
        make_block("8.1", size=13.0, is_bold=True),
        make_block("Part 1", size=11.0),
        make_block("Part 2", size=11.0)
    ]
    doc = ParsedDocument(file_path="", total_pages=1, metadata={}, pages=[PageContent(page_number=1, text="", width=100, height=100, blocks=blocks)])
    struct = await detector.detect(doc)
    assert struct.sections[0].content == "Part 1\nPart 2"


@pytest.mark.asyncio
async def test_page_provenance_tracking(detector):
    blocks = [
        make_block("8.1", size=13.0, is_bold=True, page=1),
        make_block("Part 1", size=11.0, page=1),
        make_block("Part 2", size=11.0, page=2)
    ]
    doc = ParsedDocument(file_path="", total_pages=2, metadata={}, pages=[PageContent(page_number=1, text="", width=100, height=100, blocks=blocks)])
    struct = await detector.detect(doc)
    assert struct.sections[0].start_page == 1
    assert struct.sections[0].end_page == 2


@pytest.mark.asyncio
async def test_heading_text_not_in_content(detector):
    blocks = [
        make_block("8.1", size=13.0, is_bold=True),
        make_block("Body", size=11.0)
    ]
    doc = ParsedDocument(file_path="", total_pages=1, metadata={}, pages=[PageContent(page_number=1, text="", width=100, height=100, blocks=blocks)])
    struct = await detector.detect(doc)
    assert "8.1" not in struct.sections[0].content


@pytest.mark.asyncio
async def test_empty_section_consecutive_headings(detector):
    blocks = [
        make_block("8.1", size=13.0, is_bold=True),
        make_block("8.2", size=13.0, is_bold=True)
    ]
    doc = ParsedDocument(file_path="", total_pages=1, metadata={}, pages=[PageContent(page_number=1, text="", width=100, height=100, blocks=blocks)])
    struct = await detector.detect(doc)
    assert struct.sections[0].content == ""


@pytest.mark.asyncio
async def test_body_before_any_heading(detector):
    blocks = [
        make_block("Preface body", size=11.0),
        make_block("8.1", size=13.0, is_bold=True)
    ]
    doc = ParsedDocument(file_path="", total_pages=1, metadata={}, pages=[PageContent(page_number=1, text="", width=100, height=100, blocks=blocks)])
    struct = await detector.detect(doc)
    # The Preface body is skipped since there's no section, but it shouldn't crash
    assert len(struct.sections) == 1
    assert struct.sections[0].clause_number == "8.1"
