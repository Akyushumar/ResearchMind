"""Document-related models."""
import uuid
from datetime import date

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .enums import AmendmentStatus, DocumentType, VersionStatus


class RegulatoryDocument(TimestampMixin, Base):
    """A primary regulatory document."""

    __tablename__ = "regulatory_documents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(500))
    short_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_type: Mapped[DocumentType] = mapped_column(SQLAlchemyEnum(DocumentType))
    authority_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("authorities.id"))
    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jurisdictions.id"))
    subject_area: Mapped[str] = mapped_column(String(200))

    # Relationships
    authority: Mapped["Authority"] = relationship(back_populates="documents")
    jurisdiction: Mapped["Jurisdiction"] = relationship()
    versions: Mapped[list["DocumentVersion"]] = relationship(back_populates="document")

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<RegulatoryDocument(id={self.id}, title='{self.title[:30]}...')>"


class DocumentVersion(TimestampMixin, Base):
    """A specific version of a regulatory document."""

    __tablename__ = "document_versions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("regulatory_documents.id"))
    version_label: Mapped[str] = mapped_column(String(200))
    year: Mapped[int] = mapped_column(Integer)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    superseded_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[VersionStatus] = mapped_column(SQLAlchemyEnum(VersionStatus))
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    document: Mapped["RegulatoryDocument"] = relationship(back_populates="versions")
    amendments: Mapped[list["Amendment"]] = relationship(back_populates="document_version")
    clauses: Mapped[list["Clause"]] = relationship(back_populates="document_version")
    ingestion_jobs: Mapped[list["IngestionJob"]] = relationship(back_populates="document_version")

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<DocumentVersion(id={self.id}, version_label='{self.version_label}')>"


class Amendment(TimestampMixin, Base):
    """An amendment to a document version."""

    __tablename__ = "amendments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_versions.id"))
    amendment_number: Mapped[str] = mapped_column(String(100))
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    status: Mapped[AmendmentStatus] = mapped_column(SQLAlchemyEnum(AmendmentStatus))

    # Relationship
    document_version: Mapped["DocumentVersion"] = relationship(back_populates="amendments")

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Amendment(id={self.id}, amendment_number='{self.amendment_number}')>"
