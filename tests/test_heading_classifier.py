import pytest

from researchmind.ingestion.base import TextBlock
from researchmind.models.enums import ClauseType
from researchmind.ingestion.detectors.heading_classifier import FontBasedHeadingClassifier, HeadingConfig

@pytest.fixture
def classifier():
    return FontBasedHeadingClassifier()

def test_large_bold_allcaps_is_chapter(classifier):
    block = TextBlock(
        text="CHAPTER 8", page_number=1, block_index=0,
        x0=0, y0=0, x1=10, y1=10, font_size=16.0, font_name="hebo", is_bold=True
    )
    res = classifier.classify(block)
    assert res.is_heading is True
    assert res.semantic_level == 0
    assert res.clause_type == ClauseType.PART

def test_medium_bold_is_section(classifier):
    block = TextBlock(
        text="8.1 General", page_number=1, block_index=0,
        x0=0, y0=0, x1=10, y1=10, font_size=13.0, font_name="hebo", is_bold=True
    )
    res = classifier.classify(block)
    assert res.is_heading is True
    assert res.semantic_level == 1
    assert res.clause_number == "8.1"
    assert res.numbering_depth == 1
    assert res.clause_type == ClauseType.SECTION

def test_small_bold_with_number_is_subsection(classifier):
    block = TextBlock(
        text="8.2.1", page_number=1, block_index=0,
        x0=0, y0=0, x1=10, y1=10, font_size=11.0, font_name="hebo", is_bold=True
    )
    res = classifier.classify(block)
    assert res.is_heading is True
    assert res.semantic_level == 3
    assert res.numbering_type == "decimal"

def test_plain_body_not_heading(classifier):
    block = TextBlock(
        text="The parking shall be...", page_number=1, block_index=0,
        x0=0, y0=0, x1=10, y1=10, font_size=11.0, font_name="helv", is_bold=False
    )
    res = classifier.classify(block)
    assert res.is_heading is False

def test_lettered_item_detected(classifier):
    block = TextBlock(
        text="(a) Buildings", page_number=1, block_index=0,
        x0=0, y0=0, x1=10, y1=10, font_size=11.0, font_name="helv", is_bold=False
    )
    res = classifier.classify(block, parent_depth=3)
    assert res.is_heading is True
    assert res.numbering_type == "letter"
    assert res.semantic_level == 10
    assert res.clause_number == "a"

def test_roman_item_detected(classifier):
    block = TextBlock(
        text="(iii) something", page_number=1, block_index=0,
        x0=0, y0=0, x1=10, y1=10, font_size=11.0, font_name="helv", is_bold=False
    )
    res = classifier.classify(block, parent_depth=4)
    assert res.is_heading is True
    assert res.numbering_type == "roman"
    assert res.semantic_level == 11

def test_proviso_detected(classifier):
    block = TextBlock(
        text="Provided that it is safe.", page_number=1, block_index=0,
        x0=0, y0=0, x1=10, y1=10, font_size=11.0, font_name="hebo", is_bold=True
    )
    res = classifier.classify(block, parent_depth=3)
    assert res.is_heading is True
    assert res.numbering_type == "label"
    assert res.clause_type == ClauseType.PROVISO
    assert res.semantic_level == 12

def test_note_detected(classifier):
    block = TextBlock(
        text="Note: stack parking allowed.", page_number=1, block_index=0,
        x0=0, y0=0, x1=10, y1=10, font_size=11.0, font_name="hebo", is_bold=True
    )
    res = classifier.classify(block, parent_depth=3)
    assert res.is_heading is True
    assert res.clause_type == ClauseType.NOTE

def test_table_label_detected(classifier):
    block = TextBlock(
        text="Table 8-B", page_number=1, block_index=0,
        x0=0, y0=0, x1=10, y1=10, font_size=11.0, font_name="hebo", is_bold=True
    )
    res = classifier.classify(block, parent_depth=2)
    assert res.is_heading is True
    assert res.clause_type == ClauseType.TABLE
    assert res.clause_number == "Table 8-B"

def test_calibration(classifier):
    blocks = [
        TextBlock(text="body", page_number=1, block_index=0, x0=0, y0=0, x1=0, y1=0, font_size=10.0, font_name="", is_bold=False),
        TextBlock(text="body2", page_number=1, block_index=1, x0=0, y0=0, x1=0, y1=0, font_size=10.0, font_name="", is_bold=False),
        TextBlock(text="heading", page_number=1, block_index=2, x0=0, y0=0, x1=0, y1=0, font_size=14.0, font_name="", is_bold=True),
    ]
    classifier.calibrate(blocks)
    assert classifier.median_body_font_size == 10.0

def test_numbering_depth_vs_semantic_level(classifier):
    block = TextBlock(
        text="(a) Buildings", page_number=1, block_index=0,
        x0=0, y0=0, x1=10, y1=10, font_size=11.0, font_name="helv", is_bold=False
    )
    res = classifier.classify(block, parent_depth=3)
    assert res.numbering_depth == 0
    assert res.semantic_level == 10
