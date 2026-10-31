from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
import joblib
import pandas as pd
import json
from pathlib import Path
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.schemas.clinical import (
    Fib4InputSchema,
    Fib4ResponseSchema,
    validate_finite_float,
    validate_positive_float,
)
from backend.schemas.extraction import ExtractionResponse
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
from backend.services.extraction import extract_medical_report, MAX_UPLOAD_SIZE_BYTES
from backend.services.orchestration import (
    register_extracted_report,
    get_report_detail,
    verify_clinical_observation,
    create_clinical_assessment,
    get_assessment_detail,
    list_patient_assessments,
)
from backend.schemas.models import (
    UciHcvInputSchema,
    UciHcvPredictionResponse,
    Model4InputSchema,
    Model4PredictionResponse,
)
from backend.services.models_service import (
    predict_uci_hcv,
    get_uci_hcv_metrics,
    predict_model4,
    get_model4_metrics,
)


# Create FastAPI application
app = FastAPI(
    title="AI-Assisted Liver Fibrosis Risk Stratification",
    description="Research prototype for liver fibrosis risk stratification.",
    version="1.0.0"
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Load trained models
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"

baseline_model = joblib.load(
    MODEL_DIR / "routine_clinical_baseline.pkl"
)

expanded_model = joblib.load(
    MODEL_DIR / "expanded_fibrosis_model.pkl"
)


# --------------------------------------------------
# Input structure (Preserves exact /predict schema while enforcing finite positive values)
# --------------------------------------------------

class PatientData(BaseModel):
    age: float
    bmi: float
    platelets: float
    ast: float
    alt: float
    wbc: float
    rbc: float
    hgb: float

    @field_validator("age", "bmi", "platelets", "ast", "alt", "wbc", "rbc", "hgb")
    @classmethod
    def validate_positive_finite(cls, v: float, info) -> float:
        res = validate_positive_float(v, info.field_name)
        assert res is not None
        return res


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "Liver fibrosis backend is running"
    }


# --------------------------------------------------
# Prediction
# --------------------------------------------------

@app.post("/predict")
def predict(data: PatientData):

    # Baseline model features
    baseline_input = pd.DataFrame([{
        "Age": data.age,
        "BMI": data.bmi,
        "Plat": data.platelets,
        "AST 1": data.ast,
        "ALT 1": data.alt
    }])

    # Expanded model features
    expanded_input = pd.DataFrame([{
        "Age": data.age,
        "BMI": data.bmi,
        "Plat": data.platelets,
        "AST 1": data.ast,
        "ALT 1": data.alt,
        "WBC": data.wbc,
        "RBC": data.rbc,
        "HGB": data.hgb
    }])

    # Baseline prediction
    baseline_prediction = baseline_model.predict(baseline_input)[0]
    baseline_probability = baseline_model.predict_proba(
        baseline_input
    )[0][1]

    # Expanded prediction
    expanded_prediction = expanded_model.predict(expanded_input)[0]
    expanded_probability = expanded_model.predict_proba(
        expanded_input
    )[0][1]

    return {
        "baseline_model": {
            "prediction": int(baseline_prediction),
            "probability": round(float(baseline_probability), 4)
        },
        "expanded_model": {
            "prediction": int(expanded_prediction),
            "probability": round(float(expanded_probability), 4)
        },
        "disclaimer": (
            "Research prototype for educational purposes. "
            "It does not provide a medical diagnosis."
        )
    }


# --------------------------------------------------
# Clinical FIB-4 Service Endpoint
# --------------------------------------------------

@app.post("/api/fib4/calculate", response_model=Fib4ResponseSchema)
def calculate_fib4_route(data: Fib4InputSchema):
    """
    Standard Clinical FIB-4 calculation and risk stratification endpoint.

    FIB-4 = (Age [years] × AST [U/L]) / (Platelets [10⁹/L] × √ALT [U/L])
    Separate from research ML inference to preserve clinical units and safeguards.
    """
    interpretation = calculate_and_interpret_fib4(
        age=data.age,
        ast=data.ast,
        alt=data.alt,
        platelets=data.platelets,
    )
    return interpretation.to_dict()


# --------------------------------------------------
# Medical Report Extraction Endpoint (Phase 4)
# --------------------------------------------------

