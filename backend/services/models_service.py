"""
SUGAR — Inference and Metrics Service for Model 3 and Model 4.

Model 3: UCI HCV 5-Class Classifier (models/uci_hcv_exploratory_model.pkl)
Model 4: Disease Etiology & Clinical Stigmata (models/etiology_stigmata_model.pkl)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import joblib
import pandas as pd

from backend.schemas.models import (
    Model4InputSchema,
    Model4PredictionResponse,
    UciHcvInputSchema,
    UciHcvPredictionResponse,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "outputs"

UCI_HCV_MODEL_PATH = MODEL_DIR / "uci_hcv_exploratory_model.pkl"
UCI_HCV_METRICS_PATH = OUTPUT_DIR / "uci_hcv_experiment2_metrics.json"

MODEL4_PATH = MODEL_DIR / "etiology_stigmata_model.pkl"
MODEL4_METRICS_PATH = OUTPUT_DIR / "model4_etiology_stigmata_metrics.json"

# Lazy-loaded model singletons
_uci_hcv_model = None
_model4_model = None


def get_uci_hcv_model():
    global _uci_hcv_model
    if _uci_hcv_model is None:
        if not UCI_HCV_MODEL_PATH.exists():
            raise FileNotFoundError(f"UCI HCV model artifact not found at {UCI_HCV_MODEL_PATH}")
        _uci_hcv_model = joblib.load(UCI_HCV_MODEL_PATH)
    return _uci_hcv_model


def get_model4_model():
    global _model4_model
    if _model4_model is None:
        if not MODEL4_PATH.exists():
            raise FileNotFoundError(f"Model 4 artifact not found at {MODEL4_PATH}")
        _model4_model = joblib.load(MODEL4_PATH)
    return _model4_model


# ---------------------------------------------------------------------------
# Model 3 Inference & Metrics
# ---------------------------------------------------------------------------

def predict_uci_hcv(data: UciHcvInputSchema) -> UciHcvPredictionResponse:
    model = get_uci_hcv_model()

    input_df = pd.DataFrame([{
        "Age": data.age,
        "Sex": data.sex,
        "ALB": data.alb,
        "ALP": data.alp,
        "ALT": data.alt,
        "AST": data.ast,
        "BIL": data.bil,
        "CHE": data.che,
        "CHOL": data.chol,
        "CREA": data.crea,
        "GGT": data.ggt,
        "PROT": data.prot,
    }])

    pred = model.predict(input_df)[0]
    classes = list(model.classes_)
    probs = model.predict_proba(input_df)[0]
    prob_dict = {str(c): round(float(p), 4) for c, p in zip(classes, probs)}
    top_prob = round(float(max(probs)), 4)

    is_fibrosis_or_cirrhosis = "Fibrosis" in str(pred) or "Cirrhosis" in str(pred)

    disclaimer = (
        "Research-only exploratory five-class model trained on European blood donor / hepatitis cohort. "
        "Not clinically validated. Do not use for patient management."
    )
    imbalance_warning = (
        "Dataset has extreme class imbalance (533 donors vs 21 fibrosis, 30 cirrhosis, 24 hepatitis). "
        "Test metrics on minority disease categories have wide confidence intervals (support: 4-6)."
    )

    return UciHcvPredictionResponse(
        predicted_category=str(pred),
        class_probabilities=prob_dict,
        top_probability=top_prob,
        is_fibrosis_or_cirrhosis=is_fibrosis_or_cirrhosis,
        scientific_disclaimer=disclaimer,
        imbalanced_class_warning=imbalance_warning,
    )


def get_uci_hcv_metrics() -> Dict[str, Any]:
    if not UCI_HCV_METRICS_PATH.exists():
        raise FileNotFoundError("UCI HCV metrics file not found.")
    with open(UCI_HCV_METRICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Model 4 Inference & Metrics
# ---------------------------------------------------------------------------

def predict_model4(data: Model4InputSchema) -> Model4PredictionResponse:
    model = get_model4_model()

    input_df = pd.DataFrame([{
        "Age_years": data.age_years,
        "Sex": data.sex,
        "Bilirubin": data.bilirubin,
        "Albumin": data.albumin,
        "Platelets": data.platelets,
        "SGOT": data.sgot,
        "Alk_Phos": data.alk_phos,
        "Copper": data.copper,
        "Prothrombin": data.prothrombin,
        "Ascites": data.ascites,
        "Hepatomegaly": data.hepatomegaly,
        "Spiders": data.spiders,
        "Edema": data.edema,
    }])

    pred = int(model.predict(input_df)[0])
    prob = round(float(model.predict_proba(input_df)[0][1]), 4)
    risk_label = "High Risk / Advanced Fibrosis or Cirrhosis" if pred == 1 else "Low Risk / Early or Moderate Fibrosis"

    stigmata = {
        "ascites": data.ascites or "N",
        "hepatomegaly": data.hepatomegaly or "N",
        "spiders": data.spiders or "N",
        "edema": data.edema or "N",
    }

    disclaimer = (
        "Model 4 evaluated on biopsy-confirmed Mayo Clinic Primary Biliary Cirrhosis cohort. "
        "Evaluates clinical stigmata alongside laboratory biomarkers. Educational & research prototype only."
    )

    return Model4PredictionResponse(
        prediction=pred,
        risk_label=risk_label,
        probability=prob,
        stigmata_evaluated=stigmata,
        dataset_provenance="Mayo Clinic Primary Biliary Cirrhosis (PBC) Study (N=418)",
        scientific_disclaimer=disclaimer,
    )


def get_model4_metrics() -> Dict[str, Any]:
    if not MODEL4_METRICS_PATH.exists():
        raise FileNotFoundError("Model 4 metrics file not found.")
    with open(MODEL4_METRICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
