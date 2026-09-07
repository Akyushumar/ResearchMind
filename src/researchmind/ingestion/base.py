from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from researchmind.models.enums import ClauseType, RelationshipType


@dataclass
class TextBlock:
    """A block of text on a page with position information."""
    text: str
    page_number: int
    block_index: int
    x0: float
    y0: float
    x1: float
    y1: float
    font_size: float | None = None
    font_name: str | None = None
    is_bold: bool = False


@dataclass
class PageContent:
    """Physical page representation."""
    page_number: int  # 1-indexed
    text: str
    width: float
    height: float
    blocks: list[TextBlock] = field(default_factory=list)


@dataclass
class ParsedDocument:
    """What the document physically contains."""
    file_path: str
    pages: list[PageContent]
    total_pages: int
    metadata: dict = field(default_factory=dict)  # PDF metadata: title, author, etc.


@dataclass
class DetectedSection:
    """A detected section in the document hierarchy."""
    title: str | None
    content: str
    level: int  # 0 = top-level part, 1 = section, 2 = clause, etc.
    clause_number: str | None = None
    clause_type: ClauseType = ClauseType.CLAUSE
    start_page: int | None = None
    end_page: int | None = None
    children: list[DetectedSection] = field(default_factory=list)


@dataclass
class DocumentStructure:
    """Detected hierarchy of the document."""
    title: str | None
    sections: list[DetectedSection]
    metadata: dict = field(default_factory=dict)


@dataclass
class ExtractedClause:
    """A clause ready for database storage."""
    clause_number: str
    title: str | None
    content: str
    depth: int
    path: str  # materialized path: "3.4.2.1"
    clause_type: ClauseType
    is_mandatory: bool = True
    start_page: int | None = None
    end_page: int | None = None
    children: list[ExtractedClause] = field(default_factory=list)


@dataclass
class ExtractedRelationship:
    """A detected cross-reference between clauses."""
    source_clause_path: str
    target_reference: str  # raw text: "as per clause 4.2.3"
    relationship_type: RelationshipType
    context: str | None = None
    confidence: float = 1.0


@dataclass
class EvidenceChunkData:
    """An evidence chunk ready for storage."""
    clause_path: str  # links back to clause via path
    chunk_index: int
    content: str
    token_count: int
    source_text: str  # exact original before cleaning
    start_page: int | None = None
    end_page: int | None = None
    bbox: dict | None = None  # {"x0": float, "y0": float, "x1": float, "y1": float}


class DocumentParser(ABC):
    """Stage 1: Raw file → pages/blocks with position info."""

    @abstractmethod
    async def parse(self, file_path: Path) -> ParsedDocument:
        """Parse a document file into pages and text blocks."""
        pass

    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """File extensions this parser supports."""
        pass


class StructureDetector(ABC):
    """Stage 2: Pages/blocks → hierarchical document structure."""

    @abstractmethod
    async def detect(self, parsed: ParsedDocument) -> DocumentStructure:
        """Detect the hierarchical structure of a parsed document."""
        pass


class ClauseExtractor(ABC):
    """Stage 3: Document structure → clause objects ready for storage."""

    @abstractmethod
    async def extract(self, structure: DocumentStructure) -> list[ExtractedClause]:
        """Extract clauses from document structure."""
        pass


class RelationshipExtractor(ABC):
    """Stage 4: Clauses → cross-references and relationships."""

    @abstractmethod
    async def extract(
        self, clauses: list[ExtractedClause]
    ) -> list[ExtractedRelationship]:
        """Extract relationships between clauses."""
        pass


class ClauseChunker(ABC):
    """Stage 5: Clauses → evidence chunks for embedding."""

    @abstractmethod
    async def chunk(
        self, clauses: list[ExtractedClause]
    ) -> list[EvidenceChunkData]:
        """Split clauses into evidence chunks suitable for embedding."""
        pass
