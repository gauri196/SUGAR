import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {
        "status": "ok",
        "message": "Liver fibrosis backend is running"
    }


def test_metrics_endpoint():
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "dataset" in data
    assert data["dataset"]["name"] == "UCI Hepatitis C Virus (HCV) for Egyptian Patients"
    assert data["dataset"]["rows"] == 1384
    assert data["dataset"]["columns"] == 31
    assert "target_A" in data
    assert "target_B" in data
    assert "features" in data
    assert "feature_importance" in data


def test_predict_case1_deterministic():
    payload = {
        "age": 42.0,
        "bmi": 24.5,
        "platelets": 255.0,
        "ast": 25.0,
        "alt": 24.0,
        "wbc": 6.5,
        "rbc": 4.8,
        "hgb": 15.0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["baseline_model"]["prediction"] == 1
    assert pytest.approx(data["baseline_model"]["probability"], abs=1e-4) == 0.5729
    assert data["expanded_model"]["prediction"] == 1
    assert pytest.approx(data["expanded_model"]["probability"], abs=1e-4) == 0.5062
    assert "Research prototype for educational purposes." in data["disclaimer"]


def test_predict_case2_deterministic():
    payload = {
        "age": 56.0,
        "bmi": 29.4,
        "platelets": 145.0,
        "ast": 58.0,
        "alt": 48.0,
        "wbc": 8.2,
        "rbc": 4.3,
        "hgb": 13.6
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["baseline_model"]["prediction"] == 1
    assert pytest.approx(data["baseline_model"]["probability"], abs=1e-4) == 0.5113
    assert data["expanded_model"]["prediction"] == 0
    assert pytest.approx(data["expanded_model"]["probability"], abs=1e-4) == 0.4599


def test_predict_case3_deterministic():
    payload = {
        "age": 64.0,
        "bmi": 32.8,
        "platelets": 92.0,
        "ast": 98.0,
        "alt": 65.0,
        "wbc": 10.4,
        "rbc": 3.9,
        "hgb": 12.1
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["baseline_model"]["prediction"] == 0
    assert pytest.approx(data["baseline_model"]["probability"], abs=1e-4) == 0.4663
    assert data["expanded_model"]["prediction"] == 0
    assert pytest.approx(data["expanded_model"]["probability"], abs=1e-4) == 0.4957


def test_predict_validation_errors():
    # Missing required field 'hgb'
    incomplete_payload = {
        "age": 42.0,
        "bmi": 24.5,
        "platelets": 255.0,
        "ast": 25.0,
        "alt": 24.0,
        "wbc": 6.5,
        "rbc": 4.8
    }
    response = client.post("/predict", json=incomplete_payload)
    assert response.status_code == 422

    # String passed instead of float
    invalid_type_payload = {
        "age": "forty-two",
        "bmi": 24.5,
        "platelets": 255.0,
        "ast": 25.0,
        "alt": 24.0,
        "wbc": 6.5,
        "rbc": 4.8,
        "hgb": 15.0
    }
    response = client.post("/predict", json=invalid_type_payload)
    assert response.status_code == 422
