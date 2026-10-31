"""
SUGAR — Assessment Orchestration Service Layer.

Handles:
- Patient resolution (pseudonymized / internal UUID).
- Report & unverified observation registration with deduplication.
- Clinician verification and value correction.
- Clinical assessment orchestration with verified FIB-4 calculation.
- Assessment detail and history retrieval.
- Transaction management and append-only audit event logging.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.models import (
    Patient,
    Report,
    ClinicalObservation,
    Assessment,
    AuditEvent,
)
from backend.schemas.orchestration import (
    ReportRegistrationRequest,
    ReportRegistrationResponse,
    ReportDetailResponse,
    ObservationVerificationRequest,
    ObservationVerificationResponse,
    AssessmentCreateRequest,
    AssessmentDetailResponse,
    AssessmentListResponse,
)
from backend.services.fib4 import calculate_and_interpret_fib4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# 1. Register Extracted Report
# ---------------------------------------------------------------------------

def register_extracted_report(
    db: Session,
    request: ReportRegistrationRequest,
) -> ReportRegistrationResponse:
    """
    Persist report metadata and newly extracted clinical observations.
    All newly registered observations are strictly marked as unverified.
    """
    # 1. Patient resolution
    patient: Optional[Patient] = None
    if request.patient_id:
        patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
        if not patient:
            raise ValueError(f"Patient with id '{request.patient_id}' not found.")
    elif request.external_subject_id:
        patient = (
            db.query(Patient)
            .filter(Patient.external_subject_id == request.external_subject_id)
            .first()
        )
        if not patient:
            patient = Patient(external_subject_id=request.external_subject_id)
            db.add(patient)
            db.flush()
    else:
        patient = Patient()
        db.add(patient)
        db.flush()

    # 2. Idempotency / Deduplication check
    if request.file_sha256:
        existing_report = (
            db.query(Report)
            .filter(
                Report.patient_id == patient.id,
                Report.file_sha256 == request.file_sha256,
            )
            .first()
        )
        if existing_report:
            obs = (
                db.query(ClinicalObservation)
                .filter(ClinicalObservation.report_id == existing_report.id)
                .first()
            )
            return ReportRegistrationResponse(
                success=True,
                report_id=existing_report.id,
                patient_id=patient.id,
                observation_id=obs.id if obs else "",
                extraction_status=existing_report.extraction_status,
                is_verified=obs.is_verified_by_doctor if obs else False,
                message="Report already registered (idempotent match on content hash).",
            )

    # 3. Create Report record
    report = Report(
        patient_id=patient.id,
        original_filename=request.original_filename,
        media_type=request.media_type,
        file_size_bytes=request.file_size_bytes,
        file_sha256=request.file_sha256,
        extraction_status=request.extraction_status,
        uploaded_by=request.uploaded_by,
    )
    db.add(report)
    db.flush()

    # 4. Create ClinicalObservation record (Unverified)
    vals = request.clinical_values
    obs = ClinicalObservation(
        patient_id=patient.id,
        report_id=report.id,
        age_years=vals.age_years if vals else None,
        bmi=vals.bmi if vals else None,
        platelets_10e9_l=vals.platelets_10e9_l if vals else None,
        ast_u_l=vals.ast_u_l if vals else None,
        alt_u_l=vals.alt_u_l if vals else None,
        wbc_10e9_l=vals.wbc_10e9_l if vals else None,
        rbc_10e12_l=vals.rbc_10e12_l if vals else None,
        hgb_g_dl=vals.hgb_g_dl if vals else None,
        glucose_mg_dl=vals.glucose_mg_dl if vals else None,
        cholesterol_mg_dl=vals.cholesterol_mg_dl if vals else None,
        cap_steatosis_dbm=vals.cap_steatosis_dbm if vals else None,
        etiology=vals.etiology if vals else None,
        ascites=vals.ascites if vals else None,
        jaundice=vals.jaundice if vals else None,
        hepatomegaly=vals.hepatomegaly if vals else None,
        is_verified_by_doctor=False,  # Enforce unverified
    )
    db.add(obs)
    db.flush()

    # 5. Append-only AuditEvent
    audit = AuditEvent(
        event_type="REPORT_REGISTERED",
        entity_name="reports",
        entity_id=report.id,
        performed_by=request.uploaded_by,
        metadata_json=json.dumps({
            "original_filename": report.original_filename,
            "patient_id": patient.id,
            "observation_id": obs.id,
            "extraction_status": report.extraction_status,
        }),
    )
    db.add(audit)
    db.commit()

    return ReportRegistrationResponse(
        success=True,
        report_id=report.id,
        patient_id=patient.id,
        observation_id=obs.id,
        extraction_status=report.extraction_status,
        is_verified=False,
        message="Report registered successfully. Observations marked as unverified.",
    )


# ---------------------------------------------------------------------------
# 2. Retrieve Report Detail
# ---------------------------------------------------------------------------

def get_report_detail(db: Session, report_id: str) -> ReportDetailResponse:
    """Retrieve report metadata and linked observation without exposing raw OS paths."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise ValueError(f"Report with id '{report_id}' not found.")

    obs = (
        db.query(ClinicalObservation)
        .filter(ClinicalObservation.report_id == report.id)
        .first()
    )

    obs_dict: Optional[Dict[str, Any]] = None
    if obs:
        obs_dict = {
            "id": obs.id,
            "patient_id": obs.patient_id,
            "is_verified_by_doctor": obs.is_verified_by_doctor,
            "verified_by": obs.verified_by,
            "verified_at": obs.verified_at.isoformat() if obs.verified_at else None,
            "age_years": obs.age_years,
            "bmi": obs.bmi,
            "platelets_10e9_l": obs.platelets_10e9_l,
            "ast_u_l": obs.ast_u_l,
            "alt_u_l": obs.alt_u_l,
            "wbc_10e9_l": obs.wbc_10e9_l,
            "rbc_10e12_l": obs.rbc_10e12_l,
            "hgb_g_dl": obs.hgb_g_dl,
            "glucose_mg_dl": obs.glucose_mg_dl,
            "cholesterol_mg_dl": obs.cholesterol_mg_dl,
            "cap_steatosis_dbm": obs.cap_steatosis_dbm,
        }

    return ReportDetailResponse(
        id=report.id,
        patient_id=report.patient_id,
        original_filename=report.original_filename,
        media_type=report.media_type,
        file_size_bytes=report.file_size_bytes,
        extraction_status=report.extraction_status,
        uploaded_by=report.uploaded_by,
        created_at=report.created_at.isoformat(),
        observation=obs_dict,
    )


