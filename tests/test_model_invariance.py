from pathlib import Path
import joblib
import pandas as pd
import pytest

MODELS_DIR = Path("models")


def test_baseline_artifact_integrity():
    model_path = MODELS_DIR / "routine_clinical_baseline.pkl"
    assert model_path.exists(), "routine_clinical_baseline.pkl must exist"
    model = joblib.load(model_path)

    expected_features = ["Age", "BMI", "Plat", "AST 1", "ALT 1"]
    assert list(model.feature_names_in_) == expected_features
    assert model.n_features_in_ == 5

    # Check pipeline structure
    steps = [name for name, _ in model.steps]
    assert steps == ["imputer", "scaler", "model"]

    # Test deterministic prediction
    sample_df = pd.DataFrame([{
        "Age": 50.0,
        "BMI": 25.0,
        "Plat": 200.0,
        "AST 1": 30.0,
        "ALT 1": 30.0
    }])
    prob = model.predict_proba(sample_df)[0][1]
    assert isinstance(prob, float)
    assert 0.0 <= prob <= 1.0


def test_expanded_artifact_integrity():
    model_path = MODELS_DIR / "expanded_fibrosis_model.pkl"
    assert model_path.exists(), "expanded_fibrosis_model.pkl must exist"
    model = joblib.load(model_path)

    expected_features = [
        "Age", "BMI", "Plat", "AST 1", "ALT 1", "WBC", "RBC", "HGB"
    ]
    assert list(model.feature_names_in_) == expected_features
    assert model.n_features_in_ == 8

    # Check pipeline structure
    steps = [name for name, _ in model.steps]
    assert steps == ["imputer", "model"]

    # Test deterministic prediction
    sample_df = pd.DataFrame([{
        "Age": 50.0,
        "BMI": 25.0,
        "Plat": 200.0,
        "AST 1": 30.0,
        "ALT 1": 30.0,
        "WBC": 7.0,
        "RBC": 4.5,
        "HGB": 14.0
    }])
    prob = model.predict_proba(sample_df)[0][1]
    assert isinstance(prob, float)
    assert 0.0 <= prob <= 1.0


def test_fib4_baseline_artifact_integrity():
    model_path = MODELS_DIR / "fib4_baseline_model.pkl"
    assert model_path.exists(), "fib4_baseline_model.pkl must exist"
    model = joblib.load(model_path)
    assert list(model.feature_names_in_) == ["FIB4"]
    assert model.n_features_in_ == 1


def test_uci_hcv_artifact_integrity():
    model_path = MODELS_DIR / "uci_hcv_exploratory_model.pkl"
    assert model_path.exists(), "uci_hcv_exploratory_model.pkl must exist"
    model = joblib.load(model_path)
    assert model.n_features_in_ == 12


def test_etiology_stigmata_model4_artifact_integrity():
    model_path = MODELS_DIR / "etiology_stigmata_model.pkl"
    assert model_path.exists(), "etiology_stigmata_model.pkl must exist"
    model = joblib.load(model_path)
    assert len(model.classes_) == 2
    assert hasattr(model, "predict")
    assert hasattr(model, "predict_proba")
