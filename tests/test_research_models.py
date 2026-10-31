"""
SUGAR — Research Models (Model 3: UCI HCV & Model 4: Etiology/Stigmata) Integration Tests.

Validates:
  - Model 3 (UCI HCV 5-Class) artifact, preprocessing pipeline, prediction endpoint,
    class probabilities, output interpretation, and class-imbalance warnings.
  - Model 4 (Etiology & Clinical Stigmata) artifact, preprocessing pipeline, prediction endpoint,
    stigmata handling (ascites, hepatomegaly, spiders, edema), held-out metrics, and disclaimers.
  - Input validation, boundary checks, and error responses.
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.models_service import (
    predict_uci_hcv,
    get_uci_hcv_metrics,
    predict_model4,
    get_model4_metrics,
    UCI_HCV_MODEL_PATH,
    MODEL4_PATH,
)
from backend.schemas.models import UciHcvInputSchema, Model4InputSchema
import joblib

client = TestClient(app)


# ---------------------------------------------------------------------------
# Model 3: UCI HCV 5-Class Classifier Tests
# ---------------------------------------------------------------------------

def test_uci_hcv_artifact_and_pipeline_structure():
    """Verify Model 3 artifact exists and has complete ColumnTransformer pipeline."""
    assert UCI_HCV_MODEL_PATH.exists()
    model = joblib.load(UCI_HCV_MODEL_PATH)
    assert hasattr(model, "predict")
    assert hasattr(model, "predict_proba")
    assert len(model.classes_) == 5
    assert "0=Blood Donor" in model.classes_
    assert "2=Fibrosis" in model.classes_
    assert "3=Cirrhosis" in model.classes_


def test_uci_hcv_prediction_service_and_interpretation():
    """Verify Model 3 prediction logic and minority class warnings."""
    # Typical normal blood donor profile
    data = UciHcvInputSchema(
        age=45.0,
        sex="m",
        alb=40.0,
        alp=60.0,
        alt=25.0,
        ast=25.0,
        bil=8.0,
        che=8.0,
        chol=4.5,
        crea=80.0,
        ggt=20.0,
        prot=72.0,
    )
    res = predict_uci_hcv(data)
    assert res.predicted_category in ["0=Blood Donor", "0s=suspect Blood Donor", "1=Hepatitis", "2=Fibrosis", "3=Cirrhosis"]
    assert len(res.class_probabilities) == 5
    assert sum(res.class_probabilities.values()) == pytest.approx(1.0, abs=1e-3)
    assert "class imbalance" in res.imbalanced_class_warning.lower()
    assert "not clinically validated" in res.scientific_disclaimer.lower()


def test_uci_hcv_api_endpoints():
    """Verify POST /api/models/uci-hcv/predict and GET /api/models/uci-hcv/metrics."""
    # 1. Metrics endpoint
    met_res = client.get("/api/models/uci-hcv/metrics")
    assert met_res.status_code == 200
    metrics_data = met_res.json()
    assert "test_accuracy" in metrics_data
    assert "test_balanced_accuracy" in metrics_data
    assert "classification_report" in metrics_data
    assert metrics_data["dataset_rows"] == 615

    # 2. Prediction endpoint (blood donor test case)
    payload = {
        "age": 52.0,
        "sex": "m",
        "alb": 38.5,
        "alp": 52.5,
        "alt": 18.0,
        "ast": 24.0,
        "bil": 6.8,
        "che": 9.2,
        "chol": 4.8,
        "crea": 75.0,
        "ggt": 22.0,
        "prot": 70.0,
    }
    pred_res = client.post("/api/models/uci-hcv/predict", json=payload)
    assert pred_res.status_code == 200
    res_data = pred_res.json()
    assert "predicted_category" in res_data
    assert "class_probabilities" in res_data
    assert res_data["predicted_category"] == "0=Blood Donor"

    # 3. Cirrhosis test case (elevated AST, ALT, Bilirubin, GGT; low Albumin, Cholinesterase)
    cirrhosis_payload = {
        "age": 60.0,
        "sex": "m",
        "alb": 22.0,
        "alp": 120.0,
        "alt": 110.0,
        "ast": 180.0,
        "bil": 95.0,
        "che": 2.1,
        "chol": 2.5,
        "crea": 130.0,
        "ggt": 320.0,
        "prot": 58.0,
    }
    cirr_res = client.post("/api/models/uci-hcv/predict", json=cirrhosis_payload)
    assert cirr_res.status_code == 200
    cirr_data = cirr_res.json()
    assert cirr_data["is_fibrosis_or_cirrhosis"] is True


def test_uci_hcv_missing_imputation():
    """Verify that unmeasured optional labs are cleanly imputed by the pipeline."""
    # Missing ALB, CHE, CHOL, GGT
    partial_payload = {
        "age": 48.0,
        "sex": "f",
        "ast": 35.0,
        "alt": 30.0,
    }
    pred_res = client.post("/api/models/uci-hcv/predict", json=partial_payload)
    assert pred_res.status_code == 200
    res_data = pred_res.json()
    assert "predicted_category" in res_data


def test_uci_hcv_validation_errors():
    """Verify rejection of invalid age and invalid sex."""
    # Age < 1
    res1 = client.post("/api/models/uci-hcv/predict", json={"age": -5.0, "sex": "m"})
    assert res1.status_code == 422

    # Invalid sex string
    res2 = client.post("/api/models/uci-hcv/predict", json={"age": 45.0, "sex": "unknown"})
    assert res2.status_code == 422


# ---------------------------------------------------------------------------
# Model 4: Disease Etiology & Clinical Stigmata Tests
# ---------------------------------------------------------------------------

def test_model4_artifact_and_pipeline_structure():
    """Verify Model 4 artifact exists and has complete ColumnTransformer pipeline."""
    assert MODEL4_PATH.exists()
    model = joblib.load(MODEL4_PATH)
    assert hasattr(model, "predict")
    assert hasattr(model, "predict_proba")
    assert len(model.classes_) == 2
    steps = [name for name, _ in model.steps]
    assert steps == ["preprocessor", "classifier"]


def test_model4_prediction_service_and_stigmata():
    """Verify Model 4 prediction logic with physical stigmata flags."""
    # Case with advanced cirrhosis stigmata (ascites, jaundice/high bili, hepatomegaly)
    data = Model4InputSchema(
        age_years=58.0,
        sex="F",
        bilirubin=6.5,
        albumin=2.8,
        platelets=110.0,
        sgot=125.0,
        alk_phos=1800.0,
        copper=150.0,
        prothrombin=13.5,
        ascites="Y",
        hepatomegaly="Y",
        spiders="Y",
        edema="Y",
    )
    res = predict_model4(data)
    assert res.prediction in [0, 1]
    assert res.prediction == 1
    assert 0.0 <= res.probability <= 1.0
    assert "High Risk" in res.risk_label
    assert res.stigmata_evaluated["ascites"] == "Y"
    assert res.stigmata_evaluated["hepatomegaly"] == "Y"
    assert "Mayo Clinic" in res.dataset_provenance


def test_model4_api_endpoints():
    """Verify POST /api/models/model4/predict and GET /api/models/model4/metrics."""
    # 1. Metrics endpoint
    met_res = client.get("/api/models/model4/metrics")
    assert met_res.status_code == 200
    metrics_data = met_res.json()
    assert "held_out_test_metrics" in metrics_data
    assert "cross_validation_5fold" in metrics_data
    assert "feature_importances" in metrics_data
    assert metrics_data["dataset"]["total_rows"] == 412
    assert metrics_data["held_out_test_metrics"]["roc_auc"] >= 0.65

    # 2. Prediction endpoint (mild PBC profile without stigmata)
    mild_payload = {
        "age_years": 45.0,
        "sex": "F",
        "bilirubin": 0.8,
        "albumin": 4.1,
        "platelets": 290.0,
        "sgot": 45.0,
        "alk_phos": 650.0,
        "ascites": "N",
        "hepatomegaly": "N",
        "spiders": "N",
        "edema": "N",
    }
    pred_res = client.post("/api/models/model4/predict", json=mild_payload)
    assert pred_res.status_code == 200
    data = pred_res.json()
    assert "prediction" in data
    assert "probability" in data
    assert "risk_label" in data
    assert data["prediction"] == 0
    assert "Early or Moderate" in data["risk_label"]


def test_model4_missing_stigmata_robustness():
    """Verify that Model 4 handles missing optional labs and stigmata gracefully."""
    # Minimal inputs (only required age_years)
    min_payload = {
        "age_years": 50.0,
    }
    pred_res = client.post("/api/models/model4/predict", json=min_payload)
    assert pred_res.status_code == 200
    data = pred_res.json()
    assert data["prediction"] in [0, 1]
    assert 0.0 <= data["probability"] <= 1.0


def test_model4_validation_errors():
    """Verify adult age bounds validation for Model 4."""
    # Pediatric age < 18
    res = client.post("/api/models/model4/predict", json={"age_years": 14.0})
    assert res.status_code == 422
