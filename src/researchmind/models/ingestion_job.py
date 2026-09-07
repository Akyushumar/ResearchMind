"""Ingestion job model."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .enums import IngestionStage


class IngestionJob(TimestampMixin, Base):
    """Job tracking for document ingestion."""

    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    document_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("document_versions.id"), index=True)
    status: Mapped[IngestionStage] = mapped_column(
        SQLAlchemyEnum(IngestionStage), default=IngestionStage.QUEUED
    )
    current_stage: Mapped[IngestionStage] = mapped_column(
        SQLAlchemyEnum(IngestionStage), default=IngestionStage.QUEUED
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_stage: Mapped[IngestionStage | None] = mapped_column(SQLAlchemyEnum(IngestionStage), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    parser_version: Mapped[str] = mapped_column(String(50), default="0.1.0")
    pages_processed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pages_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clauses_extracted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunks_created: Mapped[int | None] = mapped_column(Integer, nullable=True)

    document_version: Mapped["DocumentVersion"] = relationship(back_populates="ingestion_jobs")

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<IngestionJob(id={self.id}, status={self.status})>"
