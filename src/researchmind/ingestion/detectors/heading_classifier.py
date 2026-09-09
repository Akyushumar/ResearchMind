from dataclasses import dataclass, field
import statistics

from researchmind.ingestion.base import TextBlock
from researchmind.models.enums import ClauseType
from researchmind.ingestion.detectors.clause_number_parser import ClauseNumberParser, ParsedClauseNumber


@dataclass
class HeadingClassification:
    """Classification result for a text block."""
    is_heading: bool
    numbering_depth: int    # from clause number: count of dots (for decimal) or 0
    semantic_level: int     # from font/position heuristics (0=chapter, etc.)
    clause_number: str | None
    clause_type: ClauseType
    numbering_type: str     # "decimal" | "letter" | "roman" | "label" | "body"


@dataclass
class HeadingConfig:
    """Tuneable parameters for heading detection, adjustable per document type."""
    min_heading_size_delta: float = 1.5   # points above median body font
    chapter_min_font_size: float = 16.0   # absolute minimum for chapter headings
    bold_is_heading_at_depth: int = 2     # bold text at body size treated as heading up to this depth
    uppercase_is_chapter: bool = True     # ALL CAPS → chapter-level heading
    
    # Font size → semantic level mapping (descending)
    level_thresholds: list[float] = field(default_factory=lambda: [16.0, 13.0, 12.0, 11.0])


class FontBasedHeadingClassifier:
    def __init__(self, config: HeadingConfig | None = None, number_parser: ClauseNumberParser | None = None):
        self.config = config or HeadingConfig()
        self.parser = number_parser or ClauseNumberParser()
        self.median_body_font_size: float = 11.0  # default fallback

    def calibrate(self, blocks: list[TextBlock]) -> None:
        """Compute median body font size from a page/document's blocks."""
        sizes = [b.font_size for b in blocks if b.font_size is not None]
        if sizes:
            # We assume the most common font size or median is the body text size.
            # Using mode is often more robust for body text.
            try:
                self.median_body_font_size = statistics.mode(sizes)
            except statistics.StatisticsError:
                self.median_body_font_size = statistics.median(sizes)

    def classify(self, block: TextBlock, parent_depth: int = 0) -> HeadingClassification:
        """Classifies a block as a heading or body text.
        
        Args:
            block: The TextBlock to classify.
            parent_depth: The current section hierarchy depth (used for assigning levels to non-decimal nodes).
        """
        parsed = self.parser.parse(block.text)
        font_size = block.font_size or self.median_body_font_size
        is_bold = block.is_bold
        
        # Determine semantic level from font heuristics
        semantic_level = 99
        is_heading_by_font = False
        
        if self.config.uppercase_is_chapter and block.text.isupper() and font_size >= self.config.chapter_min_font_size:
            semantic_level = 0
            is_heading_by_font = True
        elif font_size >= self.median_body_font_size + self.config.min_heading_size_delta:
            is_heading_by_font = True
            # Find matching level threshold
            for level, threshold in enumerate(self.config.level_thresholds):
                if font_size >= threshold:
                    semantic_level = level
                    break
            # Fallback if thresholds are weird
            if semantic_level == 99:
                semantic_level = 1
        elif is_bold and font_size >= self.median_body_font_size:
            # Bold text at or above body size can be a heading if it has a number or is explicitly treated as such
            if parsed and parsed.numbering_type == "decimal":
                is_heading_by_font = True
                semantic_level = 3
            elif parsed and parsed.numbering_type == "label":
                is_heading_by_font = True
                semantic_level = parent_depth + 1
        
        # Special cases for non-decimal labels that should be headings even if not strictly satisfying bold/size heuristics
        if parsed:
            if parsed.numbering_type == "letter":
                return HeadingClassification(
                    is_heading=True, numbering_depth=0, semantic_level=10,
                    clause_number=parsed.normalized, clause_type=ClauseType.SUB_CLAUSE, numbering_type="letter"
                )
            elif parsed.numbering_type == "roman":
                return HeadingClassification(
                    is_heading=True, numbering_depth=0, semantic_level=11,
                    clause_number=parsed.normalized, clause_type=ClauseType.SUB_CLAUSE, numbering_type="roman"
                )
            elif parsed.numbering_type == "label":
                # Labels like "Table X-Y", "Proviso", "Note"
                if is_bold or is_heading_by_font:
                    norm_lower = parsed.normalized.lower()
                    c_type = ClauseType.TABLE if "table" in norm_lower else (
                        ClauseType.PROVISO if ("proviso" in norm_lower or "provided" in norm_lower) else (
                        ClauseType.NOTE if "note" in norm_lower else ClauseType.CLAUSE
                    ))
                    return HeadingClassification(
                        is_heading=True, numbering_depth=0, semantic_level=12,
                        clause_number=parsed.normalized, clause_type=c_type, numbering_type="label"
                    )

        if is_heading_by_font:
            # It's a heading based on font. It may or may not have a parsed clause number.
            c_type = ClauseType.PART if semantic_level == 0 else (
                ClauseType.SECTION if semantic_level == 1 else ClauseType.CLAUSE
            )
            return HeadingClassification(
                is_heading=True,
                numbering_depth=parsed.numbering_depth if parsed else 0,
                semantic_level=semantic_level,
                clause_number=parsed.normalized if parsed else None,
                clause_type=c_type,
                numbering_type=parsed.numbering_type if parsed else "body"
            )

        # Fallback to body text
        return HeadingClassification(
            is_heading=False,
            numbering_depth=0,
            semantic_level=99,
            clause_number=None,
            clause_type=ClauseType.CLAUSE,
            numbering_type="body"
        )
