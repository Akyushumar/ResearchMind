"""Pydantic schemas for API."""
import uuid
from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field


class TimestampSchema(BaseModel):
    """Base schema with timestamps."""
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class BoundingBox(BaseModel):
    """Bounding box coordinates."""
    x0: float
    y0: float
    x1: float
    y1: float


# --- Jurisdiction ---

class JurisdictionBase(BaseModel):
    """Base jurisdiction."""
    name: str
    code: str
    level: str
    parent_id: uuid.UUID | None = None
    country_code: str
    state_code: str | None = None


class JurisdictionCreate(JurisdictionBase):
    """Create jurisdiction."""
    pass


class JurisdictionUpdate(BaseModel):
    """Update jurisdiction."""
    name: str | None = None
    code: str | None = None
    level: str | None = None
    parent_id: uuid.UUID | None = None
    country_code: str | None = None
    state_code: str | None = None


class JurisdictionRead(JurisdictionBase, TimestampSchema):
    """Read jurisdiction."""
    id: uuid.UUID


class JurisdictionTree(JurisdictionRead):
    """Jurisdiction tree."""
    children: list["JurisdictionTree"] = Field(default_factory=list)


# --- Authority ---

class AuthorityBase(BaseModel):
    """Base authority."""
    name: str
    abbreviation: str
    jurisdiction_id: uuid.UUID
    authority_type: str
    website: str | None = None


class AuthorityCreate(AuthorityBase):
    """Create authority."""
    pass


class AuthorityUpdate(BaseModel):
    """Update authority."""
    name: str | None = None
    abbreviation: str | None = None
    jurisdiction_id: uuid.UUID | None = None
    authority_type: str | None = None
    website: str | None = None


class AuthorityRead(AuthorityBase, TimestampSchema):
    """Read authority."""
    id: uuid.UUID


# --- Regulatory Document ---

class RegulatoryDocumentBase(BaseModel):
    """Base document."""
    title: str
    short_title: str | None = None
    document_type: str
    authority_id: uuid.UUID
    jurisdiction_id: uuid.UUID
    subject_area: str


class RegulatoryDocumentCreate(RegulatoryDocumentBase):
    """Create document."""
    pass


class RegulatoryDocumentUpdate(BaseModel):
    """Update document."""
    title: str | None = None
    short_title: str | None = None
    document_type: str | None = None
    authority_id: uuid.UUID | None = None
    jurisdiction_id: uuid.UUID | None = None
    subject_area: str | None = None


class RegulatoryDocumentRead(RegulatoryDocumentBase, TimestampSchema):
    """Read document."""
    id: uuid.UUID


# --- Document Version ---

class DocumentVersionBase(BaseModel):
    """Base document version."""
    document_id: uuid.UUID
    version_label: str
    year: int
    effective_date: date | None = None
    status: str
    language: str = "en"


class DocumentVersionCreate(DocumentVersionBase):
    """Create document version."""
    document_id: uuid.UUID | None = None


class DocumentVersionUpdate(BaseModel):
    """Update document version."""
    document_id: uuid.UUID | None = None
    version_label: str | None = None
    year: int | None = None
    effective_date: date | None = None
    status: str | None = None
    language: str | None = None


class DocumentVersionRead(DocumentVersionBase, TimestampSchema):
    """Read document version."""
    id: uuid.UUID
    superseded_date: date | None = None
    file_path: str | None = None
    file_hash: str | None = None
    source_url: str | None = None
    total_pages: int | None = None


# --- Amendment ---

class AmendmentBase(BaseModel):
    """Base amendment."""
    document_version_id: uuid.UUID
    amendment_number: str
    title: str | None = None
    effective_date: date | None = None
    description: str | None = None
    status: str


class AmendmentCreate(AmendmentBase):
    """Create amendment."""
    pass


class AmendmentUpdate(BaseModel):
    """Update amendment."""
    document_version_id: uuid.UUID | None = None
    amendment_number: str | None = None
    title: str | None = None
    effective_date: date | None = None
    description: str | None = None
    status: str | None = None


class AmendmentRead(AmendmentBase, TimestampSchema):
    """Read amendment."""
    id: uuid.UUID
    file_path: str | None = None


# --- Clause ---

class ClauseBase(BaseModel):
    """Base clause."""
    document_version_id: uuid.UUID
    clause_number: str
    title: str | None = None
    content: str
    parent_clause_id: uuid.UUID | None = None
    depth: int = 0
    path: str
    clause_type: str
    is_mandatory: bool = True
    effective_date: date | None = None
    start_page: int | None = None
    end_page: int | None = None


class ClauseCreate(ClauseBase):
    """Create clause."""
    pass


class ClauseUpdate(BaseModel):
    """Update clause."""
    document_version_id: uuid.UUID | None = None
    clause_number: str | None = None
    title: str | None = None
    content: str | None = None
    parent_clause_id: uuid.UUID | None = None
    depth: int | None = None
    path: str | None = None
    clause_type: str | None = None
    is_mandatory: bool | None = None
    effective_date: date | None = None
    start_page: int | None = None
    end_page: int | None = None


