import pytest
import yaml
from pathlib import Path
from researchmind.ingestion.parsers.pdf_parser import PDFParser
from researchmind.ingestion.detectors.dcr_structure_detector import DCRStructureDetector
from researchmind.ingestion.extractors.clause_extractor import DCRClauseExtractor
from researchmind.ingestion.extractors.relationship_extractor import RegexRelationshipExtractor

@pytest.fixture(scope="module")
async def benchmark_data():
    pdf_path = Path("data/corpus/udcpr_2020.pdf")
    yaml_path = Path("data/benchmarks/udcpr_2020_ch8.yaml")
    
    if not pdf_path.exists() or not yaml_path.exists():
        pytest.skip("Benchmark files not available")
        
    with open(yaml_path, "r") as f:
        expected = yaml.safe_load(f)
        
    parser = PDFParser()
    parsed_doc = await parser.parse(pdf_path)
    
    detector = DCRStructureDetector()
    structure = await detector.detect(parsed_doc)
    
    extractor = DCRClauseExtractor()
    clauses = await extractor.extract(structure)
    
    chapter_clauses = [c for c in clauses if expected["chapter"] in c.path.split(".")[0]]
    if not chapter_clauses:
        chapter_clauses = [c for c in clauses if f"chapter_{expected['chapter']}" in c.path.lower()]
    
    rel_extractor = RegexRelationshipExtractor()
    rels = await rel_extractor.extract(chapter_clauses)
    
    # Flatten clause tree to easy lookup
    def flatten(c_list):
        flat = []
        for c in c_list:
            flat.append(c)
            flat.extend(flatten(c.children))
        return flat
        
    flat_clauses = flatten(chapter_clauses)
    
    return expected, flat_clauses, rels

@pytest.mark.asyncio
async def test_expected_clauses_detected(benchmark_data):
    expected, flat_clauses, _ = benchmark_data
    
    found_paths = {c.path for c in flat_clauses}
    expected_paths = {c["clause_path"] for c in expected["expected_clauses"] if c["expected"]}
    
    for exp_path in expected_paths:
        # Relax match for the chapter title since dashes/spaces can encode differently
        if exp_path.startswith("chapter_8"):
            assert any(fp.startswith("chapter_8") for fp in found_paths), f"Missing root chapter: {exp_path}"
        else:
            assert exp_path in found_paths, f"Missing expected clause: {exp_path}"

@pytest.mark.asyncio
async def test_expected_tables_detected(benchmark_data):
    expected, flat_clauses, _ = benchmark_data
    
    found_tables = {c.path for c in flat_clauses if c.clause_type.value == "table"}
    
    for t in expected["expected_tables"]:
        expected_path = f"{t['parent_path']}.{t['identifier']}"
        assert expected_path in found_tables or any(t['identifier'].lower() in ft.lower() for ft in found_tables)

@pytest.mark.asyncio
async def test_expected_relationships_detected(benchmark_data):
    expected, _, rels = benchmark_data
    
    for r in expected["expected_relationships"]:
        found = any(er.source_clause_path == r["source"] and er.target_reference == r["target"] for er in rels)
        assert found, f"Missing relationship: {r['source']} -> {r['target']}"

@pytest.mark.asyncio
async def test_report_metrics(benchmark_data):
    expected, flat_clauses, rels = benchmark_data
    
    found_paths = {c.path for c in flat_clauses}
    expected_paths = {c["clause_path"] for c in expected["expected_clauses"] if c["expected"]}
    
    recall = len(expected_paths.intersection(found_paths)) / len(expected_paths) if expected_paths else 1.0
    print(f"\nBenchmark Metrics:")
    print(f"Clause Recall: {recall:.2%}")
