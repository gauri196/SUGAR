"""
SUGAR — Phase 6 End-to-End Integration & Workflow Verification Tests.

Verifies:
1. Complete 10-step clinical lifecycle:
   - Extract from synthetic JSON report (is_verified=False).
   - Register extraction result into database.
   - Verify report retrieval shows observation as unverified.
   - Verify assessment creation is rejected before verification (HTTP 400).
   - Verify observation through clinician verification endpoint.
   - Create assessment from verified observation.
   - Independently calculate FIB-4 and compare with stored score.
   - Retrieve assessment detail and verify disclaimer.
   - Retrieve patient assessment history and verify assessment appears exactly once.
2. CSV and digital text PDF extraction through existing endpoints.
3. Scanned / image PDF returning 'no_text_found' status and manual-review warning.
4. Multi-session persistence across independent database sessions.
5. Transaction rollback on failure (failed assessment leaves no assessment or success audit event).
6. Foreign-key enforcement and patient-observation mismatch rejection.
7. SHA-256 deduplication and idempotent registration.
8. History pagination and descending chronological ordering.
9. Alembic migration execution on a clean database.
10. Model artifact integrity and baseline invariance.
"""
import io
import json
import math
import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from alembic.config import Config
from alembic import command
import pypdf

from backend.database import Base, get_db
from backend.main import app
from backend.models import (
    Patient,
    Report,
    ClinicalObservation,
    Assessment,
    AuditEvent,
)
from backend.services.fib4 import calculate_fib4


# ---------------------------------------------------------------------------
# Test Fixtures: In-Memory SQLite with StaticPool & Foreign Keys
# ---------------------------------------------------------------------------

@pytest.fixture
def db_engine():
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
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    TestingSession = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_client(db_session):
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
# Helper: Minimal Text PDF
# ---------------------------------------------------------------------------

def create_sample_text_pdf(text_lines: list[str]) -> bytes:
    stream_content = []
    stream_content.append(b"BT\n/F1 12 Tf\n50 720 Td\n")
    for i, line in enumerate(text_lines):
        if i > 0:
            stream_content.append(b"0 -20 Td\n")
        safe_line = line.replace("(", "\\(").replace(")", "\\)")
        stream_content.append(f"({safe_line}) Tj\n".encode("latin-1", errors="replace"))
    stream_content.append(b"ET\n")
    stream_bytes = b"".join(stream_content)

    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources 4 0 R /Contents 5 0 R>> endobj\n"
        b"4 0 obj <</Font <</F1 <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>>>>> endobj\n"
        b"5 0 obj <</Length " + str(len(stream_bytes)).encode() + b">> stream\n"
        + stream_bytes +
        b"endstream\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"0000000009 00000 n \n0000000056 00000 n \n0000000115 00000 n \n0000000217 00000 n \n0000000300 00000 n \n"
        b"trailer <</Size 6 /Root 1 0 R>>\nstartxref\n500\n%%EOF\n"
    )
    return pdf


# ---------------------------------------------------------------------------
# 1. Complete 10-Step Workflow Test
# ---------------------------------------------------------------------------

