import asyncio
import argparse
from pathlib import Path
from researchmind.ingestion.parsers.pdf_parser import PDFParser
from researchmind.ingestion.detectors.dcr_structure_detector import DCRStructureDetector
from researchmind.ingestion.extractors.clause_extractor import DCRClauseExtractor
from researchmind.ingestion.extractors.relationship_extractor import RegexRelationshipExtractor

async def main():
    parser = argparse.ArgumentParser(description="Test structure detection on a PDF")
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
    parser.add_argument("--chapter", type=str, help="Chapter to filter by (e.g. '8')")
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        return
        
    print(f"Parsing {pdf_path}...")
    pdf_parser = PDFParser()
    parsed_doc = await pdf_parser.parse(pdf_path)
    
    print("Detecting structure...")
    detector = DCRStructureDetector()
    structure = await detector.detect(parsed_doc)
    
    print("Extracting clauses...")
    extractor = DCRClauseExtractor()
    clauses = await extractor.extract(structure)
    
    # Filter by chapter if specified
    if args.chapter:
        chapter_clauses = [c for c in clauses if args.chapter in c.path.split(".")[0]]
        if not chapter_clauses:
            # Fallback if the path is something like "chapter_8..."
            chapter_clauses = [c for c in clauses if f"chapter_{args.chapter}" in c.path.lower()]
        clauses = chapter_clauses
        
    print("Extracting relationships...")
    rel_extractor = RegexRelationshipExtractor()
    relationships = await rel_extractor.extract(clauses)
    
    def print_tree(clause, indent=""):
        pages = f"(pages {clause.start_page}-{clause.end_page})" if clause.start_page != clause.end_page else f"(page {clause.start_page})"
        print(f"{indent}{clause.title or clause.path} {pages}")
        for child in clause.children:
            print_tree(child, indent + "  ")
            
    print("\n--- Document Structure ---")
    for c in clauses:
        print_tree(c)
        
    def count_clauses(c):
        return 1 + sum(count_clauses(child) for child in c.children)
        
    def count_tables(c):
        count = 1 if c.clause_type.value == "table" else 0
        return count + sum(count_tables(child) for child in c.children)
        
    total_clauses = sum(count_clauses(c) for c in clauses)
    total_tables = sum(count_tables(c) for c in clauses)
    
    print("\n--- Summary ---")
    print(f"Total Sections/Clauses: {total_clauses}")
    print(f"Total Tables: {total_tables}")
    print(f"Total Cross-references: {len(relationships)}")

if __name__ == "__main__":
    asyncio.run(main())

