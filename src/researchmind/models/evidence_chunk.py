"""Evidence chunk model."""
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, Computed, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.types import UserDefinedType

from .base import Base, TimestampMixin

class TSVectorType(UserDefinedType):
    cache_ok = True
    def get_col_spec(self, **kw):
        return "TSVECTOR"

class search_vector_expr(FunctionElement):
    type = TSVectorType()
    name = 'search_vector_expr'

@compiles(search_vector_expr, 'postgresql')
def compile_search_vector_expr_postgresql(element, compiler, **kw):
    return (
        "setweight(to_tsvector('english', coalesce(clause_path, '')), 'A') || "
        "setweight(to_tsvector('english', coalesce(hierarchy_context, '')), 'B') || "
        "setweight(to_tsvector('english', coalesce(content, '')), 'C')"
    )

@compiles(search_vector_expr, 'sqlite')
def compile_search_vector_expr_sqlite(element, compiler, **kw):
    return "''"

class EvidenceChunk(TimestampMixin, Base):
    """A vectorized chunk of evidence."""

    __tablename__ = "evidence_chunks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    clause_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clauses.id"), index=True)
    document_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_versions.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)

    # Structured queryable fields
    jurisdiction_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("jurisdictions.id"), nullable=True, index=True
    )
    building_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    occupancy_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    topic: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)

    # Page-level provenance
    start_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bbox_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_text: Mapped[str] = mapped_column(Text)

    # Vector store reference
    embedding_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Versioning & Embedding Metadata
    chunk_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    embedding_dimension: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    # Hierarchy Context
    clause_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hierarchy_context: Mapped[str | None] = mapped_column(Text, nullable=True)

    # FTS
    search_vector = mapped_column(TSVectorType, Computed(search_vector_expr()))

    clause: Mapped["Clause"] = relationship(back_populates="evidence_chunks")
    document_version: Mapped["DocumentVersion"] = relationship()
    jurisdiction: Mapped["Jurisdiction | None"] = relationship()

    __table_args__ = (
        Index("ix_evidence_chunks_search_vector", "search_vector", postgresql_using="gin"),
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<EvidenceChunk(id={self.id}, clause_id={self.clause_id})>"