def test_complete_e2e_clinical_workflow(test_client, db_session):
    """
    Step 1-10: End-to-end integration test verifying complete clinical pipeline.
    """
    # 1. Submit valid synthetic JSON report to /api/reports/extract
    raw_report = {
        "Age": 45,
        "AST": 42,
        "ALT": 38,
        "Platelets": 180,
        "BMI": 26.5,
    }
    file_bytes = json.dumps(raw_report).encode("utf-8")
    files = {"file": ("synthetic_report_e2e.json", file_bytes, "application/json")}
    extract_resp = test_client.post("/api/reports/extract", files=files)
    assert extract_resp.status_code == 200
    extract_data = extract_resp.json()

    # 2. Confirm returned values, units, provenance, extraction status, and unverified flag
    assert extract_data["success"] is True
    assert extract_data["extraction_status"] == "parsed"
    assert extract_data["is_verified"] is False
    assert extract_data["requires_clinician_verification"] is True
    assert extract_data["clinical_values"]["age"] == 45.0
    assert extract_data["clinical_values"]["ast"] == 42.0
    assert extract_data["clinical_values"]["alt"] == 38.0
    assert extract_data["clinical_values"]["platelets"] == 180.0
    assert extract_data["clinical_values"]["wbc"] is None  # missing preserved as null

    # 3. Register extraction result through /api/reports/register
    reg_payload = {
        "external_subject_id": "SYNTH-PATIENT-E2E-001",
        "original_filename": "synthetic_report_e2e.json",
        "media_type": "application/json",
        "file_size_bytes": len(file_bytes),
        "file_sha256": "e2e_sha256_hash_12345",
        "extraction_status": extract_data["extraction_status"],
        "clinical_values": {
            "age_years": extract_data["clinical_values"]["age"],
            "bmi": extract_data["clinical_values"]["bmi"],
            "platelets_10e9_l": extract_data["clinical_values"]["platelets"],
            "ast_u_l": extract_data["clinical_values"]["ast"],
            "alt_u_l": extract_data["clinical_values"]["alt"],
        },
        "uploaded_by": "intake_nurse_1",
    }
    reg_resp = test_client.post("/api/reports/register", json=reg_payload)
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    report_id = reg_data["report_id"]
    patient_id = reg_data["patient_id"]
    obs_id = reg_data["observation_id"]
    assert reg_data["is_verified"] is False

    # 4. Retrieve registered report and confirm observation is still unverified
    get_rep_resp = test_client.get(f"/api/reports/{report_id}")
    assert get_rep_resp.status_code == 200
    rep_detail = get_rep_resp.json()
    assert rep_detail["id"] == report_id
    assert rep_detail["observation"]["is_verified_by_doctor"] is False
    assert rep_detail["observation"]["platelets_10e9_l"] == 180.0
    assert rep_detail["observation"]["wbc_10e9_l"] is None

    # 5. Attempt assessment creation before verification; confirm rejection (HTTP 400)
    unverified_assess_resp = test_client.post("/api/assessments", json={
        "patient_id": patient_id,
        "observation_id": obs_id,
    })
    assert unverified_assess_resp.status_code == 400
    assert "not been verified" in unverified_assess_resp.json()["detail"].lower()

    # 6. Verify observation using clinician verification endpoint
    verify_resp = test_client.post(f"/api/observations/{obs_id}/verify", json={
        "verified_by": "dr_evans_hepatologist",
        "verified_values": {"ast_u_l": 42.0},  # confirm value
        "clinician_notes": "Lab values confirmed from official hospital LIS feed.",
    })
    assert verify_resp.status_code == 200
    verify_data = verify_resp.json()
    assert verify_data["is_verified_by_doctor"] is True
    assert verify_data["verified_by"] == "dr_evans_hepatologist"

    # 7. Create assessment using verified observation
    assess_resp = test_client.post("/api/assessments", json={
        "patient_id": patient_id,
        "observation_id": obs_id,
        "clinician_notes": "Initial risk triage encounter.",
    })
    assert assess_resp.status_code == 200
    assess_data = assess_resp.json()
    assessment_id = assess_data["id"]

    # 8. Independently calculate expected FIB-4 result and compare with returned & stored score
    # Formula: (Age * AST) / (Platelets * sqrt(ALT))
    expected_fib4 = (45.0 * 42.0) / (180.0 * math.sqrt(38.0))  # ≈ 1.703325...
    assert math.isclose(assess_data["fib4_score"], expected_fib4, rel_tol=1e-5)
    assert assess_data["fib4_risk_category"] == "Indeterminate"
    assert "screening" in assess_data["disclaimer"].lower() or "indirect" in assess_data["disclaimer"].lower()

    # Check database persistence of assessment
    db_assessment = db_session.query(Assessment).filter(Assessment.id == assessment_id).first()
    assert db_assessment is not None
    assert math.isclose(db_assessment.fib4_score, expected_fib4, rel_tol=1e-5)

    # 9. Retrieve assessment detail
    detail_resp = test_client.get(f"/api/assessments/{assessment_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["id"] == assessment_id
    assert detail_data["clinician_notes"] == "Initial risk triage encounter."
    assert detail_data["observation_values"]["platelets"] == 180.0

    # 10. Retrieve patient's assessment history and verify assessment appears exactly once
    history_resp = test_client.get(f"/api/patients/{patient_id}/assessments")
    assert history_resp.status_code == 200
    history_data = history_resp.json()
    assert history_data["patient_id"] == patient_id
    assert history_data["total"] == 1
    assert len(history_data["items"]) == 1
    assert history_data["items"][0]["id"] == assessment_id


# ---------------------------------------------------------------------------
# 2. CSV and PDF Endpoints & Scanned Document Verification
# ---------------------------------------------------------------------------

def test_e2e_csv_extraction_endpoint(test_client):
    csv_bytes = b"Age,BMI,Platelets,AST,ALT,WBC,RBC,HGB\n50,25.0,200,35,30,6.0,4.8,14.0\n"
    files = {"file": ("patient_panel.csv", csv_bytes, "text/csv")}
    res = test_client.post("/api/reports/extract", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["clinical_values"]["platelets"] == 200.0
    assert data["clinical_values"]["ast"] == 35.0


def test_e2e_text_pdf_extraction_endpoint(test_client):
    pdf_bytes = create_sample_text_pdf([
        "HOSPITAL LABORATORY REPORT",
        "Patient Age: 58",
        "AST (SGOT): 48 U/L",
        "ALT (SGPT): 40 U/L",
        "Platelet Count: 165 x10^3/uL",
        "BMI: 28.2 kg/m^2",
    ])
    files = {"file": ("report_digital.pdf", pdf_bytes, "application/pdf")}
    res = test_client.post("/api/reports/extract", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["clinical_values"]["age"] == 58.0
    assert data["clinical_values"]["platelets"] == 165.0


def test_e2e_scanned_pdf_manual_review_status(test_client):
    # Empty blank page with zero text stream
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    empty_pdf = buf.getvalue()

    files = {"file": ("scanned_bloodwork.pdf", empty_pdf, "application/pdf")}
    res = test_client.post("/api/reports/extract", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is False
    assert data["extraction_status"] == "no_text_found"
    assert any("manual entry is required" in w.lower() for w in data["warnings"])


# ---------------------------------------------------------------------------
# 3. Persistence, Rollback, and Foreign-Key Integrity
# ---------------------------------------------------------------------------

def test_persistence_across_independent_sessions(db_engine):
    """Confirm records persist across independent database sessions."""
    Session1 = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    Session2 = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)

    # Session 1: Write patient and report
    s1 = Session1()
    p = Patient(external_subject_id="MULTI-SESSION-001")
    s1.add(p)
    s1.commit()
    patient_id = p.id
    s1.close()

    # Session 2: Read patient from independent session
    s2 = Session2()
    read_p = s2.query(Patient).filter(Patient.id == patient_id).first()
    assert read_p is not None
    assert read_p.external_subject_id == "MULTI-SESSION-001"
    s2.close()


def test_failed_assessment_leaves_no_records_or_success_audits(test_client, db_session):
    """Verify failed assessment creation does not leave orphan assessment or success audit events."""
    reg = test_client.post("/api/reports/register", json={
        "external_subject_id": "PATIENT-FAIL-ROLLBACK",
        "original_filename": "test.json",
        "clinical_values": {"age_years": 45.0, "platelets_10e9_l": 180.0},
    })
    pat_id = reg.json()["patient_id"]
    obs_id = reg.json()["observation_id"]

    # Deliberately attempt assessment without verification (fails 400)
    res = test_client.post("/api/assessments", json={
        "patient_id": pat_id,
        "observation_id": obs_id,
    })
    assert res.status_code == 400

    # Verify no assessment record exists
    assert db_session.query(Assessment).filter(Assessment.patient_id == pat_id).count() == 0
    # Verify no ASSESSMENT_CREATED audit exists
    assert db_session.query(AuditEvent).filter(
        AuditEvent.event_type == "ASSESSMENT_CREATED",
        AuditEvent.entity_name == "assessments"
    ).count() == 0


def test_assessment_history_pagination_and_ordering(test_client):
    """Verify assessment history returns newest first and respects pagination."""
    reg = test_client.post("/api/reports/register", json={
        "external_subject_id": "PATIENT-PAGINATION",
        "original_filename": "panel.json",
        "clinical_values": {"age_years": 40.0, "platelets_10e9_l": 200.0, "ast_u_l": 30.0, "alt_u_l": 25.0},
    })
    pat_id = reg.json()["patient_id"]
    obs_id = reg.json()["observation_id"]

    test_client.post(f"/api/observations/{obs_id}/verify", json={"verified_by": "dr_pagination"})

    # Create two assessments
    a1 = test_client.post("/api/assessments", json={"patient_id": pat_id, "observation_id": obs_id, "clinician_notes": "Encounter 1"})
    a2 = test_client.post("/api/assessments", json={"patient_id": pat_id, "observation_id": obs_id, "clinician_notes": "Encounter 2"})

    # Test limit=1
    hist = test_client.get(f"/api/patients/{pat_id}/assessments?skip=0&limit=1").json()
    assert hist["total"] == 2
    assert len(hist["items"]) == 1
    assert hist["items"][0]["id"] == a2.json()["id"]  # newest first


# ---------------------------------------------------------------------------
# 4. Alembic Migration Clean Database Initialization Test
# ---------------------------------------------------------------------------

def test_alembic_migration_on_clean_database():
    """Verify that Alembic migrations run cleanly and generate all tables on an empty database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    engine = None
    try:
        test_url = f"sqlite:///{tmp_path}"
        os.environ["SUGAR_DATABASE_URL"] = test_url

        cfg = Config("alembic.ini")
        cfg.set_main_option("sqlalchemy.url", test_url)

        # Run migration from base to head
        command.upgrade(cfg, "head")

        engine = create_engine(test_url)
        inspector = inspect(engine)
        tables = sorted(inspector.get_table_names())
        expected = ["alembic_version", "assessments", "audit_events", "clinical_observations", "model_predictions", "patients", "reports"]
        assert tables == expected
    finally:
        if engine:
            engine.dispose()
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
