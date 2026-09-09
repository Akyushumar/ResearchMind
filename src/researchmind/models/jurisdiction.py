"""Jurisdiction model."""
import uuid

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .enums import JurisdictionLevel


class Jurisdiction(TimestampMixin, Base):
    """Jurisdiction representing a geographical or administrative region."""
    
    __tablename__ = "jurisdictions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    level: Mapped[JurisdictionLevel] = mapped_column(SQLAlchemyEnum(JurisdictionLevel, native_enum=False, length=50))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("jurisdictions.id"), nullable=True)
    country_code: Mapped[str] = mapped_column(String(10))
    state_code: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Relationships
    parent: Mapped["Jurisdiction | None"] = relationship(back_populates="children", remote_side=[id])
    children: Mapped[list["Jurisdiction"]] = relationship(back_populates="parent")
    authorities: Mapped[list["Authority"]] = relationship(back_populates="jurisdiction")

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Jurisdiction(id={self.id}, code='{self.code}', name='{self.name}')>"
