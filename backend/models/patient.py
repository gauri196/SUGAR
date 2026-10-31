"""
SUGAR ORM — Patient entity.

Stores only the minimum necessary identifiers. No raw PII is stored.
All patient references use an internal UUID. An optional external_subject_id
field holds a pre-pseudonymised token supplied by the calling system.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    # Optional pre-pseudonymised token supplied by the calling system.
    # Must be unique when present; NULL means no external identifier was given.
    external_subject_id: Mapped[str | None] = mapped_column(
        String(128),
        unique=True,
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )

    # Relationships (back-populated from child tables)
    reports: Mapped[list["Report"]] = relationship(  # type: ignore[name-defined]
        "Report", back_populates="patient", cascade="all, delete-orphan"
    )
    observations: Mapped[list["ClinicalObservation"]] = relationship(  # type: ignore[name-defined]
        "ClinicalObservation", back_populates="patient", cascade="all, delete-orphan"
    )
    assessments: Mapped[list["Assessment"]] = relationship(  # type: ignore[name-defined]
        "Assessment", back_populates="patient", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Patient id={self.id!r} external={self.external_subject_id!r}>"
