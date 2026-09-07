"""Applicability rule model."""
import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class ApplicabilityRule(TimestampMixin, Base):
    """Rule defining the applicability of a clause."""

    __tablename__ = "applicability_rules"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    clause_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clauses.id"), index=True)
    jurisdiction_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("jurisdictions.id"), nullable=True, index=True
    )
    building_type: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    occupancy_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    plot_area_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    plot_area_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    height_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    special_zone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    clause: Mapped["Clause"] = relationship(back_populates="applicability_rules")
    jurisdiction: Mapped["Jurisdiction | None"] = relationship()

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<ApplicabilityRule(id={self.id}, clause_id={self.clause_id})>"
