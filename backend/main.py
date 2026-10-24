from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import pandas as pd
import json
from pathlib import Path


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
# Input structure
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
# Research data read-only endpoints
# --------------------------------------------------

@app.get("/api/metrics")
def get_metrics():
    metrics_file = MODEL_DIR / "metrics.json"
    if metrics_file.exists():
        with open(metrics_file, "r") as f:
            return json.load(f)
    return {"error": "metrics.json not found"}