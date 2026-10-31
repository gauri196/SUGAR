"""
SUGAR ORM — Assessment entity.

Represents one complete clinical assessment for a patient encounter.
Ties together a verified ClinicalObservation, the FIB-4 score,
risk category, and the collection of model predictions.

Assessment statuses:
  draft      — created but not yet reviewed
  finalized  — clinician has reviewed and accepted
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    patient_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    observation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("clinical_observations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # -----------------------------------------------------------------------
    # FIB-4 result — nullable until the calculation is actually performed.
    # The formula and cutoff logic live in the clinical service layer,
    # never in this model.
    # -----------------------------------------------------------------------
    fib4_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # E.g. "Low Risk", "Indeterminate", "High Risk"
    fib4_risk_category: Mapped[str | None] = mapped_column(String(32), nullable=True)
    # Documents which cutoff was applied, e.g. "<1.30" or "<2.00 (age>=65)"
    fib4_cutoff_applied: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Free-text concordance summary written by the clinical service.
    concordance_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinician_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(  # type: ignore[name-defined]
        "Patient", back_populates="assessments"
    )
    observation: Mapped["ClinicalObservation"] = relationship(  # type: ignore[name-defined]
        "ClinicalObservation", back_populates="assessments"
    )
    predictions: Mapped[list["ModelPrediction"]] = relationship(  # type: ignore[name-defined]
        "ModelPrediction", back_populates="assessment", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Assessment id={self.id!r} "
            f"fib4={self.fib4_score!r} "
            f"status={self.status!r}>"
        )
