"""
SUGAR ORM — Report entity.

Tracks metadata about an uploaded laboratory report document.
The raw file is stored on disk under a configurable path; only the
path and a SHA-256 content hash are stored here.

Extraction statuses:
  pending          — file received, not yet parsed
  parsed           — structured values extracted successfully
  partial          — some values extracted; manual review required
  failed           — extraction pipeline errored
  manual_fallback  — clinician entered values directly; no file extraction
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


EXTRACTION_STATUSES = {
    "pending",
    "parsed",
    "partial",
    "failed",
    "manual_fallback",
}


class Report(Base):
    __tablename__ = "reports"

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
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    media_type: Mapped[str] = mapped_column(
        String(128), nullable=False, default="application/octet-stream"
    )
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # SHA-256 hex digest of the file content.
    file_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Relative path under the configured storage root (not an absolute OS path).
    storage_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    extraction_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending"
    )
    uploaded_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    # Relationships
    patient: Mapped["Patient"] = relationship(  # type: ignore[name-defined]
        "Patient", back_populates="reports"
    )
    observation: Mapped["ClinicalObservation | None"] = relationship(  # type: ignore[name-defined]
        "ClinicalObservation",
        back_populates="report",
        uselist=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Report id={self.id!r} "
            f"file={self.original_filename!r} "
            f"status={self.extraction_status!r}>"
        )
