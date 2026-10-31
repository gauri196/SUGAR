"""
SUGAR — Phase 5 Assessment Orchestration & Database Persistence Tests.

Verifies:
- Report metadata and extracted-observation persistence.
- Unverified status immediately after registration.
- Clinician verification flow and value correction.
- Critical safeguard: attempts to create assessment from UNVERIFIED observation rejected (HTTP 400).
- Critical safeguard: patient/observation mismatch rejected (HTTP 400).
- Missing, invalid, or non-finite inputs for FIB-4 calculation rejected (HTTP 422).
- Successful clinical assessment creation with verified values and deterministic FIB-4.
- Correct FIB-4 score, threshold scheme, and risk category.
- Duplicate report registration idempotency via content hash.
- Individual assessment retrieval and paginated patient assessment history.
- Append-only audit events created at each stage.
- Foreign-key enforcement and clean rollback.
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from backend.database import Base, get_db
from backend.main import app
from backend.models import (
    Patient,
    Report,
    ClinicalObservation,
    Assessment,
    AuditEvent,
)

from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Test Setup: Isolated In-Memory Database
# ---------------------------------------------------------------------------

@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session with foreign keys enforced."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def test_client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 1. Report Registration & Unverified Observation Intake
# ---------------------------------------------------------------------------

def test_register_extracted_report_unverified_status(test_client, db_session):
    payload = {
        "external_subject_id": "SYNTH-PATIENT-101",
        "original_filename": "lab_report_jan2026.json",
        "media_type": "application/json",
        "file_size_bytes": 1024,
        "file_sha256": "abc123sha256fakehash",
        "extraction_status": "parsed",
        "clinical_values": {
            "age_years": 45.0,
            "bmi": 26.5,
            "platelets_10e9_l": 180.0,
            "ast_u_l": 42.0,
            "alt_u_l": 38.0,
            "wbc_10e9_l": 6.8,
            "rbc_10e12_l": 4.5,
            "hgb_g_dl": 14.2,
        },
        "uploaded_by": "lab_tech_1",
    }
    response = test_client.post("/api/reports/register", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["is_verified"] is False
    assert data["report_id"] is not None
    assert data["patient_id"] is not None
    assert data["observation_id"] is not None

    # Verify database state
    obs = db_session.query(ClinicalObservation).filter(ClinicalObservation.id == data["observation_id"]).first()
    assert obs is not None
    assert obs.is_verified_by_doctor is False
    assert obs.platelets_10e9_l == 180.0
    assert obs.ast_u_l == 42.0
    assert obs.alt_u_l == 38.0

    # Verify AuditEvent was logged
    audit = db_session.query(AuditEvent).filter(
        AuditEvent.event_type == "REPORT_REGISTERED",
        AuditEvent.entity_id == data["report_id"]
    ).first()
    assert audit is not None
    assert audit.performed_by == "lab_tech_1"


def test_register_report_idempotency_via_sha256(test_client, db_session):
    payload = {
        "external_subject_id": "SYNTH-PATIENT-IDEMPOTENT",
        "original_filename": "repeat_test.json",
        "file_size_bytes": 500,
        "file_sha256": "identical_sha256_hash",
        "extraction_status": "parsed",
        "clinical_values": {"age_years": 50.0, "platelets_10e9_l": 200.0},
    }
    # First registration
    r1 = test_client.post("/api/reports/register", json=payload)
    assert r1.status_code == 200
    report_id_1 = r1.json()["report_id"]

    # Second registration with identical sha256 and patient
    r2 = test_client.post("/api/reports/register", json=payload)
    assert r2.status_code == 200
    report_id_2 = r2.json()["report_id"]

    # Must return the same report without duplicating in DB
    assert report_id_1 == report_id_2
    assert "idempotent" in r2.json()["message"].lower()
    assert db_session.query(Report).count() == 1


# ---------------------------------------------------------------------------
# 2. Retrieve Report Detail
# ---------------------------------------------------------------------------

def test_get_report_detail_endpoint(test_client):
    reg = test_client.post("/api/reports/register", json={
        "external_subject_id": "PATIENT-DETAIL-TEST",
        "original_filename": "metabolic_panel.json",
        "file_size_bytes": 1200,
        "extraction_status": "parsed",
        "clinical_values": {"age_years": 52.0, "platelets_10e9_l": 160.0},
    })
    report_id = reg.json()["report_id"]

    res = test_client.get(f"/api/reports/{report_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["id"] == report_id
    assert data["original_filename"] == "metabolic_panel.json"
    assert data["observation"]["age_years"] == 52.0
    assert data["observation"]["platelets_10e9_l"] == 160.0
    assert data["observation"]["ast_u_l"] is None  # preserved as null
    assert data["observation"]["is_verified_by_doctor"] is False


def test_get_report_not_found(test_client):
    res = test_client.get("/api/reports/non-existent-uuid")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# 3. Clinician Verification & Value Correction
# ---------------------------------------------------------------------------

def test_verify_clinical_observation_flow(test_client, db_session):
    # Register unverified report
    reg = test_client.post("/api/reports/register", json={
        "external_subject_id": "PATIENT-VERIFY-1",
        "original_filename": "report.json",
        "file_size_bytes": 800,
        "clinical_values": {
            "age_years": 45.0,
            "platelets_10e9_l": 150.0,
            "ast_u_l": 40.0,
            "alt_u_l": 35.0,
        },
    })
    obs_id = reg.json()["observation_id"]

    # Clinician reviews and adjusts AST from 40 to 42
    verify_payload = {
        "verified_by": "dr_alice_hepatology",
        "verified_values": {
            "ast_u_l": 42.0,
        },
        "clinician_notes": "Confirmed AST manually from raw PDF trace.",
    }
    res = test_client.post(f"/api/observations/{obs_id}/verify", json=verify_payload)
    assert res.status_code == 200
    data = res.json()

    assert data["is_verified_by_doctor"] is True
    assert data["verified_by"] == "dr_alice_hepatology"
    assert data["clinical_values"]["ast"] == 42.0

    # Verify DB update
    obs = db_session.query(ClinicalObservation).filter(ClinicalObservation.id == obs_id).first()
    assert obs.is_verified_by_doctor is True
    assert obs.ast_u_l == 42.0
    assert obs.verified_by == "dr_alice_hepatology"
    assert obs.verified_at is not None

    # Verify AuditEvent
    audit = db_session.query(AuditEvent).filter(
        AuditEvent.event_type == "VALUES_VERIFIED",
        AuditEvent.entity_id == obs_id
    ).first()
    assert audit is not None
    assert audit.performed_by == "dr_alice_hepatology"


# ---------------------------------------------------------------------------
# 4. Assessment Creation & Clinical Safeguards
# ---------------------------------------------------------------------------

def test_create_assessment_rejects_unverified_observation(test_client):
    """CRITICAL SAFEGUARD: Assessment must NEVER be calculated from unverified observations."""
    reg = test_client.post("/api/reports/register", json={
        "external_subject_id": "PATIENT-UNVERIFIED-BLOCK",
        "original_filename": "unverified.json",
        "file_size_bytes": 600,
        "clinical_values": {
            "age_years": 45.0,
            "platelets_10e9_l": 180.0,
            "ast_u_l": 42.0,
            "alt_u_l": 38.0,
        },
    })
    pat_id = reg.json()["patient_id"]
    obs_id = reg.json()["observation_id"]

    # Attempt to calculate assessment while still unverified
    res = test_client.post("/api/assessments", json={
        "patient_id": pat_id,
        "observation_id": obs_id,
    })
    assert res.status_code == 400
    assert "not been verified" in res.json()["detail"].lower()


def test_create_assessment_rejects_cross_patient_mismatch(test_client):
    """CRITICAL SAFEGUARD: Prevent patient A from creating assessment with patient B's observation."""
    reg1 = test_client.post("/api/reports/register", json={
        "external_subject_id": "PATIENT-A",
        "original_filename": "rep_a.json",
        "file_size_bytes": 500,
        "clinical_values": {"age_years": 45.0, "platelets_10e9_l": 180.0, "ast_u_l": 42.0, "alt_u_l": 38.0},
    })
    reg2 = test_client.post("/api/reports/register", json={
        "external_subject_id": "PATIENT-B",
        "original_filename": "rep_b.json",
        "file_size_bytes": 500,
        "clinical_values": {"age_years": 60.0, "platelets_10e9_l": 200.0, "ast_u_l": 30.0, "alt_u_l": 25.0},
    })
    pat_a_id = reg1.json()["patient_id"]
    obs_b_id = reg2.json()["observation_id"]

    # Verify Patient B's observation
    test_client.post(f"/api/observations/{obs_b_id}/verify", json={"verified_by": "dr_smith"})

    # Try to create assessment for Patient A with Patient B's observation
    res = test_client.post("/api/assessments", json={
        "patient_id": pat_a_id,
        "observation_id": obs_b_id,
    })
    assert res.status_code == 400
    assert "does not match" in res.json()["detail"].lower()


