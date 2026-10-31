"""
SUGAR — Assessment Orchestration & Database Persistence Pydantic Schemas.

Defines schemas for:
- Report registration & clinical observation intake.
- Clinician verification / correction.
- Clinical assessment creation with FIB-4 calculation.
- Assessment detail & patient assessment history retrieval.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from backend.schemas.clinical import ClinicalObservationSchema


class ReportRegistrationRequest(BaseModel):
    """Payload to register an extracted report and its raw observation values."""
    external_subject_id: Optional[str] = Field(
        None, description="Pre-pseudonymised patient token (creates or associates patient)"
    )
    patient_id: Optional[str] = Field(
        None, description="Direct internal UUID of existing patient if known"
    )
    original_filename: str = Field(..., description="Original report filename")
    media_type: str = Field("application/json", description="MIME type of document")
    file_size_bytes: int = Field(0, description="Size of file in bytes")
    file_sha256: Optional[str] = Field(None, description="SHA-256 digest for deduplication")
    extraction_status: str = Field("parsed", description="Status: parsed, partial, etc.")
    clinical_values: Optional[ClinicalObservationSchema] = Field(
        None, description="Structured clinical observation values (nulls preserved)"
    )
    field_provenance_json: Optional[str] = Field(
        None, description="Serialized field-level provenance metadata"
    )
    uploaded_by: Optional[str] = Field(None, description="Uploader or system agent identifier")
    idempotency_key: Optional[str] = Field(None, description="Client idempotency token")


class ReportRegistrationResponse(BaseModel):
    """Confirmation of report and unverified observation registration."""
    success: bool
    report_id: str
    patient_id: str
    observation_id: str
    extraction_status: str
    is_verified: bool
    message: str


class ReportDetailResponse(BaseModel):
    """Detailed report metadata and associated unverified observation."""
    id: str
    patient_id: str
    original_filename: str
    media_type: str
    file_size_bytes: int
    extraction_status: str
    uploaded_by: Optional[str]
    created_at: str
    observation: Optional[Dict[str, Any]] = None


class ObservationVerificationRequest(BaseModel):
    """Explicit clinician verification and value adjustment payload."""
    verified_by: str = Field(..., description="Clinician identifier (development-only identity)")
    verified_values: Optional[ClinicalObservationSchema] = Field(
        None, description="Clinician-confirmed or adjusted clinical values"
    )
    clinician_notes: Optional[str] = Field(None, description="Clinical notes or rationale")


class ObservationVerificationResponse(BaseModel):
    """Confirmation of observation verification."""
    success: bool
    observation_id: str
    patient_id: str
    is_verified_by_doctor: bool
    verified_by: str
    verified_at: str
    clinical_values: Dict[str, Optional[float]]
    message: str


class AssessmentCreateRequest(BaseModel):
    """Request to create a clinical assessment from a verified observation."""
    patient_id: str = Field(..., description="Internal UUID of patient")
    observation_id: str = Field(..., description="Internal UUID of verified ClinicalObservation")
    clinician_notes: Optional[str] = Field(None, description="Optional assessment notes")


class AssessmentDetailResponse(BaseModel):
    """Structured assessment record with FIB-4 score and risk categorization."""
    id: str
    patient_id: str
    observation_id: str
    fib4_score: float
    fib4_risk_category: str
    fib4_cutoff_applied: str
    concordance_summary: Optional[str]
    clinician_notes: Optional[str]
    status: str
    created_at: str
    observation_values: Optional[Dict[str, Optional[float]]] = None
    disclaimer: str = (
        "FIB-4 is an indirect screening and risk-stratification marker. "
        "It does not provide a definitive medical diagnosis or replace histological staging."
    )


class AssessmentListResponse(BaseModel):
    """Paginated list of patient assessments."""
    patient_id: str
    total: int
    items: List[AssessmentDetailResponse]
