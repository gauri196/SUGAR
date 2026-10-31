"""
SUGAR — Phase 2 Database and ORM Unit Tests.

Validates:
- Schema creation on SQLite with foreign keys enforced.
- CRUD operations for all entities: Patient, Report, ClinicalObservation,
  Assessment, ModelPrediction, AuditEvent.
- Foreign key constraint enforcement.
- Nullability preservation for all laboratory measurements (no zero-coercion).
- Clinician verification governance attributes.
- Cascade behaviors.
- get_db FastAPI session generator lifecycle.
"""
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from backend.database import Base, get_db
from backend.models import (
    Patient,
    Report,
    ClinicalObservation,
    Assessment,
    ModelPrediction,
    AuditEvent,
)


@pytest.fixture
def db_session():
    """Isolated in-memory SQLite database session with foreign keys enabled."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
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


def test_patient_creation(db_session):
    patient = Patient(external_subject_id="SUBJ-001")
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)

    assert patient.id is not None
    assert len(patient.id) == 36  # UUID v4 string
    assert patient.external_subject_id == "SUBJ-001"
    assert patient.created_at is not None
    assert patient.updated_at is not None


def test_patient_external_id_unique(db_session):
    p1 = Patient(external_subject_id="DUPLICATE_ID")
    p2 = Patient(external_subject_id="DUPLICATE_ID")
    db_session.add(p1)
    db_session.commit()

    db_session.add(p2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_report_creation_and_relationship(db_session):
    patient = Patient()
    db_session.add(patient)
    db_session.commit()

    report = Report(
        patient_id=patient.id,
        original_filename="lab_report_20261028.pdf",
        media_type="application/pdf",
        file_size_bytes=1048576,
        file_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        storage_path="reports/2026/10/lab_report_20261028.pdf",
        extraction_status="parsed",
        uploaded_by="dr_smith",
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    assert report.id is not None
    assert report.patient.id == patient.id
    assert patient.reports == [report]


def test_clinical_observation_nullable_measurements(db_session):
    """Ensure absent measurements remain None (NULL), never coerced to 0."""
    patient = Patient()
    db_session.add(patient)
    db_session.commit()

    obs = ClinicalObservation(
        patient_id=patient.id,
        age_years=45.0,
        # Intentionally omitting other labs
    )
    db_session.add(obs)
    db_session.commit()
    db_session.refresh(obs)

    assert obs.age_years == 45.0
    assert obs.platelets_10e9_l is None
    assert obs.ast_u_l is None
    assert obs.alt_u_l is None
    assert obs.wbc_10e9_l is None
    assert obs.rbc_10e12_l is None
    assert obs.hgb_g_dl is None
    assert obs.glucose_mg_dl is None
    assert obs.cholesterol_mg_dl is None
    assert obs.is_verified_by_doctor is False


def test_clinical_observation_verification_flow(db_session):
    patient = Patient()
    db_session.add(patient)
    db_session.commit()

    obs = ClinicalObservation(
        patient_id=patient.id,
        age_years=52.0,
        platelets_10e9_l=185.0,
        ast_u_l=42.0,
        alt_u_l=38.0,
    )
    db_session.add(obs)
    db_session.commit()

    # Clinician verifies values
    obs.is_verified_by_doctor = True
    obs.verified_by = "dr_jones"
    obs.verified_at = datetime.now(timezone.utc)
    db_session.commit()
    db_session.refresh(obs)

    assert obs.is_verified_by_doctor is True
    assert obs.verified_by == "dr_jones"
    assert obs.verified_at is not None


def test_assessment_and_predictions(db_session):
    patient = Patient()
    db_session.add(patient)
    db_session.commit()

    obs = ClinicalObservation(
        patient_id=patient.id,
        age_years=55.0,
        platelets_10e9_l=160.0,
        ast_u_l=50.0,
        alt_u_l=40.0,
        is_verified_by_doctor=True,
    )
    db_session.add(obs)
    db_session.commit()

    assessment = Assessment(
        patient_id=patient.id,
        observation_id=obs.id,
        fib4_score=1.95,
        fib4_risk_category="Indeterminate",
        fib4_cutoff_applied="<1.30 Low, >2.67 High",
        status="draft",
    )
    db_session.add(assessment)
    db_session.commit()

    pred_a = ModelPrediction(
        assessment_id=assessment.id,
        model_identifier="model_a_baseline_lr",
        model_version="1.0.0",
        target_definition="Target B: F1-F2 vs F3-F4 (advanced fibrosis)",
        predicted_class=1,
        probability=0.5729,
        feature_payload_json='{"Age": 55, "BMI": 25, "Platelets": 160, "AST 1": 1.2, "ALT 1": 1.1}',
    )
    pred_d = ModelPrediction(
        assessment_id=assessment.id,
        model_identifier="model_d_expanded_rf",
        model_version="1.0.0",
        target_definition="Target B: F1-F2 vs F3-F4 (advanced fibrosis)",
        predicted_class=1,
        probability=0.5062,
        feature_payload_json='{"Age": 55, "BMI": 25, "Platelets": 160, "AST 1": 1.2, "ALT 1": 1.1, "WBC": 6.5, "RBC": 4.5, "HGB": 14.0}',
    )
    db_session.add_all([pred_a, pred_d])
    db_session.commit()
    db_session.refresh(assessment)

    assert len(assessment.predictions) == 2
    assert assessment.patient.id == patient.id
    assert assessment.observation.id == obs.id


def test_audit_event_logging(db_session):
    event = AuditEvent(
        event_type="ASSESSMENT_CREATED",
        entity_name="assessments",
        entity_id="test-assessment-id-123",
        performed_by="dr_smith",
        metadata_json='{"fib4": 1.95}',
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)

    assert event.id is not None
    assert event.event_type == "ASSESSMENT_CREATED"
    assert event.entity_name == "assessments"
    assert event.entity_id == "test-assessment-id-123"
    assert event.created_at is not None


def test_foreign_key_enforcement(db_session):
    """Verify that foreign keys are enforced by attempting to insert invalid FK."""
    invalid_report = Report(
        patient_id="nonexistent-uuid",
        original_filename="dummy.pdf",
    )
    db_session.add(invalid_report)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_cascade_delete_patient(db_session):
    patient = Patient()
    db_session.add(patient)
    db_session.commit()

    report = Report(patient_id=patient.id, original_filename="doc.pdf")
    obs = ClinicalObservation(patient_id=patient.id)
    db_session.add_all([report, obs])
    db_session.commit()

    assessment = Assessment(patient_id=patient.id, observation_id=obs.id)
    db_session.add(assessment)
    db_session.commit()

    pred = ModelPrediction(
        assessment_id=assessment.id,
        model_identifier="model_a_baseline_lr",
        target_definition="Target B",
        predicted_class=0,
        probability=0.2,
    )
    db_session.add(pred)
    db_session.commit()

    # Deleting patient cascades to reports, observations, assessments, predictions
    db_session.delete(patient)
    db_session.commit()

    assert db_session.query(Report).count() == 0
    assert db_session.query(ClinicalObservation).count() == 0
    assert db_session.query(Assessment).count() == 0
    assert db_session.query(ModelPrediction).count() == 0


def test_get_db_generator():
    """Verify FastAPI get_db dependency yields an active session and closes it."""
    gen = get_db()
    session = next(gen)
    assert session is not None
    assert session.is_active
    with pytest.raises(StopIteration):
        next(gen)