# ---------------------------------------------------------------------------
# 3. Verify or Correct Clinical Observations
# ---------------------------------------------------------------------------

def verify_clinical_observation(
    db: Session,
    observation_id: str,
    request: ObservationVerificationRequest,
) -> ObservationVerificationResponse:
    """
    Explicit clinician verification of extracted observation.
    Allows correcting laboratory values, recording verifier identity, timestamp, and audit event.
    """
    obs = (
        db.query(ClinicalObservation)
        .filter(ClinicalObservation.id == observation_id)
        .first()
    )
    if not obs:
        raise ValueError(f"Clinical observation with id '{observation_id}' not found.")

    if not request.verified_by or not request.verified_by.strip():
        raise ValueError("Verifier identity ('verified_by') cannot be empty.")

    # Apply corrected values if provided
    if request.verified_values:
        v = request.verified_values
        if v.age_years is not None: obs.age_years = v.age_years
        if v.bmi is not None: obs.bmi = v.bmi
        if v.platelets_10e9_l is not None: obs.platelets_10e9_l = v.platelets_10e9_l
        if v.ast_u_l is not None: obs.ast_u_l = v.ast_u_l
        if v.alt_u_l is not None: obs.alt_u_l = v.alt_u_l
        if v.wbc_10e9_l is not None: obs.wbc_10e9_l = v.wbc_10e9_l
        if v.rbc_10e12_l is not None: obs.rbc_10e12_l = v.rbc_10e12_l
        if v.hgb_g_dl is not None: obs.hgb_g_dl = v.hgb_g_dl
        if v.glucose_mg_dl is not None: obs.glucose_mg_dl = v.glucose_mg_dl
        if v.cholesterol_mg_dl is not None: obs.cholesterol_mg_dl = v.cholesterol_mg_dl
        if v.cap_steatosis_dbm is not None: obs.cap_steatosis_dbm = v.cap_steatosis_dbm
        if v.etiology is not None: obs.etiology = v.etiology
        if v.ascites is not None: obs.ascites = v.ascites
        if v.jaundice is not None: obs.jaundice = v.jaundice
        if v.hepatomegaly is not None: obs.hepatomegaly = v.hepatomegaly

    now = _utcnow()
    obs.is_verified_by_doctor = True
    obs.verified_by = request.verified_by.strip()
    obs.verified_at = now

    audit = AuditEvent(
        event_type="VALUES_VERIFIED",
        entity_name="clinical_observations",
        entity_id=obs.id,
        performed_by=obs.verified_by,
        metadata_json=json.dumps({
            "verified_by": obs.verified_by,
            "verified_at": now.isoformat(),
            "notes": request.clinician_notes,
        }),
    )
    db.add(audit)
    db.commit()
    db.refresh(obs)

    return ObservationVerificationResponse(
        success=True,
        observation_id=obs.id,
        patient_id=obs.patient_id,
        is_verified_by_doctor=True,
        verified_by=obs.verified_by,
        verified_at=now.isoformat(),
        clinical_values={
            "age": obs.age_years,
            "bmi": obs.bmi,
            "platelets": obs.platelets_10e9_l,
            "ast": obs.ast_u_l,
            "alt": obs.alt_u_l,
            "wbc": obs.wbc_10e9_l,
            "rbc": obs.rbc_10e12_l,
            "hgb": obs.hgb_g_dl,
        },
        message="Observation successfully verified by clinician.",
    )


