"""
SUGAR ORM — AuditEvent entity.

Append-only log of significant state transitions. Rows in this table
must never be updated or deleted by the application.

Presence of this table does not constitute regulatory compliance.
It provides a developer-level audit trail for debugging and review.

Standardised event_type values (extend as needed):
  REPORT_UPLOADED
  EXTRACTION_COMPLETED
  EXTRACTION_FAILED
  VALUES_VERIFIED
  ASSESSMENT_CREATED
  PREDICTION_EXECUTED
  ASSESSMENT_FINALIZED
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Name of the table the event refers to, e.g. "assessments"
    entity_name: Mapped[str] = mapped_column(String(64), nullable=False)
    # UUID of the specific row the event refers to.
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    # Identifier of the actor who triggered the event (e.g. clinician ID).
    # NULL when the event is system-generated.
    performed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Minimal structured metadata serialised as JSON text.
    # Keep small — do not store full record snapshots here.
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<AuditEvent id={self.id!r} "
            f"type={self.event_type!r} "
            f"entity={self.entity_name!r}/{self.entity_id!r}>"
        )
