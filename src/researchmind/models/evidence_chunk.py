"""Evidence chunk model."""
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


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

    # Parser metadata
    parser_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)

    clause: Mapped["Clause"] = relationship(back_populates="evidence_chunks")
    document_version: Mapped["DocumentVersion"] = relationship()
    jurisdiction: Mapped["Jurisdiction | None"] = relationship()

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<EvidenceChunk(id={self.id}, clause_id={self.clause_id})>"