# ---------------------------------------------------------------------------
# 4. Create Clinical Assessment
# ---------------------------------------------------------------------------

def create_clinical_assessment(
    db: Session,
    request: AssessmentCreateRequest,
) -> AssessmentDetailResponse:
    """
    Orchestrate clinical assessment calculation and persistence.
    CRITICAL SAFEGUARDS:
      - Rejects unverified observations.
      - Rejects patient/observation mismatches.
      - Rejects missing or non-positive FIB-4 inputs.
    """
    # 1. Fetch Patient
    patient = db.query(Patient).filter(Patient.id == request.patient_id).first()
    if not patient:
        raise ValueError(f"Patient with id '{request.patient_id}' not found.")

    # 2. Fetch Observation
    obs = (
        db.query(ClinicalObservation)
        .filter(ClinicalObservation.id == request.observation_id)
        .first()
    )
    if not obs:
        raise ValueError(f"ClinicalObservation with id '{request.observation_id}' not found.")

    # 3. Prevent cross-patient mismatch
    if obs.patient_id != patient.id:
        raise ValueError(
            f"Observation '{obs.id}' belongs to patient '{obs.patient_id}', "
            f"which does not match requested patient '{patient.id}'."
        )

    # 4. CRITICAL: Reject unverified observations
    if not obs.is_verified_by_doctor:
        raise ValueError(
            "Cannot calculate assessment: Clinical observation has not been verified by a clinician. "
            "Please review and verify values before calculating FIB-4."
        )

    # 5. Validate required FIB-4 parameters
    missing = []
    if obs.age_years is None: missing.append("age_years")
    if obs.ast_u_l is None: missing.append("ast_u_l")
    if obs.alt_u_l is None: missing.append("alt_u_l")
    if obs.platelets_10e9_l is None: missing.append("platelets_10e9_l")

    if missing:
        raise ValueError(
            f"Cannot calculate FIB-4: Missing required clinical measurements: {missing}. "
            "Values cannot be coerced to zero."
        )

    # 6. Calculate FIB-4 using clinical service
    interp = calculate_and_interpret_fib4(
        age=obs.age_years,
        ast=obs.ast_u_l,
        alt=obs.alt_u_l,
        platelets=obs.platelets_10e9_l,
    )

    # 7. Persist Assessment
    assessment = Assessment(
        patient_id=patient.id,
        observation_id=obs.id,
        fib4_score=interp.score,
        fib4_risk_category=interp.risk_category,
        fib4_cutoff_applied=interp.threshold_set.boundary_rules,
        concordance_summary=interp.interpretation,
        clinician_notes=request.clinician_notes,
        status="finalized" if request.clinician_notes else "draft",
    )
    db.add(assessment)
    db.flush()

    # 8. Log AuditEvent
    audit = AuditEvent(
        event_type="ASSESSMENT_CREATED",
        entity_name="assessments",
        entity_id=assessment.id,
        performed_by=obs.verified_by,
        metadata_json=json.dumps({
            "fib4_score": interp.score,
            "risk_category": interp.risk_category,
            "cutoff_applied": interp.threshold_set.boundary_rules,
        }),
    )
    db.add(audit)
    db.commit()
    db.refresh(assessment)

    return AssessmentDetailResponse(
        id=assessment.id,
        patient_id=assessment.patient_id,
        observation_id=assessment.observation_id,
        fib4_score=assessment.fib4_score,
        fib4_risk_category=assessment.fib4_risk_category,
        fib4_cutoff_applied=assessment.fib4_cutoff_applied,
        concordance_summary=assessment.concordance_summary,
        clinician_notes=assessment.clinician_notes,
        status=assessment.status,
        created_at=assessment.created_at.isoformat(),
        observation_values={
            "age": obs.age_years,
            "platelets": obs.platelets_10e9_l,
            "ast": obs.ast_u_l,
            "alt": obs.alt_u_l,
            "bmi": obs.bmi,
        },
    )