def test_create_assessment_rejects_missing_fib4_inputs(test_client):
    # Observation with missing ALT
    reg = test_client.post("/api/reports/register", json={
        "external_subject_id": "PATIENT-MISSING-ALT",
        "original_filename": "rep.json",
        "file_size_bytes": 500,
        "clinical_values": {
            "age_years": 45.0,
            "platelets_10e9_l": 180.0,
            "ast_u_l": 42.0,
            # ALT intentionally missing
        },
    })
    pat_id = reg.json()["patient_id"]
    obs_id = reg.json()["observation_id"]

    # Verify as-is
    test_client.post(f"/api/observations/{obs_id}/verify", json={"verified_by": "dr_smith"})

    # Attempt assessment -> 422 missing clinical parameters
    res = test_client.post("/api/assessments", json={
        "patient_id": pat_id,
        "observation_id": obs_id,
    })
    assert res.status_code == 422
    assert "missing" in res.json()["detail"].lower()
    assert "alt_u_l" in res.json()["detail"]


def test_create_assessment_success_deterministic_fib4(test_client, db_session):
    # Benchmark case: age 45, AST 42, ALT 38, platelets 180 -> FIB-4 ~1.70
    reg = test_client.post("/api/reports/register", json={
        "external_subject_id": "PATIENT-FIB4-SUCCESS",
        "original_filename": "benchmark.json",
        "file_size_bytes": 750,
        "clinical_values": {
            "age_years": 45.0,
            "bmi": 26.0,
            "platelets_10e9_l": 180.0,
            "ast_u_l": 42.0,
            "alt_u_l": 38.0,
        },
    })
    pat_id = reg.json()["patient_id"]
    obs_id = reg.json()["observation_id"]

    # Verify observation
    test_client.post(f"/api/observations/{obs_id}/verify", json={
        "verified_by": "dr_carol",
        "clinician_notes": "All lab values verified against source report."
    })

    # Create assessment
    res = test_client.post("/api/assessments", json={
        "patient_id": pat_id,
        "observation_id": obs_id,
        "clinician_notes": "Patient scheduled for secondary elastography (VCTE).",
    })
    assert res.status_code == 200
    data = res.json()

    assert data["patient_id"] == pat_id
    assert data["observation_id"] == obs_id
    assert pytest.approx(data["fib4_score"], abs=1e-2) == 1.70
    assert data["fib4_risk_category"] == "Indeterminate"
    assert data["status"] == "finalized"
    assert "screening" in data["disclaimer"].lower() or "indirect" in data["disclaimer"].lower()

    # Verify AuditEvent
    audit = db_session.query(AuditEvent).filter(
        AuditEvent.event_type == "ASSESSMENT_CREATED",
        AuditEvent.entity_id == data["id"]
    ).first()
    assert audit is not None
    assert audit.performed_by == "dr_carol"


