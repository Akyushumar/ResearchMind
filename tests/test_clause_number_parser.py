import pytest

from researchmind.ingestion.detectors.clause_number_parser import ClauseNumberParser

@pytest.fixture
def parser():
    return ClauseNumberParser()

def test_parse_decimal_simple(parser):
    res = parser.parse("8")
    assert res is not None
    assert res.parts == ["8"]
    assert res.numbering_depth == 0
    assert res.normalized == "8"
    assert res.numbering_type == "decimal"

def test_parse_decimal_nested(parser):
    res = parser.parse("8.2.1")
    assert res is not None
    assert res.parts == ["8", "2", "1"]
    assert res.numbering_depth == 2
    assert res.normalized == "8.2.1"
    assert res.numbering_type == "decimal"

def test_parse_letter(parser):
    res = parser.parse("(a)")
    assert res is not None
    assert res.parts == ["a"]
    assert res.numbering_depth == 0
    assert res.normalized == "a"
    assert res.numbering_type == "letter"

def test_parse_roman(parser):
    res = parser.parse("(iii)")
    assert res is not None
    assert res.parts == ["iii"]
    assert res.numbering_depth == 0
    assert res.normalized == "iii"
    assert res.numbering_type == "roman"

def test_parse_table_label(parser):
    res = parser.parse("Table 8-B")
    assert res is not None
    assert res.numbering_type == "label"
    assert res.normalized == "Table 8-B"

def test_parse_proviso(parser):
    res = parser.parse("Proviso")
    assert res is not None
    assert res.numbering_type == "label"
    assert res.normalized == "Proviso"

def test_parse_note(parser):
    res = parser.parse("Note:")
    assert res is not None
    assert res.numbering_type == "label"
    assert res.normalized == "Note"

def test_parse_body_text_returns_none(parser):
    assert parser.parse("The parking space") is None

def test_is_child_of_true(parser):
    assert parser.is_child_of("8.2.1", "8.2")

def test_is_child_of_false(parser):
    assert not parser.is_child_of("8.2.1", "8.3")

def test_is_child_of_same(parser):
    assert not parser.is_child_of("8.2", "8.2")

def test_leading_whitespace(parser):
    res = parser.parse("  8.2.1")
    assert res is not None
    assert res.normalized == "8.2.1"

def test_trailing_content(parser):
    res = parser.parse("8.2.1 Residential Buildings")
    assert res is not None
    assert res.normalized == "8.2.1"

def test_common_ancestor(parser):
    assert parser.common_ancestor("8.2.1", "8.2.3") == "8.2"
    assert parser.common_ancestor("8.2.1", "8.3.1") == "8"
    assert parser.common_ancestor("7.1", "8.1") is None

def test_edge_case_empty_string(parser):
    assert parser.parse("") is None

def test_edge_case_alphabetic_only(parser):
    assert parser.parse("Chapter Eight") is None
