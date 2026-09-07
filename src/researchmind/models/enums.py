"""Enumeration definitions for data models."""
import enum


class JurisdictionLevel(str, enum.Enum):
    """Level of jurisdiction."""
    NATIONAL = "national"
    STATE = "state"
    DISTRICT = "district"
    MUNICIPAL = "municipal"


class DocumentType(str, enum.Enum):
    """Type of regulatory document."""
    CODE = "code"
    BYLAW = "bylaw"
    STANDARD = "standard"
    GUIDELINE = "guideline"
    CIRCULAR = "circular"
    NOTIFICATION = "notification"


class VersionStatus(str, enum.Enum):
    """Status of a document version."""
    DRAFT = "draft"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


class ClauseType(str, enum.Enum):
    """Type of document clause."""
    PART = "part"
    SECTION = "section"
    CLAUSE = "clause"
    SUB_CLAUSE = "sub_clause"
    TABLE = "table"
    FIGURE = "figure"
    NOTE = "note"
    PROVISO = "proviso"
    SCHEDULE = "schedule"
    APPENDIX = "appendix"


class RelationshipType(str, enum.Enum):
    """Type of relationship between clauses."""
    REFERENCES = "references"
    AMENDS = "amends"
    SUPERSEDES = "supersedes"
    CONFLICTS_WITH = "conflicts_with"
    ELABORATES = "elaborates"
    RESTRICTS = "restricts"
    EXEMPTS = "exempts"
    CROSS_REFERENCES = "cross_references"


class IngestionStage(str, enum.Enum):
    """Stage of the ingestion process."""
    QUEUED = "queued"
    PARSING = "parsing"
    STRUCTURING = "structuring"
    EXTRACTING_METADATA = "extracting_metadata"
    EXTRACTING_RELATIONSHIPS = "extracting_relationships"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


class AmendmentStatus(str, enum.Enum):
    """Status of a document amendment."""
    PENDING = "pending"
    APPLIED = "applied"
    WITHDRAWN = "withdrawn"
