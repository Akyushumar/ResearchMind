from researchmind.ingestion.base import (
    ClauseExtractor,
    DocumentStructure,
    DetectedSection,
    ExtractedClause,
)
from researchmind.models.enums import ClauseType
import re

class DCRClauseExtractor(ClauseExtractor):
    """
    Extracts clauses from a DocumentStructure tree, computing materialized paths,
    detecting mandatory/advisory language heuristics, and cleaning content.
    """
    
    MANDATORY_INDICATORS = re.compile(r"\b(shall|must|is required|it is mandatory)\b", re.IGNORECASE)
    ADVISORY_INDICATORS = re.compile(r"\b(may|should|recommended|desirable|may be permitted)\b", re.IGNORECASE)
    
    async def extract(self, structure: DocumentStructure) -> list[ExtractedClause]:
        extracted: list[ExtractedClause] = []
        
        for section in structure.sections:
            self._walk_section(section, parent_path="", extracted=extracted)
            
        return extracted
        
    def _walk_section(self, section: DetectedSection, parent_path: str, extracted: list[ExtractedClause], ordinal_counters: dict[str, int] = None):
        if ordinal_counters is None:
            ordinal_counters = {}
            
        # Compute path
        path = self._compute_path(parent_path, section, ordinal_counters)
        
        # Clean content
        cleaned_content = self._clean_content(section.content)
        
        # Mandatory heuristic
        is_mandatory = self._detect_mandatory_language(cleaned_content)
        
        # Create ExtractedClause
        clause = ExtractedClause(
            title=section.title,
            clause_number=section.clause_number,
            content=cleaned_content,
            depth=path.count("."),
            path=path,
            clause_type=section.clause_type,
            is_mandatory=is_mandatory,
            start_page=section.start_page,
            end_page=section.end_page,
            children=[]
        )
        
        extracted.append(clause)
        
        # Process children
        child_counters = {}
        for child in section.children:
            child_extracted = []
            self._walk_section(child, parent_path=path, extracted=child_extracted, ordinal_counters=child_counters)
            clause.children.extend(child_extracted)
            
    def _compute_path(self, parent_path: str, section: DetectedSection, counters: dict[str, int]) -> str:
        if not parent_path:
            return section.clause_number or section.title.lower().replace(" ", "_")
            
        if section.clause_type == ClauseType.PROVISO:
            counters["proviso"] = counters.get("proviso", 0) + 1
            return f"{parent_path}.proviso.{counters['proviso']}"
        elif section.clause_type == ClauseType.NOTE:
            counters["note"] = counters.get("note", 0) + 1
            return f"{parent_path}.note.{counters['note']}"
            
        if section.clause_number:
            if section.clause_number.startswith(parent_path + "."):
                return section.clause_number
            if "." in section.clause_number and section.clause_number[0].isdigit():
                return section.clause_number
            return f"{parent_path}.{section.clause_number}"
            
        # Fallback
        counters["unknown"] = counters.get("unknown", 0) + 1
        return f"{parent_path}.unknown.{counters['unknown']}"
        
    def _clean_content(self, content: str) -> str:
        if not content:
            return ""
        # Collapse whitespace
        content = re.sub(r"\s+", " ", content)
        return content.strip()
        
    def _detect_mandatory_language(self, content: str) -> bool:
        """Heuristic to detect mandatory language. This is NOT a legal conclusion."""
        if not content:
            return False
        # If it contains mandatory indicators, True.
        # Even if it contains advisory indicators, if it has mandatory, we flag it as mandatory for now.
        if self.MANDATORY_INDICATORS.search(content):
            return True
        return False