class ClauseRead(ClauseBase, TimestampSchema):
    """Read clause."""
    id: uuid.UUID


class ClausePath(BaseModel):
    """Clause path."""
    path: list[ClauseRead] = Field(default_factory=list)


# --- Clause Relationship ---

class ClauseRelationshipBase(BaseModel):
    """Base clause relationship."""
    source_clause_id: uuid.UUID
    target_clause_id: uuid.UUID
    relationship_type: str
    context: str | None = None
    extracted_text: str | None = None
    confidence: float = 1.0


class ClauseRelationshipCreate(ClauseRelationshipBase):
    """Create clause relationship."""
    pass


class ClauseRelationshipUpdate(BaseModel):
    """Update clause relationship."""
    source_clause_id: uuid.UUID | None = None
    target_clause_id: uuid.UUID | None = None
    relationship_type: str | None = None
    context: str | None = None
    extracted_text: str | None = None
    confidence: float | None = None


class ClauseRelationshipRead(ClauseRelationshipBase, TimestampSchema):
    """Read clause relationship."""
    id: uuid.UUID


# --- Applicability Rule ---

class ApplicabilityRuleBase(BaseModel):
    """Base applicability rule."""
    clause_id: uuid.UUID
    jurisdiction_id: uuid.UUID | None = None
    building_type: str | None = None
    occupancy_type: str | None = None
    plot_area_min: float | None = None
    plot_area_max: float | None = None
    height_min: float | None = None
    height_max: float | None = None
    special_zone: str | None = None
    effective_from: date | None = None
    effective_until: date | None = None
    notes: str | None = None


class ApplicabilityRuleCreate(ApplicabilityRuleBase):
    """Create applicability rule."""
    pass


class ApplicabilityRuleUpdate(BaseModel):
    """Update applicability rule."""
    clause_id: uuid.UUID | None = None
    jurisdiction_id: uuid.UUID | None = None
    building_type: str | None = None
    occupancy_type: str | None = None
    plot_area_min: float | None = None
    plot_area_max: float | None = None
    height_min: float | None = None
    height_max: float | None = None
    special_zone: str | None = None
    effective_from: date | None = None
    effective_until: date | None = None
    notes: str | None = None


class ApplicabilityRuleRead(ApplicabilityRuleBase, TimestampSchema):
    """Read applicability rule."""
    id: uuid.UUID


# --- Evidence Chunk ---

class EvidenceChunkBase(BaseModel):
    """Base evidence chunk."""
    clause_id: uuid.UUID
    document_version_id: uuid.UUID
    chunk_index: int
    content: str
    token_count: int
    jurisdiction_id: uuid.UUID | None = None
    building_type: str | None = None
    occupancy_type: str | None = None
    topic: str | None = None
    start_page: int | None = None
    end_page: int | None = None
    bbox_json: str | None = None
    source_text: str
    embedding_id: str | None = None
    parser_metadata: str | None = None


class EvidenceChunkCreate(EvidenceChunkBase):
    """Create evidence chunk."""
    pass


class EvidenceChunkUpdate(BaseModel):
    """Update evidence chunk."""
    clause_id: uuid.UUID | None = None
    document_version_id: uuid.UUID | None = None
    chunk_index: int | None = None
    content: str | None = None
    token_count: int | None = None
    jurisdiction_id: uuid.UUID | None = None
    building_type: str | None = None
    occupancy_type: str | None = None
    topic: str | None = None
    start_page: int | None = None
    end_page: int | None = None
    bbox_json: str | None = None
    source_text: str | None = None
    embedding_id: str | None = None
    parser_metadata: str | None = None


class EvidenceChunkRead(EvidenceChunkBase, TimestampSchema):
    """Read evidence chunk."""
    id: uuid.UUID


# --- Ingestion Job ---

class IngestionJobBase(BaseModel):
    """Base ingestion job."""
    document_version_id: uuid.UUID
    status: str
    current_stage: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    error_stage: str | None = None
    retry_count: int = 0
    parser_version: str = "0.1.0"
    pages_processed: int | None = None
    pages_total: int | None = None
    clauses_extracted: int | None = None
    chunks_created: int | None = None


class IngestionJobCreate(IngestionJobBase):
    """Create ingestion job."""
    pass


class IngestionJobUpdate(BaseModel):
    """Update ingestion job."""
    document_version_id: uuid.UUID | None = None
    status: str | None = None
    current_stage: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    error_stage: str | None = None
    retry_count: int | None = None
    parser_version: str | None = None
    pages_processed: int | None = None
    pages_total: int | None = None
    clauses_extracted: int | None = None
    chunks_created: int | None = None


class IngestionJobRead(IngestionJobBase, TimestampSchema):
    """Read ingestion job."""
    id: uuid.UUID
    
    @property
    def progress_pct(self) -> float:
        """Calculate progress percentage."""
        if not self.pages_total or self.pages_total == 0:
            return 0.0
        if not self.pages_processed:
            return 0.0
        return min((self.pages_processed / self.pages_total) * 100, 100.0)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    postgres: str
    qdrant: str
    version: str
