"""Clause model."""
import uuid
from datetime import date

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .enums import ClauseType


class Clause(TimestampMixin, Base):
    """A structural part of a regulatory document."""

    __tablename__ = "clauses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_versions.id"))
    clause_number: Mapped[str] = mapped_column(String(50), index=True)
    clause_number: Mapped[str | None] = mapped_column(String(50), index=True, nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    parent_clause_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("clauses.id"), nullable=True)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    path: Mapped[str] = mapped_column(String(500), index=True)
    clause_type: Mapped[ClauseType] = mapped_column(SQLAlchemyEnum(ClauseType))
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_page: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    document_version: Mapped["DocumentVersion"] = relationship(back_populates="clauses")
    parent_clause: Mapped["Clause | None"] = relationship(back_populates="children", remote_side=[id])
    children: Mapped[list["Clause"]] = relationship(back_populates="parent_clause")
    outgoing_relationships: Mapped[list["ClauseRelationship"]] = relationship(
        foreign_keys="ClauseRelationship.source_clause_id", back_populates="source_clause"
    )
    incoming_relationships: Mapped[list["ClauseRelationship"]] = relationship(
        foreign_keys="ClauseRelationship.target_clause_id", back_populates="target_clause"
    )
    applicability_rules: Mapped[list["ApplicabilityRule"]] = relationship(back_populates="clause")
    evidence_chunks: Mapped[list["EvidenceChunk"]] = relationship(back_populates="clause")

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Clause(id={self.id}, path='{self.path}')>"
