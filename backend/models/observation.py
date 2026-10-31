"""
SUGAR ORM — ClinicalObservation entity.

Stores extracted and clinician-verified laboratory values for a single
encounter. All measurement columns are nullable so that absent values
remain NULL rather than being silently coerced to zero.

Columns that feed the current models:
  Core (Model A / FIB-4): age_years, platelets_10e9_l, ast_u_l, alt_u_l, bmi
  Hematology expansion (Models B/D): wbc_10e9_l, rbc_10e12_l, hgb_g_dl
  Metabolic research context: glucose_mg_dl, cholesterol_mg_dl, cap_steatosis_dbm
  Clinical context: etiology, ascites, jaundice, hepatomegaly

Note on AST/ALT units
---------------------
The production model artifacts (routine_clinical_baseline.pkl and
expanded_fibrosis_model.pkl) were trained on the Egyptian HCV dataset
where "AST 1" and "ALT 1" are normalized ratio variables, NOT standard
U/L serum concentrations. This column stores the real clinical U/L value.
The inference service is responsible for any required transformation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ClinicalObservation(Base):
    __tablename__ = "clinical_observations"

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
    # Nullable — a report row may exist before observation is linked.
    report_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("reports.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # -----------------------------------------------------------------------
    # Core clinical variables (required for FIB-4 and Model A)
    # -----------------------------------------------------------------------
    age_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    bmi: Mapped[float | None] = mapped_column(Float, nullable=True)
    platelets_10e9_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    ast_u_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    alt_u_l: Mapped[float | None] = mapped_column(Float, nullable=True)

    # -----------------------------------------------------------------------
    # Hematology expansion (Models B / D)
    # -----------------------------------------------------------------------
    wbc_10e9_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    rbc_10e12_l: Mapped[float | None] = mapped_column(Float, nullable=True)
    hgb_g_dl: Mapped[float | None] = mapped_column(Float, nullable=True)

    # -----------------------------------------------------------------------
    # Metabolic / advanced research context
    # -----------------------------------------------------------------------
    glucose_mg_dl: Mapped[float | None] = mapped_column(Float, nullable=True)
    cholesterol_mg_dl: Mapped[float | None] = mapped_column(Float, nullable=True)
    # VCTE CAP steatosis score (dB/m)
    cap_steatosis_dbm: Mapped[float | None] = mapped_column(Float, nullable=True)

    # -----------------------------------------------------------------------
    # Disease etiology and clinical stigmata
    # -----------------------------------------------------------------------
    # Free-text constrained by application logic: hcv, hbv, mash, alcohol, other
    etiology: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ascites: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    jaundice: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    hepatomegaly: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # -----------------------------------------------------------------------
    # Verification governance
    # -----------------------------------------------------------------------
    is_verified_by_doctor: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    verified_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(  # type: ignore[name-defined]
        "Patient", back_populates="observations"
    )
    report: Mapped["Report | None"] = relationship(  # type: ignore[name-defined]
        "Report", back_populates="observation"
    )
    assessments: Mapped[list["Assessment"]] = relationship(  # type: ignore[name-defined]
        "Assessment", back_populates="observation"
    )

    def __repr__(self) -> str:
        return (
            f"<ClinicalObservation id={self.id!r} "
            f"patient={self.patient_id!r} "
            f"verified={self.is_verified_by_doctor}>"
        )
