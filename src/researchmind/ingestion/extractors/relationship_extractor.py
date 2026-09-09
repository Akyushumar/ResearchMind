from researchmind.ingestion.base import RelationshipExtractor, ExtractedClause, ExtractedRelationship
from researchmind.models.enums import RelationshipType
import re

class RegexRelationshipExtractor(RelationshipExtractor):
    REF_KEYWORDS = r"(?:as\s+per|in\s+accordance\s+with|subject\s+to|mentioned\s+in|specified\s+in|provided\s+under|laid\s+down\s+in|refer|see|vide|in)"
    CLAUSE_KEYWORDS = r"(?:Regulation|Clause|Rule|Section|Chapter)s?"
    NUMBER_PATTERN = r"(\d+(?:\.\d+)*)"
    TABLE_PATTERN = r"([A-Z0-9-]+)"
    
    CLAUSE_REF_REGEX = re.compile(rf"(?P<context>[^.]*{REF_KEYWORDS}(?:\s+provisions\s+of)?\s+{CLAUSE_KEYWORDS}\s+{NUMBER_PATTERN}[^.]*\.?)", re.IGNORECASE)
    TARGET_CLAUSE_REGEX = re.compile(rf"{REF_KEYWORDS}(?:\s+provisions\s+of)?\s+{CLAUSE_KEYWORDS}\s+{NUMBER_PATTERN}", re.IGNORECASE)
    
    TABLE_REF_REGEX = re.compile(rf"(?P<context>[^.]*{REF_KEYWORDS}\s+Table\s+{TABLE_PATTERN}[^.]*\.?)", re.IGNORECASE)
    TARGET_TABLE_REGEX = re.compile(rf"{REF_KEYWORDS}\s+Table\s+{TABLE_PATTERN}", re.IGNORECASE)
    
    async def extract(self, clauses: list[ExtractedClause]) -> list[ExtractedRelationship]:
        relationships = []
        for clause in clauses:
            self._extract_from_clause(clause, relationships)
        return relationships
        
    def _extract_from_clause(self, clause: ExtractedClause, relationships: list[ExtractedRelationship]):
        if clause.content:
            emitted_targets = set()
            
            for match in self.TARGET_CLAUSE_REGEX.finditer(clause.content):
                target = match.group(1).strip()
                if target not in emitted_targets:
                    context_match = None
                    for cm in self.CLAUSE_REF_REGEX.finditer(clause.content):
                        if match.start() >= cm.start() and match.end() <= cm.end():
                            context_match = cm.group(0).strip()
                            break
                    relationships.append(ExtractedRelationship(
                        source_clause_path=clause.path,
                        target_reference=target,
                        relationship_type=RelationshipType.CROSS_REFERENCES,
                        context=context_match or clause.content,
                        confidence=1.0
                    ))
                    emitted_targets.add(target)
            
            for match in self.TARGET_TABLE_REGEX.finditer(clause.content):
                target = f"Table {match.group(1).strip()}"
                if target not in emitted_targets:
                    context_match = None
                    for cm in self.TABLE_REF_REGEX.finditer(clause.content):
                        if match.start() >= cm.start() and match.end() <= cm.end():
                            context_match = cm.group(0).strip()
                            break
                    relationships.append(ExtractedRelationship(
                        source_clause_path=clause.path,
                        target_reference=target,
                        relationship_type=RelationshipType.CROSS_REFERENCES,
                        context=context_match or clause.content,
                        confidence=1.0
                    ))
                    emitted_targets.add(target)
                
        for child in clause.children:
            self._extract_from_clause(child, relationships)
