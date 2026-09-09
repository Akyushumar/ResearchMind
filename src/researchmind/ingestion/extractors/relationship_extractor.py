from researchmind.ingestion.base import RelationshipExtractor, ExtractedClause, ExtractedRelationship
from researchmind.models.enums import RelationshipType
import re


class RegexRelationshipExtractor(RelationshipExtractor):
    """
    Extracts explicit cross-references from clause text using regex patterns.
    """
    
    # "as per|in accordance with|subject to|mentioned in|specified in|provided under|laid down in" + Regulation|Clause|Rule|Section + decimal
    # "refer|see|vide" + Regulation|Clause|Rule|Section + decimal
    # "refer|see|as per|in" + Table + table identifier
    
    # We define patterns that capture the context around the reference, the reference itself, and the type of reference.
    # We'll use a single pass to find all references.
    
    REF_KEYWORDS = r"(?:as\s+per|in\s+accordance\s+with|subject\s+to|mentioned\s+in|specified\s+in|provided\s+under|laid\s+down\s+in|refer|see|vide|in)"
    CLAUSE_KEYWORDS = r"(?:Regulation|Clause|Rule|Section|Chapter)s?"
    NUMBER_PATTERN = r"(\d+(?:\.\d+)*)"  # 8.2.1
    TABLE_PATTERN = r"([A-Z0-9-]+)" # 8-B
    
    # Pattern for clauses
    CLAUSE_REF_REGEX = re.compile(
        rf"(?P<context>[^.]*{REF_KEYWORDS}(?:\s+provisions\s+of)?\s+{CLAUSE_KEYWORDS}\s+{NUMBER_PATTERN}[^.]*\.?)",
        re.IGNORECASE
    )
    
    # Just extracting the target for a clause reference
    TARGET_CLAUSE_REGEX = re.compile(
        rf"{REF_KEYWORDS}(?:\s+provisions\s+of)?\s+{CLAUSE_KEYWORDS}\s+{NUMBER_PATTERN}",
        re.IGNORECASE
    )
    
    # Pattern for tables
    TABLE_REF_REGEX = re.compile(
        rf"(?P<context>[^.]*{REF_KEYWORDS}\s+Table\s+{TABLE_PATTERN}[^.]*\.?)",
        re.IGNORECASE
    )
    
    TARGET_TABLE_REGEX = re.compile(
        rf"{REF_KEYWORDS}\s+Table\s+{TABLE_PATTERN}",
        re.IGNORECASE
    )
    
    async def extract(self, clauses: list[ExtractedClause]) -> list[ExtractedRelationship]:
        relationships = []
        
        for clause in clauses:
            self._extract_from_clause(clause, relationships)
            
        print(f"Extracted {len(relationships)} total relationships from {len(clauses)} root clauses.")
        for r in relationships:
            print(f"  - {r.source_clause_path} -> {r.target_reference}")
            
        return relationships
        
    def _extract_from_clause(self, clause: ExtractedClause, relationships: list[ExtractedRelationship]):
        if not clause.content:
            return
        if clause.content:
            emitted_targets = set()
            
        emitted_targets = set()
        
        # 1. Clause references
        for match in self.TARGET_CLAUSE_REGEX.finditer(clause.content):
            target = match.group(1).strip()
            
            # Find the sentence context
            context_match = None
            for cm in self.CLAUSE_REF_REGEX.finditer(clause.content):
                if match.start() >= cm.start() and match.end() <= cm.end():
                    context_match = cm.group(0).strip()
                    break
            # 1. Clause references
            for match in self.TARGET_CLAUSE_REGEX.finditer(clause.content):
                target = match.group(1).strip()
                
                # Find the sentence context
                context_match = None
                for cm in self.CLAUSE_REF_REGEX.finditer(clause.content):
                    if match.start() >= cm.start() and match.end() <= cm.end():
                        context_match = cm.group(0).strip()
                        break
                        
                if target not in emitted_targets:
                    relationships.append(ExtractedRelationship(
                        source_clause_path=clause.path,
                        target_reference=target,
                        relationship_type=RelationshipType.CROSS_REFERENCES,
                        context=context_match or clause.content,
                        confidence=1.0
                    ))
                    emitted_targets.add(target)
                    
            if target not in emitted_targets:
                relationships.append(ExtractedRelationship(
                    source_clause_path=clause.path,
                    target_reference=target,
                    relationship_type=RelationshipType.CROSS_REFERENCES,
                    context=context_match or clause.content,
                    confidence=1.0
                ))
                emitted_targets.add(target)
            # 2. Table references
            for match in self.TARGET_TABLE_REGEX.finditer(clause.content):
                target_id = match.group(1).strip()
                target = f"Table {target_id}"
                
        # 2. Table references
        for match in self.TARGET_TABLE_REGEX.finditer(clause.content):
            # Target should probably include "Table" for clarity in linking later, 
            # or just the identifier. Let's use "Table X"
            target_id = match.group(1).strip()
            target = f"Table {target_id}"
            
            context_match = None
            for cm in self.TABLE_REF_REGEX.finditer(clause.content):
                if match.start() >= cm.start() and match.end() <= cm.end():
                    context_match = cm.group(0).strip()
                    break
            
            if target not in emitted_targets:
                relationships.append(ExtractedRelationship(
                    source_clause_path=clause.path,
                    target_reference=target,
                    relationship_type=RelationshipType.CROSS_REFERENCES,
                    context=context_match or clause.content,
                    confidence=1.0
                ))
                emitted_targets.add(target)
                context_match = None
                for cm in self.TABLE_REF_REGEX.finditer(clause.content):
                    if match.start() >= cm.start() and match.end() <= cm.end():
                        context_match = cm.group(0).strip()
                        break
                
        # Recurse
                if target not in emitted_targets:
                    relationships.append(ExtractedRelationship(
                        source_clause_path=clause.path,
                        target_reference=target,
                        relationship_type=RelationshipType.CROSS_REFERENCES,
                        context=context_match or clause.content,
                        confidence=1.0
                    ))
                    emitted_targets.add(target)
                
        # Always recurse
        for child in clause.children:
            self._extract_from_clause(child, relationships)
