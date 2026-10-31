"""
SUGAR ORM — ModelPrediction entity.

Records the output of one model for one assessment. One assessment may
have multiple prediction rows — one per model called.

model_identifier values used by the current inference service:
  model_a_baseline_lr   — Logistic Regression, 5 features, Target B
  model_d_expanded_rf   — Random Forest, 8 features, Target B

feature_payload_json stores the exact numeric inputs forwarded to the
model so predictions can be reproduced independently of the observation row.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ModelPrediction(Base):
    __tablename__ = "model_predictions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    assessment_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # -----------------------------------------------------------------------
    # Model identification — must match the artifact filename / registry key.
    # -----------------------------------------------------------------------
    model_identifier: Mapped[str] = mapped_column(String(128), nullable=False)
    model_version: Mapped[str] = mapped_column(
        String(64), nullable=False, default="unknown"
    )
    # Human-readable description of what the model predicts, e.g.
    # "Target B: F1-F2 vs F3-F4 (advanced fibrosis)"
    target_definition: Mapped[str] = mapped_column(String(256), nullable=False)

    # -----------------------------------------------------------------------
    # Prediction output
    # -----------------------------------------------------------------------
    predicted_class: Mapped[int] = mapped_column(Integer, nullable=False)
    # Probability of the positive class (class 1). Range [0.0, 1.0].
    probability: Mapped[float] = mapped_column(Float, nullable=False)

    # JSON snapshot of the exact feature values passed to the model.
    # Stored as TEXT to avoid dialect-specific JSON column types.
    feature_payload_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    # Relationships
    assessment: Mapped["Assessment"] = relationship(  # type: ignore[name-defined]
        "Assessment", back_populates="predictions"
    )

    def __repr__(self) -> str:
        return (
            f"<ModelPrediction id={self.id!r} "
            f"model={self.model_identifier!r} "
            f"class={self.predicted_class} "
            f"prob={self.probability:.4f}>"
        )
