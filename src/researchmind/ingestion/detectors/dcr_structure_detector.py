from researchmind.ingestion.base import (
    StructureDetector, 
    ParsedDocument, 
    DocumentStructure, 
    DetectedSection,
)
from researchmind.models.enums import ClauseType
from researchmind.ingestion.detectors.heading_classifier import FontBasedHeadingClassifier

from dataclasses import dataclass

@dataclass
class _StackFrame:
    level: int
    section: DetectedSection


class DCRStructureDetector(StructureDetector):
    """
    Detects hierarchical document structure in Indian DCR/NBC-style documents.
    
    Pipeline:
    1. Calibrate heading classifier against all blocks (compute median font)
    2. Classify every TextBlock as heading vs body
    3. Build a stack-based hierarchy
    4. Track page provenance (start_page, end_page) per section
    """
    
    def __init__(self, classifier: FontBasedHeadingClassifier | None = None):
        self.classifier = classifier or FontBasedHeadingClassifier()
        
    async def detect(self, parsed: ParsedDocument) -> DocumentStructure:
        # Collect all blocks from the document
        all_blocks = []
        for page in parsed.pages:
            all_blocks.extend(page.blocks)
            
        if not all_blocks:
            return DocumentStructure(title=None, sections=[], metadata=parsed.metadata)
            
        # 1. Calibrate font heuristics
        self.classifier.calibrate(all_blocks)
        
        # 2. Build tree
        root_sections: list[DetectedSection] = []
        stack: list[_StackFrame] = []
        
        # Sometimes there's document metadata before the first chapter
        doc_title = None
        
        for block in all_blocks:
            # We determine parent depth for labeling (provisos etc.)
            parent_depth = stack[-1].level if stack else -1
            
            classification = self.classifier.classify(block, parent_depth=parent_depth)
            
            if classification.is_heading:
                # If we encounter a Chapter/Part heading, it might be the document title
                if not doc_title and classification.semantic_level == 0:
                    doc_title = block.text
                
                # Pop the stack until we find a parent that is strictly higher in the hierarchy (i.e., lower level number)
                while stack and stack[-1].level >= classification.semantic_level:
                    stack.pop()
                    
                new_section = DetectedSection(
                    title=block.text,
                    content="",
                    level=classification.semantic_level,
                    clause_number=classification.clause_number,
                    clause_type=classification.clause_type,
                    start_page=block.page_number,
                    end_page=block.page_number,
                    children=[]
                )
                
                if stack:
                    stack[-1].section.children.append(new_section)
                else:
                    root_sections.append(new_section)
                    
                stack.append(_StackFrame(level=classification.semantic_level, section=new_section))
            else:
                # It's body text
                if stack:
                    current_section = stack[-1].section
                    if current_section.content:
                        current_section.content += "\n" + block.text
                    else:
                        current_section.content = block.text
                    # Update end_page
                    current_section.end_page = max(current_section.end_page or 0, block.page_number)
                else:
                    # Body text before any heading
                    # This often happens with document prefaces.
                    pass
                    
        # Post-process: some sections might have their title duplicated in content if not careful, 
        # but our logic doesn't append the heading block to content, which is correct.

        return DocumentStructure(
            title=doc_title,
            sections=root_sections,
            metadata=parsed.metadata
        )
