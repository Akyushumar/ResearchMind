"""Authority model."""
import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Authority(TimestampMixin, Base):
    """Regulatory or publishing authority."""

    __tablename__ = "authorities"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    abbreviation: Mapped[str] = mapped_column(String(50), index=True)
    jurisdiction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jurisdictions.id"))
    authority_type: Mapped[str] = mapped_column(String(100))
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)

    jurisdiction: Mapped["Jurisdiction"] = relationship(back_populates="authorities")
    documents: Mapped[list["RegulatoryDocument"]] = relationship(back_populates="authority")

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Authority(id={self.id}, abbreviation='{self.abbreviation}', name='{self.name}')>"
