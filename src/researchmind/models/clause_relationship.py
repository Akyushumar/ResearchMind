"""Clause relationship model."""
import uuid

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .enums import RelationshipType


class ClauseRelationship(TimestampMixin, Base):
    """Relationship between clauses."""

    __tablename__ = "clause_relationships"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    source_clause_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clauses.id"), index=True)
    target_clause_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("clauses.id"), index=True, nullable=True)
    relationship_type: Mapped[RelationshipType] = mapped_column(SQLAlchemyEnum(RelationshipType, native_enum=False, length=50))
    context: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    source_clause: Mapped["Clause"] = relationship(
        foreign_keys=[source_clause_id], back_populates="outgoing_relationships"
    )
    target_clause: Mapped["Clause | None"] = relationship(
        foreign_keys=[target_clause_id], back_populates="incoming_relationships"
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<ClauseRelationship(source={self.source_clause_id}, target={self.target_clause_id}, type={self.relationship_type})>"