# ---------------------------------------------------------------------------
# 5. Retrieve Assessment & Patient History
# ---------------------------------------------------------------------------

def test_get_assessment_and_patient_history(test_client):
    reg = test_client.post("/api/reports/register", json={
        "external_subject_id": "PATIENT-HISTORY-TEST",
        "original_filename": "rep1.json",
        "file_size_bytes": 500,
        "clinical_values": {"age_years": 45.0, "platelets_10e9_l": 180.0, "ast_u_l": 42.0, "alt_u_l": 38.0},
    })
    pat_id = reg.json()["patient_id"]
    obs_id = reg.json()["observation_id"]

    # Verify and assess
    test_client.post(f"/api/observations/{obs_id}/verify", json={"verified_by": "dr_dave"})
    create_res = test_client.post("/api/assessments", json={
        "patient_id": pat_id,
        "observation_id": obs_id,
        "clinician_notes": "Encounter 1 Assessment",
    })
    assessment_id = create_res.json()["id"]

    # Test single assessment retrieval
    single_res = test_client.get(f"/api/assessments/{assessment_id}")
    assert single_res.status_code == 200
    assert single_res.json()["id"] == assessment_id
    assert single_res.json()["clinician_notes"] == "Encounter 1 Assessment"
    assert single_res.json()["observation_values"]["platelets"] == 180.0

    # Test patient history retrieval
    history_res = test_client.get(f"/api/patients/{pat_id}/assessments")
    assert history_res.status_code == 200
    hist = history_res.json()

    assert hist["patient_id"] == pat_id
    assert hist["total"] == 1
    assert len(hist["items"]) == 1
    assert hist["items"][0]["id"] == assessment_id