# ---------------------------------------------------------------------------
# 5. Retrieve Assessment Detail & History
# ---------------------------------------------------------------------------

def get_assessment_detail(db: Session, assessment_id: str) -> AssessmentDetailResponse:
    """Retrieve an assessment by ID with linked observation values."""
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise ValueError(f"Assessment with id '{assessment_id}' not found.")

    obs = assessment.observation
    return AssessmentDetailResponse(
        id=assessment.id,
        patient_id=assessment.patient_id,
        observation_id=assessment.observation_id,
        fib4_score=assessment.fib4_score,
        fib4_risk_category=assessment.fib4_risk_category,
        fib4_cutoff_applied=assessment.fib4_cutoff_applied,
        concordance_summary=assessment.concordance_summary,
        clinician_notes=assessment.clinician_notes,
        status=assessment.status,
        created_at=assessment.created_at.isoformat(),
        observation_values={
            "age": obs.age_years if obs else None,
            "platelets": obs.platelets_10e9_l if obs else None,
            "ast": obs.ast_u_l if obs else None,
            "alt": obs.alt_u_l if obs else None,
            "bmi": obs.bmi if obs else None,
        } if obs else None,
    )


def list_patient_assessments(
    db: Session,
    patient_id: str,
    skip: int = 0,
    limit: int = 20,
) -> AssessmentListResponse:
    """Retrieve paginated assessment history for a patient."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise ValueError(f"Patient with id '{patient_id}' not found.")

    query = (
        db.query(Assessment)
        .filter(Assessment.patient_id == patient_id)
        .order_by(Assessment.created_at.desc())
    )
    total = query.count()
    assessments = query.offset(skip).limit(limit).all()

    items = []
    for a in assessments:
        obs = a.observation
        items.append(
            AssessmentDetailResponse(
                id=a.id,
                patient_id=a.patient_id,
                observation_id=a.observation_id,
                fib4_score=a.fib4_score,
                fib4_risk_category=a.fib4_risk_category,
                fib4_cutoff_applied=a.fib4_cutoff_applied,
                concordance_summary=a.concordance_summary,
                clinician_notes=a.clinician_notes,
                status=a.status,
                created_at=a.created_at.isoformat(),
                observation_values={
                    "age": obs.age_years if obs else None,
                    "platelets": obs.platelets_10e9_l if obs else None,
                    "ast": obs.ast_u_l if obs else None,
                    "alt": obs.alt_u_l if obs else None,
                    "bmi": obs.bmi if obs else None,
                } if obs else None,
            )
        )

    return AssessmentListResponse(
        patient_id=patient_id,
        total=total,
        items=items,
    )