@app.post("/api/reports/extract", response_model=ExtractionResponse)
async def extract_report_route(file: UploadFile = File(...)):
    """
    Narrowly scoped medical report extraction endpoint.
    Accepts JSON, CSV, or digital text PDF files.
    Extracts clinical observations with provenance and marks output as unverified.
    Does NOT orchestrate assessments, run models, or persist to database.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file missing filename.")

    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty (0 bytes).")
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum upload size of {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
        )

    try:
        response = extract_medical_report(content, file.filename)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Report extraction failed: {str(e)}")


# --------------------------------------------------
# Phase 5: Assessment Orchestration & Database Persistence
# --------------------------------------------------

@app.post("/api/reports/register", response_model=ReportRegistrationResponse)
def register_report_route(
    data: ReportRegistrationRequest,
    db: Session = Depends(get_db),
):
    """
    Register an extracted report and its unverified clinical observations into database.
    Preserves missing values as null; logs audit event.
    """
    try:
        return register_extracted_report(db, data)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@app.get("/api/reports/{report_id}", response_model=ReportDetailResponse)
def get_report_route(
    report_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve report metadata and linked unverified/verified clinical observations.
    Excludes sensitive system paths.
    """
    try:
        return get_report_detail(db, report_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@app.post("/api/observations/{observation_id}/verify", response_model=ObservationVerificationResponse)
def verify_observation_route(
    observation_id: str,
    data: ObservationVerificationRequest,
    db: Session = Depends(get_db),
):
    """
    Submit clinician verification and corrections for an observation.
    Note: Authentication is developmental; not for live production use without auth.
    """
    try:
        return verify_clinical_observation(db, observation_id, data)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@app.post("/api/assessments", response_model=AssessmentDetailResponse)
def create_assessment_route(
    data: AssessmentCreateRequest,
    db: Session = Depends(get_db),
):
    """
    Orchestrate clinical assessment calculation and persistence.
    REJECTS unverified observations. Rejects cross-patient mismatches.
    Calculates deterministic FIB-4 using verified values only.
    """
    try:
        return create_clinical_assessment(db, data)
    except ValueError as ve:
        # Check if missing parameters
        msg = str(ve)
        status_code = 422 if "Missing required clinical" in msg else 400
        raise HTTPException(status_code=status_code, detail=msg)


@app.get("/api/assessments/{assessment_id}", response_model=AssessmentDetailResponse)
def get_assessment_route(
    assessment_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve an assessment by ID with linked observation values."""
    try:
        return get_assessment_detail(db, assessment_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


@app.get("/api/patients/{patient_id}/assessments", response_model=AssessmentListResponse)
def list_patient_assessments_route(
    patient_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Retrieve paginated assessment history for a patient."""
    try:
        return list_patient_assessments(db, patient_id, skip=skip, limit=limit)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))


# --------------------------------------------------
# Research data read-only endpoints
# --------------------------------------------------

@app.get("/api/metrics")
def get_metrics():
    metrics_file = MODEL_DIR / "metrics.json"
    if metrics_file.exists():
        with open(metrics_file, "r") as f:
            return json.load(f)
    return {"error": "metrics.json not found"}


# --------------------------------------------------
# Model 3: UCI HCV 5-Class Classifier Endpoints
# --------------------------------------------------

@app.post("/api/models/uci-hcv/predict", response_model=UciHcvPredictionResponse)
def predict_uci_hcv_route(data: UciHcvInputSchema):
    """
    Model 3: UCI HCV exploratory five-class hepatitis/fibrosis/cirrhosis classification.
    Research-only endpoint with explicit class-imbalance transparency.
    """
    try:
        return predict_uci_hcv(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"UCI HCV inference failed: {str(e)}")


@app.get("/api/models/uci-hcv/metrics")
def get_uci_hcv_metrics_route():
    """Retrieve actual evaluation metrics, classification report, and confusion matrix for Model 3."""
    try:
        return get_uci_hcv_metrics()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# --------------------------------------------------
# Model 4: Disease Etiology & Clinical Stigmata Endpoints
# --------------------------------------------------

@app.post("/api/models/model4/predict", response_model=Model4PredictionResponse)
def predict_model4_route(data: Model4InputSchema):
    """
    Model 4: Advanced Fibrosis / Cirrhosis prediction incorporating clinical stigmata
    (ascites, hepatomegaly, spiders, edema) and laboratory biomarkers from the Mayo Clinic PBC trial.
    """
    try:
        return predict_model4(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Model 4 inference failed: {str(e)}")


@app.get("/api/models/model4/metrics")
def get_model4_metrics_route():
    """Retrieve 5-fold CV and held-out test evaluation metrics for Model 4."""
    try:
        return get_model4_metrics()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
